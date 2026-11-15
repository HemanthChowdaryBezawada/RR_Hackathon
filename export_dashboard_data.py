#!/usr/bin/env python3
"""
export_dashboard_data.py  -  turn the model outputs into the JSON files the dashboard reads.

Usage (all paths relative to the repo root; every input except the player lists is optional):
  python export_dashboard_data.py --src outputs/final --out docs/data

It looks for these files inside --src (override any with the matching flag):
  batters.csv  bowlers.csv   (single final ranking, all eligible players, rating columns per 100 balls;
                              the older names batters_primary.csv / bowlers_primary.csv are accepted as a fallback)
  profiles.csv  tournament_summary.csv  sensitivity.csv  wp_report.csv  high_low.csv
  reliability.csv  cv_hyper.csv  kappa.csv  exclusions.csv  delta_evidence.csv  pressure_balls.parquet
Optional name lookups: --matches data_pack/matches.csv --teams data_pack/teams.csv
Nothing is invented: a missing input only removes the dashboard section that needs it (listed in meta.json).
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

IPL_TEAMS = {"Chennai Super Kings", "Delhi Capitals", "Gujarat Titans", "Kolkata Knight Riders", "Lucknow Super Giants",
             "Mumbai Indians", "Punjab Kings", "Rajasthan Royals", "Royal Challengers Bengaluru", "Sunrisers Hyderabad"}
RENAME = {
    "rating_runs_per_100_balls": "rating", "WPA_points_per_100_balls": "wpa",
    "beta_general_runs_per_100_balls": "beta", "delta_pressure_runs_per_100_balls": "delta",
    "lo80_runs_per_100_balls": "lo80", "hi80_runs_per_100_balls": "hi80",
    "beta_lo80_runs_per_100_balls": "beta_lo80", "beta_hi80_runs_per_100_balls": "beta_hi80",
    "delta_lo80_runs_per_100_balls": "delta_lo80", "delta_hi80_runs_per_100_balls": "delta_hi80",
    "P_top10": "p_top10", "n_HIGH_balls": "n_high", "n_IPL_HIGH_balls": "n_ipl_high", "n_T20I_HIGH_balls": "n_t20i_high",
    "days_since_last_match": "days_since", "active_365": "active", "display_name": "name", "mean_w_opp": "mean_w_opp",
}
WARN: list[str] = []


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if (o is None or not np.isfinite(o)) else round(float(o), 5)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (pd.Timestamp, datetime)):
        return o.strftime("%Y-%m-%d")
    return o


def read(path: Path | None, what: str, required: bool = False) -> pd.DataFrame | None:
    if path is None or not Path(path).exists():
        msg = f"missing {what}: {path}"
        if required:
            raise SystemExit("ERROR " + msg)
        WARN.append(msg)
        print("WARN", msg)
        return None
    return pd.read_parquet(path) if str(path).endswith(".parquet") else pd.read_csv(path, comment="#")


def split_teams(s) -> list[str]:
    return [t.strip() for t in str(s).split(",") if t.strip() and str(s) != "nan"]


def prep_players(df: pd.DataFrame, role: str) -> pd.DataFrame:
    d = df.rename(columns=RENAME).copy()
    d = d.sort_values("rating", ascending=False).reset_index(drop=True)
    d["rank"] = np.arange(1, len(d) + 1)
    d["role"] = role
    teams = d["teams"].map(split_teams)
    d["ipl_teams"] = teams.map(lambda t: [x for x in t if x in IPL_TEAMS])
    d["national_teams"] = teams.map(lambda t: [x for x in t if x not in IPL_TEAMS and not x.endswith(" A")])
    d["a_teams"] = teams.map(lambda t: [x for x in t if x.endswith(" A") and x not in IPL_TEAMS])
    d["ipl_experience"] = d["n_ipl_high"].fillna(0) > 0
    d["pctile"] = d["rating"].rank(pct=True) * 100
    return d


def combine(df: pd.DataFrame, role: str) -> list[dict]:
    p = prep_players(df, role)
    p["in_top10"] = p["rank"] <= 10
    keep = ["player_id", "name", "role", "rank", "in_top10", "rating", "wpa", "lo80", "hi80", "beta", "beta_lo80", "beta_hi80",
            "delta", "delta_lo80", "delta_hi80", "boot_sd", "p_top10", "n_high", "n_ipl_high", "n_t20i_high", "last_match_date",
            "days_since", "active", "mean_w_opp", "p_pos", "disaster_rate", "ipl_teams", "national_teams", "a_teams",
            "ipl_experience", "pctile"]
    extra = [c for c in ["estimator", "rating_ridge"] if c in p.columns]
    return p[[c for c in keep + extra if c in p.columns]].to_dict("records")


def attach_profiles(players: list[dict], prof: pd.DataFrame | None, role: str) -> list[dict]:
    if prof is None:
        return players
    q = prof[prof["role"] == role] if "role" in prof.columns else prof
    cols = {c.lower(): c for c in q.columns}
    pick = lambda *names: next((cols[n.lower()] for n in names if n.lower() in cols), None)
    mh, ml = pick("run_rate_high", "run_rate_per_over_high", "economy_high", "HIGH_metric"), pick("run_rate_low", "run_rate_per_over_low", "economy_low", "LOW_metric")
    sh, sl = pick("strike_rate_high"), pick("strike_rate_low")
    nh, nl = pick("HIGH_n"), pick("LOW_n")
    out = {}
    for r in q.itertuples(index=False):
        d = r._asdict()
        out[int(d[pick("player_id")])] = dict(
            metric_high=d.get(mh) if mh else None, metric_low=d.get(ml) if ml else None,
            strike_rate_high=d.get(sh) if sh else None, strike_rate_low=d.get(sl) if sl else None,
            high_n=d.get(nh) if nh else None, low_n=d.get(nl) if nl else None,
            low_sample_warning=bool(d.get(pick("low_sample_warning"))) if pick("low_sample_warning") else None)
    for p in players:
        p.update(out.get(int(p["player_id"]), {}))
        p["metric_label"] = "Run rate (runs per over)" if role == "batter" else "Economy (runs per over)"
    return players


def pressure_section(df: pd.DataFrame, matches: pd.DataFrame | None, teams: pd.DataFrame | None) -> dict:
    over = "over" if "over" in df.columns else "overid"
    need = {"innings", over, "w_before", "PI", "set", "wp_before", "batting_won", "match_id"}
    if not need <= set(df.columns):
        WARN.append(f"pressure_balls missing columns {sorted(need - set(df.columns))}")
        return {}
    d = df.copy()
    d["w"] = d["w_before"].clip(0, 9).astype(int)
    d["is_high"] = (d["set"] == "HIGH").astype(float)
    heat = {}
    for inn in (1, 2):
        g = d[d.innings == inn].groupby([over, "w"]).agg(pi=("PI", "mean"), high=("is_high", "mean"), n=("PI", "size")).reset_index()
        grid_pi = [[None] * 10 for _ in range(20)]
        grid_hi = [[None] * 10 for _ in range(20)]
        grid_n = [[0] * 10 for _ in range(20)]
        for r in g.itertuples(index=False):
            o, w = int(r[0]) - 1, int(r[1])
            if 0 <= o < 20:
                grid_pi[o][w], grid_hi[o][w], grid_n[o][w] = r.pi, r.high, int(r.n)
        heat[f"innings{inn}"] = dict(pi=grid_pi, high_share=grid_hi, n=grid_n)
    share = {f"innings{i}": d[d.innings == i].groupby(over)["is_high"].mean().reindex(range(1, 21)).tolist() for i in (1, 2)}
    bins = np.clip((d["wp_before"] * 10).astype(int), 0, 9)
    calib = {}
    for inn in (1, 2):
        s = d[d.innings == inn].assign(bin=bins[d.innings == inn])
        g = s.groupby("bin").agg(pred=("wp_before", "mean"), obs=("batting_won", "mean"), n=("wp_before", "size")).reset_index()
        calib[f"innings{inn}"] = g.to_dict("records")
    # example matches: innings-2 traces with many HIGH balls and a late swing
    traces = []
    d2 = d[d.innings == 2].sort_values(["match_id", "innings_ball_num"])
    score = d2.groupby("match_id").agg(nh=("is_high", "sum"), swing=("dWP", lambda x: x.abs().sum()), n=("PI", "size"))
    score = score[score.n >= 60].assign(s=lambda x: x.swing + 0.002 * x.nh).sort_values("s", ascending=False)
    names = teams.set_index("team_id")["team_name"].to_dict() if teams is not None and {"team_id", "team_name"} <= set(teams.columns) else {}
    minfo = matches.set_index("match_id") if matches is not None and "match_id" in matches.columns else None
    for mid in score.index[:4]:
        m = d2[d2.match_id == mid]
        bt = int(m["batting_team_id"].iloc[0]) if "batting_team_id" in m else None
        label = f"Match {int(mid)}"
        if minfo is not None and mid in minfo.index and "match_date" in minfo.columns:
            label += f" - {str(minfo.loc[mid, 'match_date'])[:10]}"
        traces.append(dict(match_id=int(mid), label=label, chasing_team=names.get(bt, str(bt)), chase_won=bool(m["batting_won"].iloc[0]),
                           balls=[f"{int(o)}.{i % 6 + 1}" for i, o in enumerate(m[over])], wp=m["wp_before"].round(4).tolist(),
                           pi=m["PI"].round(3).tolist(), high=(m["set"] == "HIGH").astype(int).tolist(),
                           wicket=m["wicket"].astype(int).tolist() if "wicket" in m else None,
                           runs=m["runs_total"].round(1).tolist() if "runs_total" in m else None))
    return dict(heatmap=heat, high_share_by_over=share, calibration=calib, traces=traces)


def table_records(df: pd.DataFrame | None) -> list[dict] | None:
    return None if df is None else df.to_dict("records")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="outputs/final")
    ap.add_argument("--out", default="docs/data")
    ap.add_argument("--matches")
    ap.add_argument("--teams")
    ap.add_argument("--hi_q", type=float, default=0.75)
    ap.add_argument("--pi_weights", default="0.60,0.25,0.15")
    for k in ("batters", "bowlers", "profiles", "tournament_summary", "sensitivity", "wp_report",
              "high_low", "reliability", "cv_hyper", "kappa", "exclusions", "delta_evidence", "pressure_balls"):
        ap.add_argument(f"--{k}")
    a = ap.parse_args()
    src, out = Path(a.src), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "downloads").mkdir(exist_ok=True)
    path = lambda k, ext="csv": Path(getattr(a, k)) if getattr(a, k) else src / f"{k}.{ext}"

    def first_existing(*names):
        for n in names:
            if (src / n).exists():
                return src / n
        return src / names[0]

    b_path = Path(a.batters) if a.batters else first_existing("batters.csv", "batters_primary.csv")
    w_path = Path(a.bowlers) if a.bowlers else first_existing("bowlers.csv", "bowlers_primary.csv")
    bp = read(b_path, "batters", required=True)
    wp_ = read(w_path, "bowlers", required=True)
    prof = read(path("profiles"), "profiles")
    batters = attach_profiles(combine(bp, "batter"), prof, "batter")
    bowlers = attach_profiles(combine(wp_, "bowler"), prof, "bowler")
    json.dump(clean(batters), open(out / "players_batters.json", "w"))
    json.dump(clean(bowlers), open(out / "players_bowlers.json", "w"))

    pb = read(path("pressure_balls", "parquet"), "pressure_balls.parquet")
    matches = read(Path(a.matches) if a.matches else None, "matches.csv")
    teams = read(Path(a.teams) if a.teams else None, "teams.csv")
    pressure = pressure_section(pb, matches, teams) if pb is not None else {}
    hl = read(path("high_low"), "high_low")
    pressure["high_low"] = table_records(hl)
    pressure["definition"] = dict(weights=dict(zip(["leverage_percentile", "closeness", "scarcity"], map(float, a.pi_weights.split(",")))),
                                  high_quantile=a.hi_q, low_quantile=0.5,
                                  formula="PI = 0.60*pct(LI) + 0.25*closeness + 0.15*scarcity; HIGH = top 25% of PI; LOW = bottom 50%")
    json.dump(clean(pressure), open(out / "pressure.json", "w"))

    validation = dict(wp_report=table_records(read(path("wp_report"), "wp_report")),
                      tournament=table_records(read(path("tournament_summary"), "tournament_summary")),
                      sensitivity=table_records(read(path("sensitivity"), "sensitivity")),
                      reliability=table_records(read(path("reliability"), "reliability")),
                      cv_hyper=(lambda d: None if d is None else d.head(12).to_dict("records"))(read(path("cv_hyper"), "cv_hyper")),
                      kappa=table_records(read(path("kappa"), "kappa")),
                      delta_evidence=table_records(read(path("delta_evidence"), "delta_evidence")),
                      exclusions=table_records(read(path("exclusions"), "exclusions")))
    json.dump(clean(validation), open(out / "validation.json", "w"))

    n_matches = int(pb["match_id"].nunique()) if pb is not None else None
    ipl_matches = int(pb.loc[pb.comp_group == "IPL", "match_id"].nunique()) if pb is not None and "comp_group" in pb else None
    meta = dict(generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                counts=dict(usable_matches=n_matches, usable_balls=None if pb is None else int(len(pb)), ipl_matches=ipl_matches,
                            t20i_and_other_matches=None if n_matches is None or ipl_matches is None else n_matches - ipl_matches,
                            eligible_batters=len(batters), eligible_bowlers=len(bowlers)),
                data_window=None if pb is None or "match_date" not in pb else [str(pd.to_datetime(pb.match_date).min().date()), str(pd.to_datetime(pb.match_date).max().date())],
                rules=dict(excluded_from_rankings=["Pakistan", "Pakistan A"],
                           included_note="Bangladeshi players are included: seven registered for the IPL 2027 mini-auction (16 Dec 2026); auction inclusion is not guaranteed.",
                           min_high_balls=dict(batter=150, bowler=120), min_consistency_units=12, min_seasons=2, active_within_days=365),
                missing_sections=WARN)
    json.dump(clean(meta), open(out / "meta.json", "w"), indent=1)

    for p in (b_path, w_path, path("profiles"), path("tournament_summary"), path("sensitivity")):
        if p.exists():
            shutil.copy(p, out / "downloads" / p.name)
    # section status: make it obvious what the dashboard will (not) be able to show
    status = {"players_batters": len(batters), "players_bowlers": len(bowlers),
              "pressure.heatmap": bool(pressure.get("heatmap")), "pressure.calibration": bool(pressure.get("calibration")),
              "pressure.traces": bool(pressure.get("traces")), "pressure.high_low": bool(pressure.get("high_low")),
              **{f"validation.{k}": bool(v) for k, v in validation.items()}}
    print("SECTION STATUS (MISSING = the dashboard hides that card):")
    for k, v in status.items():
        print(f"  {'OK     ' if v else 'MISSING'} {k}: {v}")
    print(f"OK  wrote {len(list(out.glob('*.json')))} JSON files to {out}  ({len(WARN)} warnings)")


if __name__ == "__main__":
    main()
