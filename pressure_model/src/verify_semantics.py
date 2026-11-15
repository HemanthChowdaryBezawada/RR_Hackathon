"""Verify the cricket data semantics required before modeling pressure."""

from pathlib import Path
import re
import sys
from typing import Any

import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.yaml"
CONFIG = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
DATA_DIR = (ROOT / CONFIG["data_dir"]).resolve()
OUT_DIR = ROOT / CONFIG["outputs_dir"]
OUT_DIR.mkdir(parents=True, exist_ok=True)
C = CONFIG["columns"]


def load(name: str) -> pd.DataFrame:
    """Load one source table without inference shortcuts."""
    return pd.read_csv(DATA_DIR / name, low_memory=False)


def result_number(value: Any, phrase: str) -> int | None:
    """Extract the integer in a result phrase, or return None."""
    match = re.search(rf"won by\s+(\d+)\s+{phrase}", str(value), re.I)
    return int(match.group(1)) if match else None


def result_is_clean_runs(value: Any) -> bool:
    """Identify ordinary run-margin results eligible for run validation."""
    text = str(value)
    return bool(re.search(r"won by\s+\d+\s+runs", text, re.I)) and not bool(
        re.search(r"D/?L|Duckworth|revised|super", text, re.I)
    )


def status(ok: bool, detail: str) -> str:
    """Format one explicit semantic test result."""
    return f"{'PASS' if ok else 'FAIL'}: {detail}"


