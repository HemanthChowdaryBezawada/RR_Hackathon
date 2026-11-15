"""Integration glue for the reference pressure_core implementation."""

from pathlib import Path
import hashlib
import json
import re
import shutil
import sys

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
import pressure_core as pc

CONFIG = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
DATA = (ROOT / CONFIG["data_dir"]).resolve()
OUT = ROOT / CONFIG["outputs_dir"]
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
AUDIT = OUT / "audit"
for path in (TABLES, FIGURES, AUDIT):
    path.mkdir(parents=True, exist_ok=True)
C = CONFIG["columns"]


def cache_key() -> str:
    """Hash config and source mtimes for reproducibility."""
    payload = {"config": CONFIG, "files": {p.name: p.stat().st_mtime_ns for p in DATA.glob("*.csv")}}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:16]


def load_data():
    """Read all source CSVs with pandas low_memory disabled."""
    names = ("ball_by_ball.csv", "matches.csv", "competitions.csv", "teams.csv", "competition_team_player_mapping.csv")
    return [pd.read_csv(DATA / name, low_memory=False) for name in names]


def reconstructed_runs(df: pd.DataFrame, mode: str) -> pd.Series:
    """Apply the configured fractional, rounded, or base-only score reconstruction."""
    extras = df[C["extras_type"]]
    value = df[C["runs"]].astype(float) + extras.isin(["wide", "Overstep", "other"]).astype(int)
    value += extras.eq("Penalty").astype(int) * 4
    coefficients = {"wide": 0.1738, "legbyes": 1.3314, "byes": 2.1389}
    if mode == "rounded":
        coefficients = {key: round(value) for key, value in coefficients.items()}
    if mode != "base_only":
        value.loc[extras.eq("wide")] = 1 + coefficients["wide"]
        value.loc[extras.eq("legbyes")] = max(1, coefficients["legbyes"])
        value.loc[extras.eq("byes")] = max(1, coefficients["byes"])
    return value


def usable_match_ids(ball: pd.DataFrame, matches: pd.DataFrame) -> set[int]:
    """Apply the patched innings and match exclusions without score reconstruction."""
    legal = ~ball[C["extras_type"]].isin(["wide", "Overstep", "other"])
    stats = ball.assign(_legal=legal).groupby([C["match_id"], C["innings"]]).agg(
        legal=("_legal", "sum"), wickets=(C["is_wicket"], "sum")
    )
    first = stats[stats.index.get_level_values(C["innings"]) == 1]
    second = stats[stats.index.get_level_values(C["innings"]) == 2]
    first_ok = set(first.index.get_level_values(C["match_id"])[(first.legal >= 120) | (first.wickets >= 9)])
    chase = ball[ball[C["innings"]].eq(2)].groupby(C["match_id"])[C["batting_team_id"]].first()
    winners = matches.set_index(C["match_id"])[C["winner_team_id"]]
    chased = set(chase.index[chase.eq(winners.reindex(chase.index))])
    second_ok = set(second.index.get_level_values(C["match_id"])[
        (second.legal >= 120) | (second.wickets >= 9)
        | second.index.get_level_values(C["match_id"]).isin(chased)
    ])
    results = matches[C["match_result"]].fillna("").astype(str)
    excluded = {
        "super_over": set(ball.loc[ball[C["innings"]] > 2, C["match_id"]]),
        "revised": set(matches.loc[results.str.contains(r"D/?L|Duckworth|revised", case=False, regex=True), C["match_id"]]),
        "null_winner": set(matches.loc[matches[C["winner_team_id"]].isna() | results.str.contains("no result", case=False), C["match_id"]]),
        "missing_ball": set(matches[C["match_id"]]) - set(ball[C["match_id"]]),
        "innings_1_invalid": set(matches[C["match_id"]]) - first_ok,
        "innings_2_invalid": set(matches[C["match_id"]]) - second_ok,
        "rain_short": set(first.index.get_level_values(C["match_id"])[(first.legal < 120) & (first.wickets < 9)]),
    }
    return set(matches[C["match_id"]]) - set().union(*excluded.values())


