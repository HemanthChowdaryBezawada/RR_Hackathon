#!/usr/bin/env python3
"""
make_report_assets.py - build every figure/table/number the methodology PPT needs, from the model outputs.

Usage:
  python make_report_assets.py --src outputs/final --out report_assets

Inputs (same names as export_dashboard_data.py; anything missing only skips the figure that needs it):
  batters.csv bowlers.csv (single final ranking; *_primary.csv accepted as a fallback) profiles.csv tournament_summary.csv sensitivity.csv
  wp_report.csv high_low.csv exclusions.csv pressure_balls.parquet
Outputs: report_assets/figures/F*.png (16:9-friendly), report_assets/tables/T*.csv, report_assets/facts.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

NAVY, PINK, SLATE, MID, LIGHT, TEAL, AMBER = "#0B1B3F", "#E6007E", "#8A94A6", "#C5CBD8", "#F4F5F9", "#1F9D8F", "#F2A900"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": MID, "axes.labelcolor": NAVY, "xtick.color": NAVY,
                     "ytick.color": NAVY, "text.color": NAVY, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": "#E6E9F0", "grid.linewidth": 0.8, "figure.dpi": 100, "savefig.dpi": 220})
SKIPPED: list[str] = []

# From semantics_patch_report.md (runs reconstruction). Source numbers, not recomputed here.
RESIDUAL_HIST = {-10: 2, -8: 2, -7: 4, -6: 3, -5: 10, -4: 24, -3: 25, -2: 26, -1: 37, 0: 86, 1: 56, 2: 21, 3: 22, 4: 17, 5: 10, 6: 4, 7: 3, 8: 3, 9: 2, 11: 1}
NNLS = [("wide", 0.1738, 0.0962, 0.2546), ("legbyes", 1.3314, 1.1699, 1.4988), ("byes", 2.1389, 1.7754, 2.5231),
        ("Overstep", 0.0, 0.0, 0.3958), ("other", 0.2912, 0.0, 0.8121)]


def read(p: Path, what: str):
    if not Path(p).exists():
        SKIPPED.append(f"{what} ({p})")
        print("SKIP missing", what, p)
        return None
    return pd.read_parquet(p) if str(p).endswith(".parquet") else pd.read_csv(p, comment="#")


def save(fig, path: Path):
    if not fig.get_constrained_layout():
        fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", path.name)


def players(src: Path, role: str) -> pd.DataFrame | None:
    for nm in (f"{role}.csv", f"{role}_primary.csv"):
        d = read(src / nm, nm)
        if d is not None:
            d = d.sort_values("rating_runs_per_100_balls", ascending=False).reset_index(drop=True)
            d["rank"] = np.arange(1, len(d) + 1)
            return d
    return None


def fig_high_low(hl, out):
    order = ["LOW", "MEDIUM", "HIGH"]
    hl = hl.set_index("set").loc[order]
    cols = [SLATE, MID, PINK]
    fig, ax = plt.subplots(1, 4, figsize=(13, 3.6))
    panels = [("Win-probability swing per ball", ["mean_expected_LI", "mean_abs_dWP"], ["Expected (before the ball)", "Realised (after the ball)"], None),
              ("Share of balls where match is undecided", ["undecided_share"], None, "{:.0%}"),
              ("Wicket probability per ball", ["wicket_rate"], None, "{:.1%}"),
              ("Dot-ball share", ["dot_pct"], None, "{:.0%}")]
    for a, (title, cs, leg, fmt) in zip(ax, panels):
        x = np.arange(3)
        if len(cs) == 2:
            w = 0.38
            a.bar(x - w / 2, hl[cs[0]], w, color=cols, alpha=0.55, label=leg[0], hatch="//", edgecolor="white")
            a.bar(x + w / 2, hl[cs[1]], w, color=cols, label=leg[1])
            a.legend(frameon=False, fontsize=8, loc="upper left")
        else:
            b = a.bar(x, hl[cs[0]], 0.6, color=cols)
            for r, v in zip(b, hl[cs[0]]):
                a.text(r.get_x() + r.get_width() / 2, v, fmt.format(v), ha="center", va="bottom", fontsize=9)
        a.set_xticks(x, order)
        a.set_title(title, fontsize=10, loc="left")
        a.grid(axis="x", visible=False)
    save(fig, out / "F02_high_vs_low.png")


def fig_pi_heat(pb, out):
    d = pb.copy()
    ov = "over" if "over" in d.columns else "overid"
    d["w"] = d["w_before"].clip(0, 9).astype(int)
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.3), sharey=True, constrained_layout=True)
    for a, inn in zip(ax, (1, 2)):
        g = d[d.innings == inn].groupby(["w", ov])["PI"].mean().unstack()
        g = g.reindex(index=range(10), columns=range(1, 21))
        im = a.imshow(g.values, origin="lower", aspect="auto", cmap="RdPu", vmin=0.2, vmax=0.95, extent=[0.5, 20.5, -0.5, 9.5])
        a.set_title(f"Innings {inn}: average Pressure Index", loc="left", fontsize=11)
        a.set_xlabel("Over")
        a.grid(False)
        a.set_xticks(range(1, 21, 2))
    ax[0].set_ylabel("Wickets lost")
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cb.set_label("Pressure Index (0-1)")
    save(fig, out / "F03_pi_heatmap.png")


def fig_share(pb, out):
    ov = "over" if "over" in pb.columns else "overid"
    fig, a = plt.subplots(figsize=(8.5, 3.8))
    for inn, c in ((1, SLATE), (2, PINK)):
        s = (pb[pb.innings == inn].assign(h=lambda x: (x["set"] == "HIGH")).groupby(ov)["h"].mean().reindex(range(1, 21)))
        a.plot(s.index, s.values * 100, color=c, lw=2.5, marker="o", ms=4, label=f"Innings {inn}")
    a.set_xlabel("Over")
    a.set_ylabel("% of balls classed HIGH pressure")
    a.set_xticks(range(1, 21, 2))
    a.legend(frameon=False)
    save(fig, out / "F04_high_share_by_over.png")


def fig_calibration(pb, wp, out):
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
    for a, inn in zip(ax, (1, 2)):
        d = pb[pb.innings == inn]
        bins = np.clip((d["wp_before"] * 10).astype(int), 0, 9)
        g = d.groupby(bins).agg(p=("wp_before", "mean"), o=("batting_won", "mean"), n=("wp_before", "size"))
        a.plot([0, 1], [0, 1], color=MID, ls="--", lw=1.5, label="Perfect calibration")
        a.plot(g.p, g.o, color=PINK, marker="o", lw=2.5, label="Model (out-of-fold)")
        a.set_title(f"Innings {inn}", loc="left")
        a.set_xlabel("Predicted win probability")
        txt = ""
        if wp is not None:
            r = wp[(wp.innings == inn) & (wp.group == "all")]
            if len(r):
                r = r.iloc[0]
                txt = f"AUC {r.auc:.2f}   log-loss {r.log_loss:.3f} (baseline {r.base_logloss:.3f})   ECE {r.ece:.3f}"
        a.text(0.02, 0.95, txt, transform=a.transAxes, fontsize=9, va="top")
        a.legend(frameon=False, loc="lower right", fontsize=9)
    ax[0].set_ylabel("Observed win rate")
    save(fig, out / "F05_wp_calibration.png")


def fig_traces(pb, out, k=2):
    ov = "over" if "over" in pb.columns else "overid"
    d2 = pb[pb.innings == 2].sort_values(["match_id", "innings_ball_num"])
    sc = d2.groupby("match_id").agg(sw=("dWP", lambda x: x.abs().sum()), n=("PI", "size"))
    for i, mid in enumerate(sc[sc.n >= 60].sort_values("sw", ascending=False).index[:k], 1):
        m = d2[d2.match_id == mid].reset_index(drop=True)
        fig, a = plt.subplots(figsize=(10, 3.9))
        x = np.arange(len(m))
        a.plot(x, m.wp_before, color=NAVY, lw=2)
        hi = (m["set"] == "HIGH").to_numpy()
        start = None
        for j, h in enumerate(hi):
            if h and start is None:
                start = j
            if (not h or j == len(hi) - 1) and start is not None:
                a.axvspan(start - 0.5, j - 0.5, color=PINK, alpha=0.18, lw=0)
                start = None
        w = m.wicket.to_numpy() == 1
        a.scatter(x[w], m.wp_before[w], color=PINK, s=40, zorder=3, label="Wicket")
        a.axhline(0.5, color=MID, ls="--", lw=1)
        a.set_ylim(0, 1)
        a.set_xlabel("Ball of the chase")
        a.set_ylabel("Chasing side win probability")
        a.set_title(f"Match {int(mid)}: pink bands are HIGH-pressure balls", loc="left", fontsize=11)
        a.legend(frameon=False, loc="upper left")
        save(fig, out / f"F06_match_trace_{i}.png")


def fig_tournament(t, out):
    t = t.copy()
    t["label"] = t["estimator"].str.replace("_", " ", regex=False)
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.3))
    for a, role in zip(ax, ("batter", "bowler")):
        d = t[t.role == role].sort_values("mean_pearson")
        y = np.arange(len(d))
        best = d.mean_pearson.idxmax()
        a.barh(y, d.mean_pearson, color=[PINK if i == best else MID for i in d.index], height=0.6)
        a.errorbar(d.mean_pearson, y, xerr=[d.mean_pearson - d.p05, d.p95 - d.mean_pearson], fmt="none", ecolor=NAVY, lw=1.2, capsize=3)
        ceil = np.sqrt(d.noise_ceiling_relB.iloc[0])
        a.axvline(ceil, color=TEAL, ls="--", lw=2)
        a.text(ceil - 0.005, -0.55, f"noise ceiling {ceil:.2f} ", color=TEAL, fontsize=9, va="bottom", ha="right")
        a.set_yticks(y, d.label)
        a.set_xlim(0, max(ceil, d.p95.max()) * 1.12)
        a.set_ylim(-0.7, len(d) - 0.4)
        a.set_title(f"{role.capitalize()}s", fontsize=12, loc="left", fontweight="bold")
        a.set_xlabel("Held-out correlation with next-half HIGH-pressure value per ball\n(bar = mean of the splits; whisker = 5th to 95th percentile)")
        a.grid(axis="y", visible=False)
    save(fig, out / "F07_tournament.png")


def fig_forest(d, role, out, name, top=25):
    d = d.head(top).iloc[::-1]
    fig, a = plt.subplots(figsize=(9.5, 8.2))
    y = np.arange(len(d))
    col = [PINK if r <= 10 else SLATE for r in d["rank"]]
    a.hlines(y, d.lo80_runs_per_100_balls, d.hi80_runs_per_100_balls, color=col, lw=2.2, alpha=0.8)
    a.scatter(d.rating_runs_per_100_balls, y, color=col, s=46, zorder=3)
    a.set_yticks(y, [f"{int(r)}. {n}" for r, n in zip(d["rank"], d.display_name)])
    if "P_top10" in d:
        xr = a.get_xlim()[1]
        for yi, p in zip(y, d["P_top10"]):
            a.text(xr, yi, f"  {p:.0%}", va="center", fontsize=9, color=NAVY)
        a.text(xr, len(d) - 0.2, "  P(top 10)", fontsize=9, color=NAVY, fontweight="bold", va="bottom")
    a.axvline(0, color=MID, lw=1)
    a.set_xlabel("Runs above expectation per 100 balls in HIGH-pressure situations (dot = estimate, line = 80% interval)")
    a.grid(axis="y", visible=False)
    save(fig, out / name)


def fig_beta_delta(bat, bow, out):
    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    for a, d, t in zip(ax, (bat, bow), ("Batters", "Bowlers")):
        d = d.head(20)
        yerr_lo = np.maximum(0, d.delta_pressure_runs_per_100_balls - d.delta_lo80_runs_per_100_balls)
        yerr_hi = np.maximum(0, d.delta_hi80_runs_per_100_balls - d.delta_pressure_runs_per_100_balls)
        a.errorbar(d.beta_general_runs_per_100_balls, d.delta_pressure_runs_per_100_balls,
                   yerr=[yerr_lo, yerr_hi],
                   fmt="o", color=PINK, ecolor=MID, capsize=2)
        for r in d.head(8).itertuples():
            a.annotate(r.display_name.split()[-1], (r.beta_general_runs_per_100_balls, r.delta_pressure_runs_per_100_balls), fontsize=8, xytext=(4, 4), textcoords="offset points")
        a.axhline(0, color=NAVY, lw=1)
        a.set_title(f"{t}: usual level vs pressure shift (top 20)", loc="left", fontsize=11)
        a.set_xlabel("Usual level (runs above expectation per 100 balls)")
    ax[0].set_ylabel("Pressure shift (runs per 100 balls, 80% interval)")
    save(fig, out / "F10_beta_vs_delta.png")


def fig_ptop(bat, bow, out):
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8), sharey=False)
    for a, d, t in zip(ax, (bat, bow), ("Batters", "Bowlers")):
        d = d.head(15).iloc[::-1]
        a.barh(d.display_name, d.P_top10 * 100, color=[PINK if r <= 10 else MID for r in d["rank"]])
        a.set_title(f"{t}: probability of finishing in the top 10", loc="left", fontsize=11)
        a.set_xlabel("% of 300 match-level bootstrap resamples")
        a.grid(axis="y", visible=False)
    save(fig, out / "F11_p_top10.png")


def fig_sens(s, out):
    s = s[(s.kendall_tau.notna()) & (s.kendall_tau < 0.9999)].copy()
    s["run"] = s["run"].str.replace("_", " ", regex=False)
    fig, a = plt.subplots(figsize=(9, 5))
    runs = list(dict.fromkeys(s.run))
    y = np.arange(len(runs))
    for off, role, c in ((-0.18, "batter", PINK), (0.18, "bowler", NAVY)):
        v = s[s.role == role].set_index("run").reindex(runs).kendall_tau
        a.barh(y + off, v, height=0.34, color=c, label=role.capitalize() + "s")
    a.set_yticks(y, runs)
    a.set_xlim(0.7, 1.0)
    a.set_xlabel("Kendall tau vs default ranking (1.0 = identical order)")
    a.legend(frameon=False, loc="lower left")
    a.grid(axis="y", visible=False)
    save(fig, out / "F12_sensitivity.png")


def fig_extras(out):
    fig, ax = plt.subplots(1, 2, figsize=(12, 4), gridspec_kw={"width_ratios": [1.4, 1]})
    ks = sorted(RESIDUAL_HIST)
    ax[0].bar(ks, [RESIDUAL_HIST[k] for k in ks], color=[PINK if k == 0 else MID for k in ks])
    ax[0].set_xlabel("Reported margin minus reconstructed margin (runs)")
    ax[0].set_ylabel("Matches")
    ax[0].set_title("358 'won by N runs' matches after reconstruction", loc="left", fontsize=10)
    names = [n for n, *_ in NNLS]
    co = [c for _, c, *_ in NNLS]
    lo = [c - l for _, c, l, _ in NNLS]
    hi = [h - c for _, c, _, h in NNLS]
    ax[1].barh(names[::-1], co[::-1], xerr=[lo[::-1], hi[::-1]], color=NAVY, capsize=3)
    ax[1].set_xlabel("Estimated extra runs per delivery (95% CI)")
    ax[1].set_title("What the dataset does not record", loc="left", fontsize=10)
    ax[1].grid(axis="y", visible=False)
    save(fig, out / "F13_extras_reconstruction.png")


def fig_funnel(ex, out):
    ex = ex.copy()
    fig, a = plt.subplots(figsize=(9, 4.2))
    y = np.arange(len(ex))[::-1]
    c = [PINK if "usable" in str(r).lower() else SLATE for r in ex.iloc[:, 0]]
    a.barh(y, ex.iloc[:, 1], color=c)
    for yi, v in zip(y, ex.iloc[:, 1]):
        a.text(v, yi, f"  {int(v)}", va="center")
    a.set_yticks(y, ex.iloc[:, 0])
    a.set_xlabel("Matches")
    a.grid(axis="y", visible=False)
    save(fig, out / "F14_data_funnel.png")


def fig_profiles(d, prof, role, out, name):
    if prof is None:
        return
    q = prof[prof["role"] == role] if "role" in prof.columns else prof
    cols = {c.lower(): c for c in q.columns}
    h = next((cols[c] for c in ("run_rate_high", "high_metric") if c in cols), None)
    l = next((cols[c] for c in ("run_rate_low", "low_metric") if c in cols), None)
    if not h or not l:
        SKIPPED.append("profile metric columns")
        return
    top = d.head(10)[["player_id", "display_name"]].merge(q[["player_id", h, l]], on="player_id").iloc[::-1]
    fig, a = plt.subplots(figsize=(8.5, 4.8))
    y = np.arange(len(top))
    a.hlines(y, top[l], top[h], color=MID, lw=3)
    a.scatter(top[l], y, color=SLATE, s=70, label="Ordinary situations (LOW)", zorder=3)
    a.scatter(top[h], y, color=PINK, s=70, label="High pressure (HIGH)", zorder=3)
    a.set_yticks(y, top.display_name)
    a.set_xlabel("Runs per over scored (batters) / conceded (bowlers)")
    a.legend(frameon=False, loc="lower right")
    a.grid(axis="y", visible=False)
    save(fig, out / name)


def top10_table(d, role):
    t = d.head(10)
    return pd.DataFrame({"Rank": t["rank"], "Player": t.display_name, "Teams": t.teams,
                         "Rating (runs/100 balls)": t.rating_runs_per_100_balls.round(1),
                         "80% interval": t.lo80_runs_per_100_balls.round(0).astype(int).astype(str) + " to " + t.hi80_runs_per_100_balls.round(0).astype(int).astype(str),
                         "P(top 10)": (t.P_top10 * 100).round(0).astype(int).astype(str) + "%",
                         "HIGH balls (IPL / T20I)": t.n_HIGH_balls.astype(int).astype(str) + " (" + t.n_IPL_HIGH_balls.astype(int).astype(str) + " / " + t.n_T20I_HIGH_balls.astype(int).astype(str) + ")",
                         "Last match": t.last_match_date})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="outputs/final")
    ap.add_argument("--out", default="report_assets")
    a = ap.parse_args()
    src, out = Path(a.src), Path(a.out)
    (out / "figures").mkdir(parents=True, exist_ok=True)
    (out / "tables").mkdir(exist_ok=True)
    fg = out / "figures"

    bat, bow = players(src, "batters"), players(src, "bowlers")
    prof, hl = read(src / "profiles.csv", "profiles"), read(src / "high_low.csv", "high_low")
    tour, sens = read(src / "tournament_summary.csv", "tournament_summary"), read(src / "sensitivity.csv", "sensitivity")
    wp, ex = read(src / "wp_report.csv", "wp_report"), read(src / "exclusions.csv", "exclusions")
    pb = read(src / "pressure_balls.parquet", "pressure_balls.parquet")

    if hl is not None:
        fig_high_low(hl, fg)
    if pb is not None:
        fig_pi_heat(pb, fg)
        fig_share(pb, fg)
        fig_calibration(pb, wp, fg)
        fig_traces(pb, fg)
    if tour is not None:
        fig_tournament(tour, fg)
    if bat is not None:
        fig_forest(bat, "batter", fg, "F08_forest_batters.png")
    if bow is not None:
        fig_forest(bow, "bowler", fg, "F09_forest_bowlers.png")
    if bat is not None and bow is not None:
        fig_beta_delta(bat, bow, fg)
        fig_ptop(bat, bow, fg)
        fig_profiles(bat, prof, "batter", fg, "F16a_high_vs_low_batters.png")
        fig_profiles(bow, prof, "bowler", fg, "F16b_high_vs_low_bowlers.png")
    if sens is not None:
        fig_sens(sens, fg)
    fig_extras(fg)
    if ex is not None:
        fig_funnel(ex, fg)

    facts: dict = {"skipped": SKIPPED, "ranking_rules": "Pakistan and Pakistan A excluded; Bangladesh included; active within 365 days"}
    for role, d in (("batters", bat), ("bowlers", bow)):
        if d is None:
            continue
        top10_table(d, role).to_csv(out / "tables" / f"T0{1 if role == 'batters' else 2}_top10_{role}.csv", index=False)
        facts[f"top10_{role}"] = [dict(rank=int(r["rank"]), name=r.display_name, rating=round(r.rating_runs_per_100_balls, 1), lo80=round(r.lo80_runs_per_100_balls, 1),
                                       hi80=round(r.hi80_runs_per_100_balls, 1), p_top10=round(float(r.P_top10), 3), n_high=int(r.n_HIGH_balls), teams=r.teams)
                                  for _, r in d.head(10).iterrows()]
        facts[f"expected_overlap_{role}"] = round(float(d.head(10).P_top10.sum()), 2)
        facts[f"eligible_{role}"] = int(len(d))
    if tour is not None:
        tour.to_csv(out / "tables" / "T03_tournament.csv", index=False)
        for role in ("batter", "bowler"):
            r = tour[tour.role == role].sort_values("mean_pearson", ascending=False)
            facts[f"tournament_best_{role}"] = dict(estimator=r.iloc[0].estimator, mean_pearson=round(r.iloc[0].mean_pearson, 3),
                                                    runner_up=r.iloc[1].estimator, runner_up_pearson=round(r.iloc[1].mean_pearson, 3),
                                                    noise_ceiling_corr=round(float(np.sqrt(r.iloc[0].noise_ceiling_relB)), 3))
    if sens is not None:
        s = sens[(sens.kendall_tau.notna()) & (sens.kendall_tau < 0.9999)]
        sens.to_csv(out / "tables" / "T04_sensitivity.csv", index=False)
        facts["kendall_tau_min"], facts["kendall_tau_max"] = round(float(s.kendall_tau.min()), 3), round(float(s.kendall_tau.max()), 3)
    if hl is not None:
        facts["high_low"] = hl.round(4).to_dict("records")
    if wp is not None:
        facts["wp_report"] = wp.round(4).to_dict("records")
    if pb is not None:
        facts["usable_matches"], facts["usable_balls"] = int(pb.match_id.nunique()), int(len(pb))
        if "comp_group" in pb:
            facts["matches_by_group"] = pb.groupby("comp_group").match_id.nunique().to_dict()
    json.dump(facts, open(out / "facts.json", "w"), indent=1, default=str)
    print(f"done. figures: {len(list(fg.glob('*.png')))}, skipped inputs: {len(SKIPPED)}")


if __name__ == "__main__":
    main()
