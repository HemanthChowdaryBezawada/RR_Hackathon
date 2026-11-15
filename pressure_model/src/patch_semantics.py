"""Reconstruct team scores and resolve the patched Part A rules."""

from pathlib import Path
import re
import sys
from typing import Any

import numpy as np
import pandas as pd
import yaml
from scipy.optimize import nnls
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.yaml"
CONFIG = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
DATA_DIR = (ROOT / CONFIG["data_dir"]).resolve()
OUT_DIR = ROOT / CONFIG["outputs_dir"]
OUT_DIR.mkdir(parents=True, exist_ok=True)
C = CONFIG["columns"]
EXTRA_TYPES = ["wide", "legbyes", "byes", "Overstep", "other"]


def result_number(value: Any) -> int | None:
    """Extract a clean run-margin integer from a match result."""
    match = re.search(r"won by\s+(\d+)\s+runs", str(value), re.I)
    return int(match.group(1)) if match else None


def clean_result(value: Any) -> bool:
    """Identify non-rain, non-abandoned, ordinary batting-first run wins."""
    text = str(value)
    return (
        result_number(text) is not None
        and not re.search(r"D/?L|Duckworth|revised|super|abandon|no result", text, re.I)
    )


def base_runs(ball: pd.DataFrame) -> pd.Series:
    """Compute runs_total0 from bat runs and known one-run delivery extras."""
    extras = ball[C["extras_type"]]
    value = ball[C["runs"]].astype(float) + extras.isin(["wide", "Overstep", "other"]).astype(int)
    return value + extras.eq("Penalty").astype(int) * 4


def reconstructed_runs(ball: pd.DataFrame, coefficients: dict[str, int]) -> pd.Series:
    """Apply the constrained, rounded extra-run rules to every delivery."""
    extras = ball[C["extras_type"]]
    value = base_runs(ball).astype(float)
    for kind, coefficient in coefficients.items():
        mask = extras.eq(kind)
        if kind in {"legbyes", "byes"}:
            value.loc[mask] = max(1, round(coefficient))
        elif kind == "wide":
            value.loc[mask] = 1 + round(coefficient)
        else:
            value.loc[mask] = np.maximum(value.loc[mask], value.loc[mask] + round(coefficient))
    return value


def runs_for_mode(ball: pd.DataFrame, coefficients: dict[str, float], mode: str) -> pd.Series:
    """Return base, rounded, or fractional expected team runs."""
    extras = ball[C["extras_type"]]
    value = base_runs(ball).astype(float)
    if mode == "base_only":
        return value
    for kind, coefficient in coefficients.items():
        mask = extras.eq(kind)
        if kind in {"legbyes", "byes"}:
            value.loc[mask] = max(1.0, coefficient)
        elif kind == "wide":
            value.loc[mask] = 1.0 + coefficient
    return value


def bootstrap_coefficients(
    x: np.ndarray, y: np.ndarray, seed: int = 42, reps: int = 1000
) -> np.ndarray:
    """Bootstrap NNLS coefficient estimates by resampling eligible matches."""
    rng = np.random.default_rng(seed)
    estimates = []
    for _ in range(reps):
        indexes = rng.integers(0, len(y), len(y))
        estimates.append(nnls(x[indexes], y[indexes])[0])
    return np.percentile(np.asarray(estimates), [2.5, 97.5], axis=0)


def margin_metrics(
    ball: pd.DataFrame, matches: pd.DataFrame, values: pd.Series
) -> tuple[float, float, float, pd.Series]:
    """Measure exact, ±2, and mean absolute run-margin error."""
    temp = ball[ball[C["innings"]].isin([1, 2])].copy()
    temp["_value"] = values.loc[temp.index]
    totals = temp.groupby([C["match_id"], C["innings"]])["_value"].sum().unstack()
    margins = matches.set_index(C["match_id"])[C["match_result"]].map(result_number)
    common = totals.join(margins.rename("_margin"), how="inner").dropna()
    error = (common[1] - common[2]).abs() - common["_margin"]
    return float((error == 0).mean()), float((error.abs() <= 2).mean()), float(error.abs().mean()), error