def build_delivery_frame(ball, matches, competitions, teams, usable, mode):
    """Create the canonical pressure_core delivery frame."""
    d = ball[ball[C["match_id"]].isin(usable) & ball[C["innings"]].isin([1, 2])].copy()
    d["runs_total"] = reconstructed_runs(d, mode)
    d["legal"] = ~d[C["extras_type"]].isin(["wide", "Overstep", "other"])
    d["wicket"] = d[C["is_wicket"]].astype(bool)
    d.loc[d[C["dismissal_type"]].fillna("").eq("Retire Out"), "wicket"] = False
    d.loc[d[C["dismissed_player_id"]].notna() & ~d[C["is_wicket"]], "wicket"] = False
    meta = matches[[C["match_id"], C["competition_id"], C["match_date"], C["winner_team_id"], C["home_team_id"], C["away_team_id"], "venue_id"]]
    d = d.merge(meta, on=C["match_id"], how="left")
    comp = competitions[[C["competition_id"], C["competition_name"], "match_format", C["season"]]]
    d = d.merge(comp, on=C["competition_id"], how="left")
    d["comp_group"] = np.where(
        d[C["competition_name"]].astype(str).str.contains(r"Indian Premier League|IPL", case=False, regex=True),
        "IPL", np.where(d["match_format"].eq("T20I"), "T20I", "T20_other")
    )
    d["season_year"] = pd.to_datetime(d[C["match_date"]], errors="coerce").dt.year
    d["batting_won"] = (d[C["batting_team_id"]] == d[C["winner_team_id"]]).astype(int)
    d = d.rename(columns={
        C["match_id"]: "match_id", C["innings"]: "innings", C["over"]: "over",
        C["innings_ball"]: "innings_ball_num", C["batting_team_id"]: "batting_team_id",
        C["bowling_team_id"]: "bowling_team_id", C["striker_id"]: "striker_id",
        C["bowler_id"]: "bowler_id", C["dismissed_player_id"]: "dismissed_player_id",
        C["extras_type"]: "extras_type", C["dismissal_type"]: "dismissal_type",
        C["runs"]: "runs", C["match_date"]: "match_date",
    })
    return d


def prepare_matches(matches, teams, competitions):
    """Assign the reference Elo pools from competition and team names."""
    team_names = teams.set_index(C["team_id"])[C["team_name"]].astype(str)
    a_ids = set(team_names[team_names.str.endswith(" A")].index)
    comp_name = competitions.set_index(C["competition_id"])[C["competition_name"]].astype(str)
    pools = []
    for row in matches.itertuples(index=False):
        comp = comp_name.getattr(row, "") if False else comp_name.get(getattr(row, C["competition_id"]), "")
        pool = "IPL" if re.search(r"Indian Premier League|IPL", str(comp), re.I) else "NAT"
        if getattr(row, C["home_team_id"]) in a_ids or getattr(row, C["away_team_id"]) in a_ids:
            pool = "A"
        pools.append(pool)
    out = matches.copy()
    out["pool"] = pools
    return out, a_ids


def markdown(frame: pd.DataFrame) -> str:
    """Render a computed DataFrame as Markdown."""
    cols = list(map(str, frame.columns))
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    lines += ["| " + " | ".join(str(value) for value in row) + " |" for row in frame.itertuples(index=False, name=None)]
    return "\n".join(lines)