def fmt(value: Any) -> str:
    """Format report values compactly."""
    if pd.isna(value):
        return "null"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def main() -> None:
    ball = load("ball_by_ball.csv")
    matches = load("matches.csv")
    playing = load("playing_eleven.csv")
    teams = load("teams.csv")
    competitions = load("competitions.csv")
    mapping = load("competition_team_player_mapping.csv")
    report: list[str] = [
        "# Part A - Semantics Verification",
        "",
        f"Data directory: `{DATA_DIR}`",
        "",
        "All six CSVs were read with `low_memory=False`. No modeling or ranking was run.",
        "",
        "## A1. Extras code map",
        "",
    ]

    extras = ball[[C["extras_type"], C["extras_code"]]].copy()
    extras[C["extras_type"]] = extras[C["extras_type"]].fillna("<null>")
    cross = pd.crosstab(extras[C["extras_type"]], extras[C["extras_code"]])
    report += ["| extras_type | extras1_runs counts |", "| --- | --- |"]
    for name, row in cross.iterrows():
        report.append(f"| {name} | " + ", ".join(f"{code}: {int(count)}" for code, count in row.items() if count) + " |")
    code_map = extras.groupby(C["extras_type"])[C["extras_code"]].nunique()
    one_to_one = bool((code_map <= 1).all())
    report += [
        "",
        status(one_to_one, f"extras1_runs is a one-to-one category code: {one_to_one}; exclude it from run sums."),
        "",
        "## A2. Run semantics",
        "",
    ]
    type_col = C["extras_type"]
    runs_col = C["runs"]
    extras2_col = C["extras_runs"]
    overstep = ball[type_col].eq("Overstep")
    wide = ball[type_col].eq("wide")
    r1 = ball[runs_col]
    r2 = r1 + (wide | overstep).astype(int)
    r3 = r1 + ball[extras2_col]
    r4 = r2 + ball[extras2_col]
    formulas = {"R1=runs": r1, "R2=runs+wide/Overstep": r2, "R3=runs+extras_2_runs": r3, "R4=R2+extras_2_runs": r4}
    eligible_matches = matches[matches[C["match_result"]].map(result_is_clean_runs)].copy()
    margins = eligible_matches.set_index(C["match_id"])[C["match_result"]].map(lambda x: result_number(x, "runs"))
    report += ["| Formula | Matches checked | Exact margin matches | Match rate |", "| --- | ---: | ---: | ---: |"]
    formula_rates: dict[str, float] = {}
    for name, values in formulas.items():
        temp = ball[ball[C["innings"]].isin([1, 2])].copy()
        temp["_value"] = values.loc[temp.index]
        totals = temp.groupby([C["match_id"], C["innings"]])["_value"].sum().unstack()
        common = totals.join(margins.rename("_margin"), how="inner").dropna()
        exact = ((common[1] - common[2]).abs() == common["_margin"]).sum()
        rate = exact / len(common) if len(common) else 0
        formula_rates[name] = rate
        report.append(f"| {name} | {len(common)} | {exact} | {rate:.2%} |")
    chosen_formula = max(formula_rates, key=formula_rates.get)
    chosen = formulas[chosen_formula]
    report += [f"", status(formula_rates[chosen_formula] >= 0.95, f"chosen formula `{chosen_formula}` with rate {formula_rates[chosen_formula]:.2%}."), "", "| extras_type | rows | runs distribution |", "| --- | ---: | --- |"]
    for name in ["wide", "legbyes", "byes", "Overstep"]:
        subset = ball[ball[type_col].eq(name)][runs_col].value_counts().sort_index()
        report.append(f"| {name} | {len(ball[ball[type_col].eq(name)]):,} | " + ", ".join(f"{fmt(k)}: {v}" for k, v in subset.items()) + " |")

    report += ["", "## A3. Derived runs semantics", ""]
    run_bat = chosen.copy()
    run_bat[ball[type_col].isin(["wide", "byes", "legbyes"])] = 0
    run_bat[overstep] = np.maximum(chosen[overstep] - 1, 0)
    flagged = ball[C["is_four"]] | ball[C["is_six"]]
    flagged_ok = run_bat[flagged].isin([4, 6]).mean() if flagged.any() else 1.0
    report += [status(flagged_ok >= 0.95, f"flagged boundary rows have runs_off_bat in {{4,6}} at rate {flagged_ok:.2%} ({int(flagged.sum())} rows).")]

    report += ["", "## A4. Legal-ball rule", ""]
    candidate_sets = [
        {"wide", "Overstep"},
        {"wide", "Overstep", "other"},
        {"wide", "Overstep", "Penalty"},
        {"wide", "Overstep", "other", "Penalty"},
    ]
    legal_rows = []
    for illegal in candidate_sets:
        temp = ball.copy()
        temp["_illegal"] = temp[type_col].isin(illegal)
        last_over = temp.groupby([C["match_id"], C["innings"]])[C["over"]].transform("max")
        temp = temp[temp[C["over"]] != last_over]
        over_counts = temp.groupby([C["match_id"], C["innings"], C["over"]])["_illegal"].apply(lambda x: int((~x).sum()))
        share = float((over_counts == 6).mean()) if len(over_counts) else 0
        legal_rows.append((illegal, share, len(over_counts)))
    report += ["| Illegal extras set | Overs checked | Exactly-six share |", "| --- | ---: | ---: |"]
    for illegal, share, count in legal_rows:
        report.append(f"| {{{', '.join(sorted(illegal))}}} | {count:,} | {share:.2%} |")
    chosen_illegal, chosen_share, _ = max(legal_rows, key=lambda x: x[1])
    penalty_rows = ball[ball[type_col].eq("Penalty")]
    report += [status(chosen_share == max(row[1] for row in legal_rows), f"chosen illegal set {{{', '.join(sorted(chosen_illegal))}}}; Penalty rows={len(penalty_rows):,}, non-delivery under chosen rule={int(penalty_rows[type_col].isin(chosen_illegal).sum()):,}.")]

    report += ["", "## A5. Wicket rule", ""]
    wicket_matches = matches[matches[C["match_result"]].map(lambda x: result_number(x, "wickets") is not None)].copy()
    wicket_margin = wicket_matches.set_index(C["match_id"])[C["match_result"]].map(lambda x: result_number(x, "wickets"))
    second = ball[ball[C["innings"]].eq(2)].copy()
    second["_all"] = second[C["is_wicket"]].astype(int)
    second["_no_retire"] = second["_all"] & ~second[C["dismissal_type"]].fillna("").eq("Retire Out")
    second["_strict"] = second["_no_retire"] & second[C["dismissed_player_id"]].notna()
    wicket_totals = second.groupby(C["match_id"])[["_all", "_no_retire", "_strict"]].sum()
    report += ["| Rule | Matches | Exact wicket-margin matches | Rate |", "| --- | ---: | ---: | ---: |"]
    wicket_rates = {}
    for rule in ["_all", "_no_retire", "_strict"]:
        common = wicket_totals.join(wicket_margin.rename("margin"), how="inner").dropna()
        exact = (10 - common[rule] == common["margin"]).sum()
        wicket_rates[rule] = exact / len(common) if len(common) else 0
        report.append(f"| {rule} | {len(common)} | {exact} | {wicket_rates[rule]:.2%} |")
    dismissed_without_flag = ball[ball[C["dismissed_player_id"]].notna() & ~ball[C["is_wicket"]]]
    report += [status(True, f"chosen wicket rule `{max(wicket_rates, key=wicket_rates.get)}`; dismissed_player_id present while is_wicket=False: {len(dismissed_without_flag)} rows."), "", "Rows with dismissed_player_id but is_wicket=False:", ""]
    report += [f"- match_id={row[C['match_id']]}, innings={row[C['innings']]}, dismissed_player_id={row[C['dismissed_player_id']]}, dismissal_type={row[C['dismissal_type']]}" for _, row in dismissed_without_flag.iterrows()]

    report += ["", "## A6. Ordering", ""]
    grouped_order = ball.sort_values([C["match_id"], C["innings"], C["innings_ball"]]).groupby([C["match_id"], C["innings"]])[C["innings_ball"]]
    bad_order = 0
    bad_duplicate = 0
    for _, values in grouped_order:
        bad_order += int((values.diff().dropna() <= 0).sum())
        bad_duplicate += int(values.duplicated().sum())
    report += [status(bad_order == 0 and bad_duplicate == 0, f"ordering violations={bad_order}, duplicate innings_ball_num values={bad_duplicate}.")]

    report += ["", "## A7. Coverage", ""]
    covered_ids = set(ball[C["match_id"]].unique())
    uncovered = matches[~matches[C["match_id"]].isin(covered_ids)]
    report += [f"Matches without ball data: {len(uncovered)}", "", "| match_id | date | comp_id | result |", "| --- | --- | --- | --- |"]
    report += [f"| {row[C['match_id']]} | {row['match_date']} | {row[C['competition_id']]} | {row[C['match_result']]} |" for _, row in uncovered.iterrows()]
    report += [status(True, "matches without ball data are excluded from downstream semantic calculations.")]

    report += ["", "## A8. Exclusion audit", ""]
    match_ids = set(matches[C["match_id"]])
    super_over = set(ball.loc[ball[C["innings"]] > 2, C["match_id"]])
    dl = set(matches.loc[matches[C["match_result"]].astype(str).str.contains(r"D/?L|Duckworth|revised", case=False, regex=True, na=False), C["match_id"]])
    null_winner = set(matches.loc[matches[C["winner_team_id"]].isna() | matches[C["match_result"]].astype(str).str.contains("no result", case=False), C["match_id"]])
    legal = ~ball[type_col].isin(chosen_illegal)
    innings_counts = ball.assign(_legal=legal).groupby([C["match_id"], C["innings"]])["_legal"].sum().unstack()
    first_short = set(innings_counts.index[(innings_counts.get(1, pd.Series(dtype=float)) < 120) & (innings_counts.get(1, pd.Series(dtype=float)) > 0)])
    second_anomaly = set(innings_counts.index[innings_counts.get(2, pd.Series(dtype=float)).fillna(0) == 0])
    missing_venue = set(matches.loc[matches["venue_id"].isna(), C["match_id"]]) if "venue_id" in matches else set()
    audit = [
        ("super-over rows (innings > 2)", len(super_over)),
        ("D/L or revised overs/target", len(dl)),
        ("null win_team_id or no result", len(null_winner)),
        ("innings 1 neither all-out nor 120 legal balls (proxy: <120 legal)", len(first_short)),
        ("innings 2 anomalies (no legal balls)", len(second_anomaly)),
        ("missing venue", len(missing_venue)),
    ]
    report += ["| Exclusion reason | Matches |", "| --- | ---: |"] + [f"| {name} | {count} |" for name, count in audit]
    excluded = super_over | dl | null_winner | first_short | second_anomaly | missing_venue | set(uncovered[C["match_id"]])
    usable_matches = match_ids - excluded
    report += [f"", f"Final usable matches: {len(usable_matches)}", f"Final usable ball rows: {int(ball[C['match_id']].isin(usable_matches).sum())}"]

    report += ["", "## A9. Competitions", ""]
    comp_counts = matches.groupby(C["competition_id"]).size().rename("matches")
    comp_info = competitions.merge(comp_counts, left_on=C["competition_id"], right_index=True, how="left")
    t20 = comp_info[comp_info["match_format"].eq("T20")]
    report += ["### T20 competitions", "", "| comp_id | comp_name | season/date range | matches |", "| --- | --- | --- | ---: |"]
    for _, row in t20.iterrows():
        dates = matches.loc[matches[C["competition_id"]].eq(row[C["competition_id"]]), "match_date"]
        report.append(f"| {row[C['competition_id']]} | {row[C['competition_name']]} | {dates.min()} to {dates.max()} | {int(row.get('matches', 0))} |")
    ipl = comp_info[comp_info[C["competition_name"]].astype(str).str.contains(r"Indian Premier League|IPL", case=False, regex=True)]
    report += ["", "### IPL competitions", "", "| comp_id | comp_name | season | matches |", "| --- | --- | --- | ---: |"]
    for _, row in ipl.iterrows():
        report.append(f"| {row[C['competition_id']]} | {row[C['competition_name']]} | {row[C['season']]} | {int(row.get('matches', 0))} |")
    comp_group = competitions[[C["competition_id"], C["competition_name"], "match_format"]].copy()
    comp_group["comp_group"] = np.where(comp_group[C["competition_name"]].str.contains(r"Indian Premier League|IPL", case=False, regex=True), "IPL", np.where(comp_group["match_format"].eq("T20I"), "T20I", "T20_other"))
    report += ["", "Resolved comp_group: IPL for IPL-name competitions; T20I for match_format=T20I; T20_other otherwise.", "", "IPL seasons present: " + ", ".join(map(str, sorted(ipl[C["season"]].dropna().unique()))) + "."]

    report += ["", "## A10. Identity", ""]
    collisions = mapping.groupby(C["player_id"])[C["player_name"]].nunique()
    collision_ids = set(collisions[collisions > 1].index)
    report += [f"Player ids sharing more than one name: {len(collision_ids)}", "", "| player_id | names |", "| --- | --- |"]
    for player_id in sorted(collision_ids):
        names = sorted(mapping.loc[mapping[C["player_id"]].eq(player_id), C["player_name"]].dropna().unique())
        report.append(f"| {player_id} | {', '.join(map(str, names))} |")
    ball_ids = set(ball[[C["striker_id"], C["non_striker_id"], C["bowler_id"], C["dismissed_player_id"]]].stack().dropna().astype(int))
    mapping_ids = set(mapping[C["player_id"]].dropna().astype(int))
    missing_players = sorted(ball_ids - mapping_ids)
    report += ["", f"Player ids in ball_by_ball absent from mapping: {len(missing_players)}", ", ".join(map(str, missing_players)) if missing_players else "none"]

    report += ["", "## A11. Pakistan and Bangladesh audit", ""]
    names = mapping[[C["player_id"], C["player_name"], C["team_name"]]].drop_duplicates()
    pakistan_ids = set(names.loc[names[C["team_name"]].isin(["Pakistan", "Pakistan A"]), C["player_id"]])
    pakistan_ids |= set(ball.loc[ball[C["batting_team_id"]].isin(teams.loc[teams[C["team_name"]].isin(["Pakistan", "Pakistan A"]), "team_id"]), C["striker_id"]])
    pakistan_ids |= set(ball.loc[ball[C["bowling_team_id"]].isin(teams.loc[teams[C["team_name"]].isin(["Pakistan", "Pakistan A"]), "team_id"]), C["bowler_id"]])
    report += ["### Pakistan/Pakistan A players", "", "| player_id | names |", "| --- | --- |"]
    for player_id in sorted(pakistan_ids):
        found = names.loc[names[C["player_id"]].eq(player_id), C["player_name"]].dropna().unique()
        report.append(f"| {player_id} | {', '.join(map(str, found)) or '(name unavailable)'} |")
    bangladesh_ids = set(names.loc[names[C["team_name"]].isin(["Bangladesh", "Bangladesh A"]), C["player_id"]])
    report += ["", "### Bangladesh/Bangladesh A players", "", "| player_id | names |", "| --- | --- |"]
    for player_id in sorted(bangladesh_ids):
        found = names.loc[names[C["player_id"]].eq(player_id), C["player_name"]].dropna().unique()
        report.append(f"| {player_id} | {', '.join(map(str, found)) or '(name unavailable)'} |")

    resolved = {
        "run_formula": chosen_formula,
        "illegal_extras": sorted(chosen_illegal),
        "wicket_rule": max(wicket_rates, key=wicket_rates.get),
        "exclude_matches_without_ball_data": True,
        "excluded_teams": ["Pakistan", "Pakistan A"],
        "alt_excluded_teams": ["Bangladesh", "Bangladesh A"],
    }
    CONFIG["resolved_rules"] = resolved
    CONFIG_PATH.write_text(yaml.safe_dump(CONFIG, sort_keys=False), encoding="utf-8")
    report += ["", "## Resolved rules written to config.yaml", "", "```yaml", yaml.safe_dump(resolved, sort_keys=False).rstrip(), "```", "", "PART A COMPLETE. STOP before Part B."]
    output = OUT_DIR / "semantics_report.md"
    output.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(output.resolve())


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "src"))
    main()