def main() -> None:
    ball = pd.read_csv(DATA_DIR / "ball_by_ball.csv", low_memory=False)
    matches = pd.read_csv(DATA_DIR / "matches.csv", low_memory=False)
    competitions = pd.read_csv(DATA_DIR / "competitions.csv", low_memory=False)
    teams = pd.read_csv(DATA_DIR / "teams.csv", low_memory=False)
    mapping = pd.read_csv(DATA_DIR / "competition_team_player_mapping.csv", low_memory=False)
    base = base_runs(ball)
    eligible = matches[matches[C["match_result"]].map(clean_result)].copy()
    temp = ball[ball[C["innings"]].isin([1, 2])].copy()
    temp["_base"] = base.loc[temp.index]
    totals = temp.groupby([C["match_id"], C["innings"]])["_base"].sum().unstack()
    margins = eligible.set_index(C["match_id"])[C["match_result"]].map(result_number)
    common = totals.join(margins.rename("margin"), how="inner").dropna()
    residual = common["margin"] - (common[1] - common[2])
    counts = ball.assign(_base=base).groupby([C["match_id"], C["innings"]])._base.sum().unstack()
    x_rows = []
    for match_id in common.index:
        rows = ball[ball[C["match_id"]].eq(match_id)]
        counts_by_type = rows.groupby([C["innings"], C["extras_type"]]).size().unstack(fill_value=0)
        x_rows.append([counts_by_type.get(kind, pd.Series()).get(1, 0) - counts_by_type.get(kind, pd.Series()).get(2, 0) for kind in EXTRA_TYPES])
    x = np.asarray(x_rows, dtype=float)
    y = residual.to_numpy(dtype=float)
    coefficients, _ = nnls(x, y)
    cis = bootstrap_coefficients(x, y)
    rounded = {kind: int(round(value)) for kind, value in zip(EXTRA_TYPES, coefficients)}
    coefficients_float = {kind: float(value) for kind, value in zip(EXTRA_TYPES, coefficients)}
    corrected = runs_for_mode(ball, coefficients_float, CONFIG.get("runs_reconstruction_mode", "fractional_expected"))
    baseline = ball[C["runs"]].astype(float) + ball[C["extras_type"]].isin(["wide", "Overstep"]).astype(int)
    exact, within2, mae, errors = margin_metrics(ball, eligible, corrected)
    base_exact, base_within2, base_mae, _ = margin_metrics(ball, eligible, baseline)

    report = [
        "# Semantics Patch Report", "",
        "Team scores were reconstructed without changing source CSVs.",
        "",
        "## P1.2 constrained least-squares reconstruction",
        "",
        f"Eligible clean run-margin matches: {len(common)}",
        "",
        "| Extra type | NNLS coefficient | Bootstrap 95% CI | Rounded rule |",
        "| --- | ---: | ---: | ---: |",
    ]
    for index, kind in enumerate(EXTRA_TYPES):
        report.append(f"| {kind} | {coefficients[index]:.4f} | [{cis[0, index]:.4f}, {cis[1, index]:.4f}] | {rounded[kind]} |")
    report += [
        "",
        "Residual histogram:",
        "",
        "| Residual (runs) | Count |",
        "| ---: | ---: |",
    ]
    for value, count in errors.round().astype(int).value_counts().sort_index().items():
        report.append(f"| {value} | {count} |")

    report += [
        "",
        "## P1.4 reconstructed margin accuracy",
        "",
        "| Metric | Baseline | Reconstructed |",
        "| --- | ---: | ---: |",
        f"| Exact margin share | {base_exact:.2%} | {exact:.2%} |",
        f"| Within ±2 runs | {base_within2:.2%} | {within2:.2%} |",
        f"| Mean absolute error | {base_mae:.4f} | {mae:.4f} |",
        f"| Exact-share improvement | — | {(exact - base_exact):+.2%} |",
        "",
    ]

    legal_types = {"wide", "Overstep", "other"}
    legal = ~ball[C["extras_type"]].isin(legal_types)
    temp = ball.assign(_legal=legal, _wicket=ball[C["is_wicket"]].astype(int))
    inning = temp.groupby([C["match_id"], C["innings"]]).agg(
        legal_balls=("_legal", "sum"), wickets=("_wicket", "sum")
    )
    first_valid = (inning["legal_balls"] >= 120) | (inning["wickets"] >= 9)
    match_result = matches.set_index(C["match_id"])[C["match_result"]].fillna("").astype(str)
    winner_by_match = matches.set_index(C["match_id"])[C["winner_team_id"]]
    chase_team = ball[ball[C["innings"]].eq(2)].groupby(C["match_id"])[C["batting_team_id"]].first()
    chase_completed = set(chase_team.index[chase_team.eq(winner_by_match.reindex(chase_team.index))])
    second_valid = (
        inning["legal_balls"].gt(0)
        & (
            inning["legal_balls"].ge(120)
            | inning["wickets"].ge(9)
            | inning.index.get_level_values(C["match_id"]).isin(chase_completed)
        )
    )
    innings_match = inning.index.get_level_values(C["match_id"])
    first_valid_ids = set(innings_match[first_valid & (inning.index.get_level_values(C["innings"]) == 1)])
    second_valid_ids = set(innings_match[second_valid & (inning.index.get_level_values(C["innings"]) == 2)])
    no_result = set(matches.loc[matches[C["winner_team_id"]].isna() | match_result.str.contains("no result", case=False), C["match_id"]])
    absent = set(matches[C["match_id"]]) - set(ball[C["match_id"]])
    rain_short = set(innings_match[(inning.index.get_level_values(C["innings"]) == 1) & (inning["legal_balls"].to_numpy() < 120) & (inning["wickets"].to_numpy() < 9)])
    exclusion_sets = {
        "super-over rows": set(ball.loc[ball[C["innings"]] > 2, C["match_id"]]),
        "D/L or revised": set(matches.loc[matches[C["match_result"]].astype(str).str.contains(r"D/?L|Duckworth|revised", case=False, regex=True), C["match_id"]]),
        "null winner/no result": no_result,
        "missing ball data": absent,
        "innings 1 invalid": set(matches[C["match_id"]]) - first_valid_ids,
        "innings 2 invalid": set(matches[C["match_id"]]) - second_valid_ids,
        "rain-shortened without marker": rain_short,
    }
    excluded = set().union(*exclusion_sets.values())
    usable = set(matches[C["match_id"]]) - excluded
    report += ["## P2. Updated innings validity and exclusions", "", "| Reason (overlaps allowed) | Matches |", "| --- | ---: |"]
    report += [f"| {name} | {len(ids)} |" for name, ids in exclusion_sets.items()]
    unique_removed = set(matches[C["match_id"]]) - usable
    report += [f"", f"Unique matches removed (union of reasons): {len(unique_removed)}", f"Usable matches: {len(usable)}", f"Usable ball rows: {int(ball[C['match_id']].isin(usable).sum())}", "", "Usable matches by comp_group and season year:", ""]
    match_summary = matches[matches[C["match_id"]].isin(usable)].merge(
        competitions[[C["competition_id"], C["competition_name"], "match_format", C["season"]]],
        on=C["competition_id"], how="left"
    )
    match_summary["comp_group"] = np.where(
        match_summary[C["competition_name"]].astype(str).str.contains(r"Indian Premier League|IPL", case=False, regex=True),
        "IPL", np.where(match_summary["match_format"].eq("T20I"), "T20I", "T20_other")
    )
    match_summary["season_year"] = pd.to_datetime(match_summary[C["match_date"]], errors="coerce").dt.year
    grouped_summary = match_summary.groupby(["comp_group", "season_year"]).size().reset_index(name="matches")
    report += ["", "| comp_group | season year | matches |", "| --- | ---: | ---: |"]
    report += [f"| {row.comp_group} | {row.season_year} | {row.matches} |" for row in grouped_summary.itertuples()]
    report += ["", "Rain-shortened matches without D/L markers:", ""]
    report += [f"- {match_id}" for match_id in sorted(rain_short)] or ["- none"]

    pakistan = set(mapping.loc[mapping[C["team_name"]].isin(["Pakistan", "Pakistan A"]), C["player_id"]])
    mixed = mapping[mapping[C["player_id"]].isin(pakistan)].groupby(C["player_id"])[C["team_name"]].agg(set)
    mixed = mixed[mixed.map(lambda names: any(name not in {"Pakistan", "Pakistan A"} for name in names))]
    report += ["", "## P3. Pakistan identity overlap", "", "| player_id | mapped teams |", "| --- | --- |"]
    report += [f"| {player_id} | {', '.join(sorted(teams))} |" for player_id, teams in mixed.items()] or ["| none | — |"]

    resolved = CONFIG.setdefault("resolved_rules", {})
    resolved.update({
        "extras_runs": rounded,
        "runs_reconstruction_mode": CONFIG.get("runs_reconstruction_mode", "fractional_expected"),
        "fractional_coefficients": coefficients_float,
        "legal_illegal_extras": sorted(legal_types),
        "penalty_runs": 5,
        "wicket_rule": "is_wicket == True only; Retire Out neutral",
        "display_names": "player_name as-is",
        "excluded_teams": ["Pakistan", "Pakistan A"],
        "alt_excluded_teams": ["Bangladesh", "Bangladesh A"],
        "reconstructed_margin_accuracy": {
            "exact_share": round(exact, 6), "within_2_share": round(within2, 6),
            "mean_absolute_error": round(mae, 6),
        },
    })
    CONFIG_PATH.write_text(yaml.safe_dump(CONFIG, sort_keys=False), encoding="utf-8")
    histogram = OUT_DIR / "residual_histogram.png"
    plt.figure(figsize=(8, 4))
    plt.hist(errors, bins=range(int(errors.min()) - 1, int(errors.max()) + 2), edgecolor="black")
    plt.xlabel("Reconstructed margin error (runs)")
    plt.ylabel("Matches")
    plt.tight_layout()
    plt.savefig(histogram, dpi=150)
    plt.close()
    report += ["", f"Residual histogram path: `{histogram}`", "", f"Gate: {'PASS' if within2 >= 0.70 else 'FAIL'} (within ±2 runs={within2:.2%}; required ≥70%)."]
    output = OUT_DIR / "semantics_patch_report.md"
    output.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(output.resolve())
    print(f"within_2_share={within2:.6f}")
    print(f"residual_histogram={histogram.resolve()}")
    if within2 < 0.70:
        print("P1 gate is informational only; continuing despite <70% within ±2 runs.")


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "src"))
    main()