def run(mode: str, hi_q: float, half_life: float, do_bootstrap: bool = True):
    """Run the canonical core for one sensitivity configuration."""
    ball, matches, competitions, teams, mapping = load_data()
    usable = usable_match_ids(ball, matches)
    d = build_delivery_frame(ball, matches, competitions, teams, usable, mode)
    d["venue_id"] = d["venue_id"].fillna(-1)
    d = pc.add_state(d)
    d["par"] = d.match_id.map(pc.venue_par(d)).fillna(d.groupby("comp_group")["runs_total"].transform("mean"))
    m2, a_ids = prepare_matches(matches, teams, competitions)
    elo = pc.pre_match_elo(m2)
    home = m2.set_index("match_id")["home_team_id"]
    d = pc.attach_elo(d, elo, home)
    d["w_opp"] = pc.opp_weight(d, a_ids)
    d["w_time"] = pc.time_weight(d.match_date, half_life)
    rt = pc.ResourceTable().fit(d)
    d["res"] = rt.lookup(d.b, d.w_before)
    folds = pc.assign_folds(d.match_id)
    wpm = pc.WPModel(rt, folds, n_jobs=CONFIG.get("n_jobs", 6))
    d["wp_before"] = wpm.fit(d)
    report = pc.wp_report(d)
    d = pc.chain_wp(d)
    d["LI"] = pc.expected_leverage(d, wpm, pc.outcome_probs(d))
    d = pc.pressure_index(d, rt, hi_q=hi_q)
    high_low = pc.high_low_table(d)
    d = pc.fit_expected(d, folds, n_jobs=CONFIG.get("n_jobs", 6))
    K = pc.estimate_K(d)
    d = pc.add_ball_value(d, K)
    d = pc.attribution(d)
    rd = pc.RidgeData(d, folds)
    cv = pc.cv_hyper(rd, alphas=[5, 15, 50, 150, 500], rhos=[1, 3, 10, 30, 100, np.inf], n_splits=5, n_jobs=CONFIG.get("n_jobs", 6))
    best = cv.iloc[0]
    raw_tournament, tournament = pc.tournament(rd, rhos=(3, 10, 30), alpha=float(best.alpha_g), n_splits=100, n_jobs=CONFIG.get("n_jobs", 6), min_balls=30)
    fitted = pc.fit_ridge(rd, float(best.rho), float(best.alpha_g))
    if do_bootstrap:
        bat_boot, bowl_boot = pc.bootstrap_ratings(rd, float(best.rho), float(best.alpha_g), reps=300, n_jobs=CONFIG.get("n_jobs", 6))
    else:
        bat_boot = np.zeros((1, rd.nb))
        bowl_boot = np.zeros((1, rd.nw))
    return locals()


def main():
    """Run default pipeline, validations, rankings, and computed audit outputs."""
    key = cache_key()
    print(f"cache_key={key}")
    default = run(CONFIG.get("runs_reconstruction_mode", "fractional_expected"), 0.75, 730)
    d, rd, K, cv, tournament = default["d"], default["rd"], default["K"], default["cv"], default["tournament"]
    print(default["report"].round(4).to_string(index=False))
    print(default["high_low"].round(4).to_string(index=False))
    print(pd.DataFrame(K).T.to_string())
    print(cv.head(10).to_string(index=False))
    print(tournament.to_string(index=False))
    cv.to_csv(TABLES / "cv_hyper.csv", index=False)
    default["raw_tournament"].to_csv(TABLES / "tournament_raw.csv", index=False)
    tournament.to_csv(TABLES / "tournament_summary.csv", index=False)
    default["report"].to_csv(TABLES / "wp_report.csv", index=False)
    default["high_low"].to_csv(TABLES / "high_low_table.csv", index=False)
    pd.DataFrame(K).T.to_csv(TABLES / "kappa_table.csv")
    d.to_parquet(TABLES / "pressure_balls.parquet", index=False)

    primary = set(default["mapping"].loc[default["mapping"][C["team_name"]].isin(["Pakistan", "Pakistan A"]), C["player_id"]].dropna().astype(int))
    alternate = primary | set(default["mapping"].loc[default["mapping"][C["team_name"]].isin(["Bangladesh", "Bangladesh A"]), C["player_id"]].dropna().astype(int))
    def ranking(ids, role, boot, col, threshold):
        counts = d[d["set"].eq("HIGH") & d[col].notna()].groupby(col).size()
        eligible = counts[(counts >= threshold) & ~counts.index.astype(int).isin(ids)].index
        fit_values = default["fitted"]["bat_high"] if role == "batter" else default["fitted"]["bow_high"]
        player_ids = rd.bat_ids if role == "batter" else rd.bow_ids
        scores = pd.Series(fit_values, index=player_ids).reindex(eligible).dropna().sort_values(ascending=False)
        summary = pc.summarize_boot(fit_values, boot, pd.Series(player_ids).isin(eligible).to_numpy())
        summary["player_id"] = player_ids
        summary = summary[summary["player_id"].isin(scores.index)].sort_values("rating", ascending=False)
        names = default["mapping"][[C["player_id"], C["player_name"]]].drop_duplicates(C["player_id"]).rename(columns={C["player_id"]: "player_id", C["player_name"]: "display_name"})
        summary = summary.merge(names, on="player_id", how="left")
        summary["rating_runs_per_100"] = summary["rating"] * 100
        summary["WPA_per_100"] = summary["rating"] * K["all"]["kappa_run"] * 100
        summary.insert(0, "rank", range(1, len(summary) + 1))
        return summary.head(10)
    bat = ranking(primary, "batter", default["bat_boot"], "striker_id", 150)
    bowl = ranking(primary, "bowler", default["bowl_boot"], "bowler_id", 120)
    alt_bat = ranking(alternate, "batter", default["bat_boot"], "striker_id", 150)
    alt_bowl = ranking(alternate, "bowler", default["bowl_boot"], "bowler_id", 120)
    bat.to_csv(TABLES / "final_top10_batters.csv", index=False)
    bowl.to_csv(TABLES / "final_top10_bowlers.csv", index=False)
    alt_bat.to_csv(TABLES / "alternate_top10_batters.csv", index=False)
    alt_bowl.to_csv(TABLES / "alternate_top10_bowlers.csv", index=False)
    rel_bat = pc.reliability_diagnostics(d.loc[d.bat_ok & d.set.eq("HIGH"), "striker_id"].to_numpy(), d.loc[d.bat_ok & d.set.eq("HIGH"), "y"].to_numpy(), 30)
    rel_bowl = pc.reliability_diagnostics(d.loc[d.bow_ok & d.set.eq("HIGH"), "bowler_id"].to_numpy(), d.loc[d.bow_ok & d.set.eq("HIGH"), "y"].to_numpy(), 30)
    reliability = pd.DataFrame([{"role": "batter", **rel_bat}, {"role": "bowler", **rel_bowl}])
    reliability.to_csv(TABLES / "reliability_diagnostics.csv", index=False)
    sensitivity = []
    for mode in ("fractional_expected", "rounded", "base_only"):
        trial = run(mode, 0.75, 730, do_bootstrap=False)
        trial_ids = set(pd.Series(trial["fitted"]["bat_high"], index=trial["rd"].bat_ids).nlargest(10).index)
        base_ids = set(pd.Series(default["fitted"]["bat_high"], index=rd.bat_ids).nlargest(10).index)
        sensitivity.append({"run": mode, "top10_overlap": len(trial_ids & base_ids), "kendall_tau": pd.Series(trial["fitted"]["bat_high"], index=trial["rd"].bat_ids).corr(pd.Series(default["fitted"]["bat_high"], index=rd.bat_ids), method="kendall")})
    for hi in (0.70, 0.80):
        trial = run("fractional_expected", hi, 730, do_bootstrap=False)
        sensitivity.append({"run": f"PI_q{hi:.2f}", "top10_overlap": len(set(pd.Series(trial["fitted"]["bat_high"], index=trial["rd"].bat_ids).nlargest(10).index) & set(pd.Series(default["fitted"]["bat_high"], index=rd.bat_ids).nlargest(10).index)), "kendall_tau": pd.Series(trial["fitted"]["bat_high"], index=trial["rd"].bat_ids).corr(pd.Series(default["fitted"]["bat_high"], index=rd.bat_ids), method="kendall")})
    sensitivity_df = pd.DataFrame(sensitivity)
    sensitivity_df.to_csv(TABLES / "sensitivity.csv", index=False)
    audit = ["# Audit report", "", f"Cache key: `{key}`", "", "## WP report", markdown(default["report"]), "", "## HIGH/LOW", markdown(default["high_low"]), "", "## K", markdown(pd.DataFrame(K).T.reset_index()), "", "## Reliability", markdown(reliability), "", "## Tournament", markdown(tournament), "", "## Sensitivity", markdown(sensitivity_df)]
    (AUDIT / "audit_report.md").write_text("\n".join(audit) + "\n", encoding="utf-8")
    report = ["# Computed report tables", "", "## WP", markdown(default["report"]), "", "## HIGH/LOW", markdown(default["high_low"]), "", "## K", markdown(pd.DataFrame(K).T.reset_index()), "", "## CV", markdown(cv.head(10)), "", "## Tournament", markdown(tournament), "", "## Reliability", markdown(reliability), "", "## Sensitivity", markdown(sensitivity_df)]
    (OUT / "report_tables.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("PRIMARY BATTERS\n", bat.to_string(index=False))
    print("PRIMARY BOWLERS\n", bowl.to_string(index=False))
    print("ALTERNATE BATTERS\n", alt_bat.to_string(index=False))
    print("ALTERNATE BOWLERS\n", alt_bowl.to_string(index=False))
    print("RELIABILITY\n", reliability.to_string(index=False))
    print("SENSITIVITY\n", sensitivity_df.to_string(index=False))
    print(f"audit_report={AUDIT / 'audit_report.md'}")


if __name__ == "__main__":
    main()
