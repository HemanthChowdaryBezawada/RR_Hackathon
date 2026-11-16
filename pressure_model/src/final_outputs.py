"""Reporting-only finalization for the pressure_core pipeline."""

from pathlib import Path
import shutil
import sys

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
from pressure_model.src.run_all import C, CONFIG, TABLES, run
import pressure_core as pc

FINAL = ROOT / "outputs" / "final"
ROOT_FINAL = ROOT.parent / "outputs" / "final"
FIGURES = ROOT / "outputs" / "figures"
FINAL.mkdir(parents=True, exist_ok=True)
ROOT_FINAL.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)


def md(frame: pd.DataFrame) -> str:
    """Render a computed table to Markdown."""
    columns = [str(column) for column in frame.columns]
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    lines.extend("| " + " | ".join(str(value) for value in row) + " |" for row in frame.itertuples(index=False, name=None))
    return "\n".join(lines)


def bootstrap_general_pressure(default, role: str, player_ids: np.ndarray) -> pd.DataFrame:
    """Refit the existing ridge specification on each match bootstrap for beta and delta intervals."""
    rd = default["rd"]
    rho = float(default["best"].rho)
    alpha = float(default["best"].alpha_g)
    unique_matches, inverse = np.unique(rd.mid, return_inverse=True)

    def one(rep: int) -> tuple[np.ndarray, np.ndarray]:
        rng = np.random.default_rng(pc.SEED + rep)
        counts = np.bincount(rng.integers(0, len(unique_matches), len(unique_matches)), minlength=len(unique_matches))
        fit = pc.fit_ridge(rd, rho, alpha, weights=rd.w * counts[inverse])
        return (fit["bat_gen"], fit["delta"]) if role == "batter" else (fit["bow_gen"], -fit["eta"])

    values = Parallel(n_jobs=CONFIG.get("n_jobs", 6))(delayed(one)(rep) for rep in range(300))
    general = np.vstack([value[0] for value in values])
    shift = np.vstack([value[1] for value in values])
    return pd.DataFrame({
        "player_id": player_ids,
        "beta_lo80": np.quantile(general, 0.1, axis=0),
        "beta_hi80": np.quantile(general, 0.9, axis=0),
        "delta_lo80": np.quantile(shift, 0.1, axis=0),
        "delta_hi80": np.quantile(shift, 0.9, axis=0),
    })


def bootstrap_eb(default, role: str, player_ids: np.ndarray, reps: int = 300) -> np.ndarray:
    """Match-level bootstrap for empirical Bayes general shrunk ratings (E3_EB_general)."""
    d = default["rd"].df
    player_col = "striker_id" if role == "batter" else "bowler_id"
    sign = 1.0 if role == "batter" else -1.0
    all_balls = d[d[player_col].notna()].copy()
    matches = np.unique(all_balls["match_id"])
    m_series = all_balls["match_id"]
    val_series = sign * all_balls["y"]
    sigma2 = float(np.var(val_series, ddof=1))

    def one(rep: int) -> np.ndarray:
        rng = np.random.default_rng(pc.SEED + rep)
        sampled = rng.integers(0, len(matches), len(matches))
        counts = np.bincount(sampled, minlength=len(matches))
        weights = m_series.map(pd.Series(counts, index=matches)).fillna(0).to_numpy()
        w_mask = weights > 0
        means = pd.Series(0.0, index=player_ids)
        ns = pd.Series(0.0, index=player_ids)
        if np.any(w_mask):
            w_sub = weights[w_mask]
            v_sub = val_series.to_numpy()[w_mask]
            p_sub = all_balls[player_col].to_numpy()[w_mask]
            df_sub = pd.DataFrame({"p": p_sub, "wy": w_sub * v_sub, "w": w_sub})
            agg = df_sub.groupby("p").sum()
            c_idx = agg.index.intersection(player_ids)
            means.loc[c_idx] = agg.loc[c_idx, "wy"] / agg.loc[c_idx, "w"]
            ns.loc[c_idx] = agg.loc[c_idx, "w"]

        return pc.eb_shrink(means.to_numpy(), ns.to_numpy(), sigma2)["post"]

    return np.vstack(Parallel(n_jobs=CONFIG.get("n_jobs", 6))(delayed(one)(rep) for rep in range(reps)))


def eb_point(default, role: str, player_ids: np.ndarray) -> np.ndarray:
    """Empirical Bayes point estimate across ALL deliveries (E3_EB_general)."""
    d = default["rd"].df
    player_col = "striker_id" if role == "batter" else "bowler_id"
    sign = 1.0 if role == "batter" else -1.0
    all_balls = d[d[player_col].notna()]
    grouped = all_balls.assign(_value=sign * all_balls["y"]).groupby(player_col)["_value"].agg(["mean", "count"])
    means = pd.Series(0.0, index=player_ids)
    ns = pd.Series(0.0, index=player_ids)
    common_idx = grouped.index.intersection(player_ids)
    means.loc[common_idx] = grouped.loc[common_idx, "mean"]
    ns.loc[common_idx] = grouped.loc[common_idx, "count"]
    sigma2 = float(np.var(sign * all_balls["y"], ddof=1))
    return pc.eb_shrink(means.to_numpy(), ns.to_numpy(), sigma2)["post"]


def get_overall_last_dates(d: pd.DataFrame) -> pd.Series:
    """Compute the last match date across ANY delivery (batting or bowling) in the usable data."""
    bat_last = d.groupby("striker_id")["match_date"].max()
    bow_last = d.groupby("bowler_id")["match_date"].max()
    all_pids = set(bat_last.index) | set(bow_last.index)
    overall_last = {}
    for p in all_pids:
        dt1 = bat_last.get(p)
        dt2 = bow_last.get(p)
        if dt1 is not None and dt2 is not None:
            overall_last[p] = max(dt1, dt2)
        elif dt1 is not None:
            overall_last[p] = dt1
        else:
            overall_last[p] = dt2
    return pd.Series(overall_last)


def make_ranking(default, role: str, excluded: set[int], boot: np.ndarray, threshold: int,
                 beta_delta: pd.DataFrame, point: np.ndarray, ridge_point: np.ndarray,
                 estimator: str, overall_last_s: pd.Series, active_only: bool = True) -> pd.DataFrame:
    """Build the complete requested ranking table from fitted core objects."""
    d, rd = default["d"], default["rd"]
    player_col = "striker_id" if role == "batter" else "bowler_id"
    ids = rd.bat_ids if role == "batter" else rd.bow_ids
    counts = d[d["set"].eq("HIGH") & d[player_col].notna()].groupby(player_col).size()
    eligible = counts[(counts >= threshold) & ~counts.index.astype(int).isin(excluded)].index
    summary = pc.summarize_boot(point, boot, pd.Series(ids).isin(eligible).to_numpy())
    summary["player_id"] = ids
    summary = summary[summary["player_id"].isin(eligible)].sort_values("rating", ascending=False)
    mapping = default["mapping"]
    names = mapping[[C["player_id"], C["player_name"]]].drop_duplicates(C["player_id"]).rename(
        columns={C["player_id"]: "player_id", C["player_name"]: "display_name"}
    )
    teams = mapping.groupby(C["player_id"])[C["team_name"]].agg(lambda values: ", ".join(sorted(set(map(str, values))))).rename("teams")
    meta = d[d["set"].eq("HIGH")].groupby(player_col).agg(
        n_HIGH_balls=("runs_total", "size"), mean_w_opp=("w_opp", "mean")
    ).rename_axis("player_id").reset_index()

    total_balls = d[d[player_col].notna()].groupby(player_col).size().rename("n_balls_total").reset_index().rename(columns={player_col: "player_id"})

    by_comp = d[d["set"].eq("HIGH")].pivot_table(index=player_col, columns="comp_group", values="runs_total", aggfunc="size", fill_value=0)
    by_comp = by_comp.rename(columns={"IPL": "n_IPL_HIGH_balls", "T20I": "n_T20I_HIGH_balls"}).reset_index().rename(columns={player_col: "player_id"})
    units = pc.consistency_units(d, player_col, 1 if role == "batter" else -1, 4 if role == "batter" else 6)
    units = units.reset_index()[[player_col, "p_pos", "disaster_rate"]].rename(columns={player_col: "player_id"})
    result = summary.merge(names, on="player_id", how="left").merge(teams, on="player_id", how="left").merge(meta, on="player_id", how="left").merge(total_balls, on="player_id", how="left").merge(by_comp, on="player_id", how="left").merge(units, on="player_id", how="left")
    result = result.fillna({"n_IPL_HIGH_balls": 0, "n_T20I_HIGH_balls": 0, "p_pos": 0, "disaster_rate": 0, "n_balls_total": 0})
    result["n_balls_total"] = result["n_balls_total"].astype(int)
    result["rating_runs_per_100_balls"] = result["rating"] * 100
    result["WPA_points_per_100_balls"] = result["rating"] * default["K"]["all"]["kappa_run"] * 100
    general = pd.Series(
        default["fitted"]["bat_gen"] if role == "batter" else default["fitted"]["bow_gen"], index=ids
    )
    result["beta_general_runs_per_100_balls"] = general.reindex(result["player_id"]).to_numpy() * 100
    result["estimator"] = estimator

    # Ridge cross-check columns
    if role == "batter":
        result["rating_ridge"] = pd.Series(ridge_point, index=ids).reindex(result["player_id"]).to_numpy() * 100
        result["beta_ridge"] = result["beta_general_runs_per_100_balls"]
        result["delta_ridge"] = result["rating_ridge"] - result["beta_ridge"]
    else:
        result["rating_ridge"] = result["rating_runs_per_100_balls"]
        result["beta_ridge"] = result["beta_general_runs_per_100_balls"]
        result["delta_ridge"] = result["rating_ridge"] - result["beta_ridge"]

    result["delta_pressure_runs_per_100_balls"] = result["delta_ridge"]
    result = result.merge(beta_delta, on="player_id", how="left")
    latest = pd.to_datetime(d["match_date"]).max()

    # Unified last match date across ANY delivery (batting or bowling)
    result["last_match_date"] = pd.to_datetime(result["player_id"].map(overall_last_s))
    result["days_since_last_match"] = (latest - result["last_match_date"]).dt.days
    result["active_365"] = result["days_since_last_match"] <= 365
    result["lo80_runs_per_100_balls"] = np.minimum(result["lo80"] * 100, result["rating_runs_per_100_balls"])
    result["hi80_runs_per_100_balls"] = np.maximum(result["hi80"] * 100, result["rating_runs_per_100_balls"])
    result["beta_lo80_runs_per_100_balls"] = result["beta_lo80"] * 100
    result["beta_hi80_runs_per_100_balls"] = result["beta_hi80"] * 100
    result["delta_lo80_runs_per_100_balls"] = result["delta_lo80"] * 100
    result["delta_hi80_runs_per_100_balls"] = result["delta_hi80"] * 100
    if active_only:
        result = result[result["active_365"]]
    result.insert(0, "rank", range(1, len(result) + 1))
    if role == "batter":
        result["rank_ridge"] = result["rating_ridge"].rank(ascending=False, method="min").astype(int)
    else:
        result["rank_ridge"] = result["rank"]

    # Compare with high-only dates to print players whose date changed by > 7 days
    high_last = d[d["set"].eq("HIGH")].groupby(player_col)["match_date"].max()
    old_dates = high_last.reindex(result["player_id"]).values
    diff_days = (pd.to_datetime(result["last_match_date"].values) - pd.to_datetime(old_dates)).days
    changed_mask = np.abs(np.nan_to_num(diff_days, nan=0.0)) > 7
    if np.any(changed_mask):
        changed = result[changed_mask].copy()
        print(f"\n[{role.upper()}] Players whose last_match_date changed by > 7 days ({len(changed)}):")
        for idx, row in changed.iterrows():
            pos = result.index.get_loc(idx)
            old_str = str(old_dates[pos])[:10]
            new_str = str(row["last_match_date"])[:10]
            df_val = int(diff_days[pos])
            print(f"  {row['display_name']} (ID {row['player_id']}): was {old_str}, now {new_str} (diff +{df_val} days)")

    return result[[
        "rank", "player_id", "display_name", "teams", "rating_runs_per_100_balls", "WPA_points_per_100_balls",
        "beta_general_runs_per_100_balls", "delta_pressure_runs_per_100_balls", "boot_sd", "lo80_runs_per_100_balls",
        "hi80_runs_per_100_balls", "P_top10", "n_HIGH_balls", "n_balls_total", "n_IPL_HIGH_balls", "n_T20I_HIGH_balls",
        "last_match_date", "days_since_last_match", "active_365", "mean_w_opp", "p_pos", "disaster_rate",
        "beta_lo80_runs_per_100_balls", "beta_hi80_runs_per_100_balls", "delta_lo80_runs_per_100_balls", "delta_hi80_runs_per_100_balls",
        "estimator", "rating_ridge", "rank_ridge", "beta_ridge", "delta_ridge"
    ]]


def rank_variant(trial, role: str, estimator: str = None, excluded: set[int] = None, rho_inf: bool = False, ipl_only: bool = False, overall_last_s: pd.Series = None) -> pd.DataFrame:
    """Standardized ranking function applied uniformly across all variants in the sensitivity analysis."""
    d = trial["d"]
    rd = trial["rd"]
    player_col = "striker_id" if role == "batter" else "bowler_id"
    threshold = 150 if role == "batter" else 120
    ids = rd.bat_ids if role == "batter" else rd.bow_ids

    if excluded is None:
        mapping = trial["mapping"]
        excluded = set(mapping.loc[mapping[C["team_name"]].isin(["Pakistan", "Pakistan A"]), C["player_id"]].dropna().astype(int))

    if ipl_only:
        h_mask = d["set"].eq("HIGH") & (d["comp_group"] == "IPL") & d[player_col].notna()
    else:
        h_mask = d["set"].eq("HIGH") & d[player_col].notna()

    counts = d[h_mask].groupby(player_col).size()
    eff_threshold = threshold if not ipl_only else 50
    eligible = counts[(counts >= eff_threshold) & ~counts.index.astype(int).isin(excluded)].index

    if estimator is None:
        estimator = "E3_EB_general" if role == "batter" else "E5_ridge_rho3"

    if estimator == "E3_EB_general":
        sign = 1.0 if role == "batter" else -1.0
        all_balls = d[d[player_col].notna()]
        if ipl_only:
            all_balls = all_balls[all_balls["comp_group"] == "IPL"]
        grouped = all_balls.assign(_value=sign * all_balls["y"]).groupby(player_col)["_value"].agg(["mean", "count"])
        means = pd.Series(0.0, index=ids)
        ns = pd.Series(0.0, index=ids)
        c_idx = grouped.index.intersection(ids)
        means.loc[c_idx] = grouped.loc[c_idx, "mean"]
        ns.loc[c_idx] = grouped.loc[c_idx, "count"]
        sigma2 = float(np.var(sign * all_balls["y"], ddof=1))
        scores = pd.Series(pc.eb_shrink(means.to_numpy(), ns.to_numpy(), sigma2)["post"], index=ids)
    elif estimator == "E5_ridge_rho3":
        if rho_inf:
            fit = pc.fit_ridge(rd, np.inf, float(trial["best"].alpha_g))
            pt = fit["bat_high"] if role == "batter" else fit["bow_high"]
        else:
            pt = trial["fitted"]["bat_high"] if role == "batter" else trial["fitted"]["bow_high"]
        scores = pd.Series(pt, index=ids)
    else:
        raise ValueError(f"Unknown estimator: {estimator}")

    latest = pd.to_datetime(d["match_date"]).max()
    if overall_last_s is not None:
        last_dates = overall_last_s.reindex(eligible)
    else:
        last_dates = d.groupby(player_col)["match_date"].max().reindex(eligible)
    days_since = (latest - pd.to_datetime(last_dates)).dt.days
    active = days_since[days_since <= 365].index

    valid_ids = [p for p in eligible if p in active and p in scores.index]
    ranked = pd.DataFrame({
        "player_id": valid_ids,
        "score": scores.loc[valid_ids].values
    }).sort_values("score", ascending=False).reset_index(drop=True)
    return ranked


def main() -> None:
    """Generate final frozen tables and figures with exact Patch 8 specifications."""
    default = run(CONFIG.get("runs_reconstruction_mode", "fractional_expected"), 0.75, 730)
    print("high_offset_runs_per_ball", default["fitted"].get("high_offset"))
    mapping = default["mapping"]
    names = mapping[[C["player_id"], C["player_name"]]].drop_duplicates(C["player_id"]).rename(
        columns={C["player_id"]: "player_id", C["player_name"]: "display_name"}
    )
    primary = set(mapping.loc[mapping[C["team_name"]].isin(["Pakistan", "Pakistan A"]), C["player_id"]].dropna().astype(int))
    alternate = primary | set(mapping.loc[mapping[C["team_name"]].isin(["Bangladesh", "Bangladesh A"]), C["player_id"]].dropna().astype(int))

    tournament = default["tournament"]
    raw_tournament = default["raw_tournament"]

    # 1. Paired difference in held-out Pearson between E3_EB_general and E5_ridge_rho3
    paired = raw_tournament[raw_tournament["estimator"].isin(["E3_EB_general", "E5_ridge_rho3"])].pivot_table(
        index=["role", "split"], columns="estimator", values="pearson"
    ).reset_index()
    paired["difference_E3_minus_E5"] = paired["E3_EB_general"] - paired["E5_ridge_rho3"]
    paired_differences = paired.groupby("role")["difference_E3_minus_E5"].agg(
        mean="mean", sd="std", n_splits="count"
    ).reset_index()
    paired_differences["se"] = paired_differences["sd"] / np.sqrt(paired_differences["n_splits"])
    paired_differences.to_csv(FINAL / "paired_differences.csv", index=False)
    paired_differences.to_csv(ROOT_FINAL / "paired_differences.csv", index=False)
    print("\n--- PAIRED DIFFERENCES (E3_EB_general minus E5_ridge_rho3) ---")
    print(paired_differences.to_string(index=False))

    # 2. Final estimator per role selection decision
    means = tournament.pivot(index="role", columns="estimator", values="mean_pearson")
    decisions = {}
    print("\n--- ESTIMATOR SELECTION DECISION ---")
    for role in ("batter", "bowler"):
        eb_mean = float(means.loc[role, "E3_EB_general"])
        ridge_mean = float(means.loc[role, "E5_ridge_rho3"])
        if eb_mean > ridge_mean and (eb_mean - ridge_mean) > 0.01:
            decisions[role] = "E3_EB_general"
            print(f"{role.capitalize()}: E3_EB_general selected (mean Pearson = {eb_mean:.6f} vs ridge {ridge_mean:.6f}; advantage = +{eb_mean - ridge_mean:.6f} > 0.01).")
        else:
            decisions[role] = "E5_ridge_rho3"
            reason = "ridge is higher" if ridge_mean >= eb_mean else "EB is within 0.01 and ridge adjusts for opposition"
            print(f"{role.capitalize()}: E5_ridge_rho3 selected (mean Pearson = {ridge_mean:.6f} vs EB {eb_mean:.6f}; {reason}).")

    # 3. Bootstrap & rating computation per role
    overall_last_s = get_overall_last_dates(default["d"])

    bat_ids = default["rd"].bat_ids
    bowl_ids = default["rd"].bow_ids
    ridge_bat = default["fitted"]["bat_high"]
    ridge_bowl = default["fitted"]["bow_high"]

    bat_point = eb_point(default, "batter", bat_ids) if decisions["batter"] == "E3_EB_general" else ridge_bat
    bowl_point = eb_point(default, "bowler", bowl_ids) if decisions["bowler"] == "E3_EB_general" else ridge_bowl

    bat_boot = bootstrap_eb(default, "batter", bat_ids) if decisions["batter"] == "E3_EB_general" else default["bat_boot"]
    bowl_boot = bootstrap_eb(default, "bowler", bowl_ids) if decisions["bowler"] == "E3_EB_general" else default["bowl_boot"]

    bat_beta_delta = bootstrap_general_pressure(default, "batter", bat_ids)
    bowl_beta_delta = bootstrap_general_pressure(default, "bowler", bowl_ids)

    # 4. Generate rankings (eligible, active 365, Pakistan excluded, Bangladesh in)
    bat = make_ranking(default, "batter", primary, bat_boot, 150, bat_beta_delta, bat_point, ridge_bat, decisions["batter"], overall_last_s)
    bowl = make_ranking(default, "bowler", primary, bowl_boot, 120, bowl_beta_delta, bowl_point, ridge_bowl, decisions["bowler"], overall_last_s)
    alt_bat = make_ranking(default, "batter", alternate, bat_boot, 150, bat_beta_delta, bat_point, ridge_bat, decisions["batter"], overall_last_s)
    alt_bowl = make_ranking(default, "bowler", alternate, bowl_boot, 120, bowl_beta_delta, bowl_point, ridge_bowl, decisions["bowler"], overall_last_s)

    for name, frame in {
        "batters": bat, "bowlers": bowl,
        "primary_batters": bat, "primary_bowlers": bowl,
    }.items():
        frame.to_csv(FINAL / f"{name}.csv", index=False)
        frame.to_csv(ROOT_FINAL / f"{name}.csv", index=False)

    tournament.to_csv(FINAL / "tournament_summary.csv", index=False)
    tournament.to_csv(ROOT_FINAL / "tournament_summary.csv", index=False)

    # 5. Rebuild sensitivity table calling the SAME final-ranking function for every variant
    print("\n--- REBUILDING SENSITIVITY TABLE ---")
    base_ranked = {
        "batter": rank_variant(default, "batter", estimator=decisions["batter"], excluded=primary, overall_last_s=overall_last_s),
        "bowler": rank_variant(default, "bowler", estimator=decisions["bowler"], excluded=primary, overall_last_s=overall_last_s)
    }

    sensitivity_rows = []
    variants = [
        ("fractional_expected", default),
        ("rounded", run("rounded", 0.75, 730, do_bootstrap=False)),
        ("base_only", run("base_only", 0.75, 730, do_bootstrap=False)),
        ("PI_q0.70", run("fractional_expected", 0.70, 730, do_bootstrap=False)),
        ("PI_q0.75", default),
        ("PI_q0.80", run("fractional_expected", 0.80, 730, do_bootstrap=False)),
        ("no_time_decay", run("fractional_expected", 0.75, np.inf, do_bootstrap=False)),
        ("half_life_730", default),
    ]

    for label, trial in variants:
        trial_last = overall_last_s if trial is default else get_overall_last_dates(trial["d"])
        for role in ("batter", "bowler"):
            base_r = base_ranked[role]
            base_ids10 = set(base_r.head(10)["player_id"])
            base_ids15 = set(base_r.head(15)["player_id"])

            if trial is default:
                sensitivity_rows.append({
                    "role": role, "run": label,
                    "top10_overlap": 10, "top15_overlap": 15, "kendall_tau": 1.0
                })
            else:
                trial_r = rank_variant(trial, role, estimator=decisions[role], excluded=primary, overall_last_s=trial_last)
                trial_ids10 = set(trial_r.head(10)["player_id"])
                trial_ids15 = set(trial_r.head(15)["player_id"])
                common = pd.merge(base_r[["player_id", "score"]].rename(columns={"score": "base"}),
                                  trial_r[["player_id", "score"]].rename(columns={"score": "trial"}),
                                  on="player_id")
                kt = common["base"].corr(common["trial"], method="kendall") if len(common) > 1 else np.nan
                sensitivity_rows.append({
                    "role": role, "run": label,
                    "top10_overlap": len(base_ids10 & trial_ids10),
                    "top15_overlap": len(base_ids15 & trial_ids15),
                    "kendall_tau": kt
                })

    # Additional sensitivity rows: rho_inf, ridge_vs_EB_estimator, IPL_only, alternate_vs_primary
    for role in ("batter", "bowler"):
        base_r = base_ranked[role]
        base_ids10 = set(base_r.head(10)["player_id"])
        base_ids15 = set(base_r.head(15)["player_id"])

        # rho_inf (only affects ridge)
        inf_r = rank_variant(default, role, estimator=decisions[role], excluded=primary, rho_inf=True, overall_last_s=overall_last_s)
        common_inf = pd.merge(base_r[["player_id", "score"]].rename(columns={"score": "base"}),
                              inf_r[["player_id", "score"]].rename(columns={"score": "trial"}),
                              on="player_id")
        kt_inf = common_inf["base"].corr(common_inf["trial"], method="kendall") if len(common_inf) > 1 else np.nan
        sensitivity_rows.append({
            "role": role, "run": "rho_inf",
            "top10_overlap": len(base_ids10 & set(inf_r.head(10)["player_id"])),
            "top15_overlap": len(base_ids15 & set(inf_r.head(15)["player_id"])),
            "kendall_tau": kt_inf
        })

        # ridge vs EB estimator
        opp_estimator = "E5_ridge_rho3" if decisions[role] == "E3_EB_general" else "E3_EB_general"
        opp_r = rank_variant(default, role, estimator=opp_estimator, excluded=primary, overall_last_s=overall_last_s)
        common_opp = pd.merge(base_r[["player_id", "score"]].rename(columns={"score": "base"}),
                              opp_r[["player_id", "score"]].rename(columns={"score": "trial"}),
                              on="player_id")
        kt_opp = common_opp["base"].corr(common_opp["trial"], method="kendall") if len(common_opp) > 1 else np.nan
        sensitivity_rows.append({
            "role": role, "run": "ridge_vs_EB_estimator",
            "top10_overlap": len(base_ids10 & set(opp_r.head(10)["player_id"])),
            "top15_overlap": len(base_ids15 & set(opp_r.head(15)["player_id"])),
            "kendall_tau": kt_opp
        })

        # IPL_only
        ipl_r = rank_variant(default, role, estimator=decisions[role], excluded=primary, ipl_only=True, overall_last_s=overall_last_s)
        common_ipl = pd.merge(base_r[["player_id", "score"]].rename(columns={"score": "base"}),
                              ipl_r[["player_id", "score"]].rename(columns={"score": "trial"}),
                              on="player_id")
        kt_ipl = common_ipl["base"].corr(common_ipl["trial"], method="kendall") if len(common_ipl) > 1 else np.nan
        sensitivity_rows.append({
            "role": role, "run": "IPL_only",
            "top10_overlap": len(base_ids10 & set(ipl_r.head(10)["player_id"])),
            "top15_overlap": len(base_ids15 & set(ipl_r.head(15)["player_id"])),
            "kendall_tau": kt_ipl
        })

    sensitivity = pd.DataFrame(sensitivity_rows)
    sensitivity.to_csv(FINAL / "sensitivity.csv", index=False)
    sensitivity.to_csv(ROOT_FINAL / "sensitivity.csv", index=False)
    print(sensitivity.to_string(index=False))

    # 6. Delta evidence table & player diagnostics
    d = default["d"].copy()
    high = d[d["set"].eq("HIGH")].copy()

    delta_rows = []
    for role, frame in [("batter", bat), ("bowler", bowl)]:
        delta_rows.append({
            "role": role,
            "eligible_players": len(frame),
            "delta_interval_above_zero": int((frame["delta_lo80_runs_per_100_balls"] > 0).sum()),
            "delta_interval_below_zero": int((frame["delta_hi80_runs_per_100_balls"] < 0).sum()),
        })
    delta_df = pd.DataFrame(delta_rows)
    delta_df.to_csv(FINAL / "delta_evidence.csv", index=False)
    delta_df.to_csv(ROOT_FINAL / "delta_evidence.csv", index=False)
    print("\n--- DELTA EVIDENCE (80% CI entirely above / below 0) ---")
    print(delta_df.to_string(index=False))

    # Diagnostics for named players
    named_players = {
        "Vaibhav Sooryavanshi": 50284,
        "Yashasvi Jaiswal": None,
        "Shubman Gill": None,
        "Sai Sudharsan": None,
        "Ruturaj Gaikwad": None,
        "Rinku Singh": None
    }
    print("\n--- NAMED PLAYER DIAGNOSTICS ---")
    for name, pid in named_players.items():
        if pid is not None:
            p_matches = mapping[mapping[C["player_id"]] == pid]
        else:
            p_matches = mapping[mapping[C["player_name"]].astype(str).str.contains(name, case=False, na=False)]
        pids = p_matches[C["player_id"]].dropna().unique().astype(int)
        for p in pids:
            p_name = mapping.loc[mapping[C["player_id"]] == p, C["player_name"]].iloc[0]
            h_count = int(high[high["striker_id"] == p].shape[0])
            in_batters = p in bat["player_id"].values
            if in_batters:
                row = bat[bat["player_id"] == p].iloc[0]
                filter_status = f"ELIGIBLE (Rank {int(row['rank'])}, Rating {row['rating_runs_per_100_balls']:.2f})"
            elif h_count < 150:
                filter_status = f"EXCLUDED: Sample floor (< 150 HIGH balls; faced {h_count})"
            else:
                filter_status = "EXCLUDED: Inactivity (> 365 days) or Pakistan nationality"
            print(f"diagnostic | {p_name:22s} (ID {p:5d}) | HIGH balls: {h_count:3d} | Status: {filter_status}")

    # Near-miss table: 100-149 HIGH balls with rating > 10th-ranked qualified batter
    tenth_rating = float(bat.iloc[9]["rating_runs_per_100_balls"])
    tenth_name = bat.iloc[9]["display_name"]
    print(f"\n--- NEAR-MISS TABLE (100-149 HIGH balls, rating above 10th-ranked {tenth_name} [{tenth_rating:.2f}]) ---")
    batter_stats = high[high["striker_id"].notna()].groupby("striker_id").agg(
        n_high=("y", "size"), mean_y=("y", "mean")
    ).reset_index()
    sigma2_high = float(high["y"].var(ddof=1))
    batter_stats["eb_rating"] = pc.eb_shrink(batter_stats["mean_y"].to_numpy(), batter_stats["n_high"].to_numpy(), sigma2_high)["post"] * 100
    batter_stats["raw_rating"] = batter_stats["mean_y"] * 100

    near_miss = batter_stats[(batter_stats["n_high"].between(100, 149)) & (batter_stats["eb_rating"] > tenth_rating)].copy()
    near_miss = near_miss.merge(names, left_on="striker_id", right_on="player_id", how="left")
    near_miss = near_miss[["player_id", "display_name", "n_high", "eb_rating", "raw_rating"]].sort_values("eb_rating", ascending=False)
    if len(near_miss) > 0:
        print(near_miss.to_string(index=False))
    else:
        print("No players met both criteria.")

    # Additional artifacts and profile tables
    share_rows = []
    for group in ["innings", "phase_idx", "over"]:
        counts = d.groupby(group).size()
        high_counts = high.groupby(group).size()
        for key in counts.index:
            share_rows.append({"dimension": group, "value": key, "n_balls": counts[key], "n_HIGH": high_counts.get(key, 0), "high_share": high_counts.get(key, 0) / counts[key]})
    high_share = pd.DataFrame(share_rows)
    high_share.to_csv(FINAL / "high_share.csv", index=False)
    high_share.to_csv(ROOT_FINAL / "high_share.csv", index=False)

    heat = d.pivot_table(index="b", columns="w_before", values="PI", aggfunc="mean")
    heat.to_csv(FINAL / "pi_heatmap.csv")
    heat.to_csv(ROOT_FINAL / "pi_heatmap.csv")

    profiles = []
    for role, frame, player_col in [("batter", bat, "striker_id"), ("bowler", bowl, "bowler_id")]:
        for player_id in frame["player_id"]:
            p = d[d[player_col].eq(player_id)]
            h, l = p[p["set"].eq("HIGH")], p[p["set"].eq("LOW")]
            profiles.append({
                "role": role, "player_id": player_id, "display_name": frame.loc[frame["player_id"].eq(player_id), "display_name"].iloc[0],
                "IPL_HIGH": int((h["comp_group"] == "IPL").sum()), "T20I_HIGH": int((h["comp_group"] == "T20I").sum()),
                "last_match_date": overall_last_s.get(player_id, p["match_date"].max()), "HIGH_run_rate_per_over": h["runs_total"].mean() * 6,
                "LOW_run_rate_per_over": l["runs_total"].mean() * 6, "HIGH_n": len(h), "LOW_n": len(l),
                "strike_rate_HIGH": h["runs_total"].sum() / max(len(h), 1) * 100 if role == "batter" else np.nan,
                "strike_rate_LOW": l["runs_total"].sum() / max(len(l), 1) * 100 if role == "batter" else np.nan,
                "economy_HIGH": h["runs_total"].sum() / max(len(h), 1) * 6 if role == "bowler" else np.nan,
                "economy_LOW": l["runs_total"].sum() / max(len(l), 1) * 6 if role == "bowler" else np.nan,
                "low_sample_warning": len(h) < (150 if role == "batter" else 120)
            })
    profiles_df = pd.DataFrame(profiles)
    profiles_df.to_csv(FINAL / "player_profiles.csv", index=False)
    profiles_df.to_csv(FINAL / "profiles.csv", index=False)
    profiles_df.to_csv(ROOT_FINAL / "player_profiles.csv", index=False)
    profiles_df.to_csv(ROOT_FINAL / "profiles.csv", index=False)

    # 7. Copy all other validation tables to outputs/final
    table_copies = {
        "wp_report.csv": "wp_report.csv",
        "high_low_table.csv": "high_low.csv",
        "reliability_diagnostics.csv": "reliability.csv",
        "cv_hyper.csv": "cv_hyper.csv",
        "kappa_table.csv": "kappa.csv",
        "eligibility_counts.csv": "exclusions.csv",
        "pressure_balls.parquet": "pressure_balls.parquet",
    }
    for src_name, dst_name in table_copies.items():
        src_path = TABLES / src_name
        if src_path.exists():
            shutil.copy(src_path, FINAL / dst_name)
            shutil.copy(src_path, ROOT_FINAL / dst_name)

    # Generate Figures
    plt.figure(figsize=(7, 5))
    for label, group in d.groupby("set"):
        plt.scatter(group["LI"], group["dWP"].abs(), s=5, label=label)
    plt.legend()
    plt.xlabel("Expected leverage")
    plt.ylabel("Realised |dWP|")
    plt.savefig(FIGURES / "expected_li_vs_realised.png", dpi=300)
    plt.close()

    plt.figure(figsize=(7, 5))
    plt.imshow(heat.to_numpy(), aspect="auto", cmap="viridis")
    plt.colorbar(label="Mean PI")
    plt.xticks(range(len(heat.columns)), heat.columns)
    plt.yticks(range(len(heat.index)), heat.index)
    plt.savefig(FIGURES / "pi_heatmap.png", dpi=300)
    plt.close()

    for frame, title in [(bat.head(10), "batters"), (bowl.head(10), "bowlers")]:
        plt.figure(figsize=(10, 5))
        yerr_low = np.maximum(0, frame["rating_runs_per_100_balls"] - frame["lo80_runs_per_100_balls"])
        yerr_high = np.maximum(0, frame["hi80_runs_per_100_balls"] - frame["rating_runs_per_100_balls"])
        plt.errorbar(frame["display_name"], frame["rating_runs_per_100_balls"],
                     yerr=[yerr_low, yerr_high], fmt="o")
        plt.xticks(rotation=70, ha="right")
        plt.tight_layout()
        plt.savefig(FIGURES / f"top10_{title}.png", dpi=300)
        plt.close()

    plt.figure(figsize=(7, 5))
    plt.scatter(bat["beta_general_runs_per_100_balls"], bat["delta_pressure_runs_per_100_balls"], label="batters")
    plt.scatter(bowl["beta_general_runs_per_100_balls"], bowl["delta_pressure_runs_per_100_balls"], label="bowlers")
    plt.legend()
    plt.savefig(FIGURES / "beta_delta_scatter.png", dpi=300)
    plt.close()

    plt.figure(figsize=(8, 5))
    for role, group in tournament.groupby("role"):
        yerr_low = np.maximum(0, group["mean_pearson"] - group["p05"])
        yerr_high = np.maximum(0, group["p95"] - group["mean_pearson"])
        plt.errorbar(group["estimator"], group["mean_pearson"],
                     yerr=[yerr_low, yerr_high], fmt="o", label=role)
    plt.legend()
    plt.xticks(rotation=70)
    plt.tight_layout()
    plt.savefig(FIGURES / "tournament_pearson.png", dpi=300)
    plt.close()

    # Audit report
    audit = ROOT / "outputs" / "audit" / "audit_report.md"
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text(
        "# Corrected pressure-model audit\n\n"
        f"- high_offset_runs_per_ball: {default['fitted'].get('high_offset')}\n"
        f"- latest_match_date: {pd.to_datetime(default['d']['match_date']).max().date()}\n\n"
        "## Tournament\n\n" + md(tournament) +
        "\n\n## Paired Differences\n\n" + md(paired_differences) +
        "\n\n## Sensitivity\n\n" + md(sensitivity) +
        "\n\n## Delta evidence\n\n" + md(delta_df) +
        "\n\n## Final lists\n\n### Primary batters\n\n" + md(bat.head(10)) +
        "\n\n### Primary bowlers\n\n" + md(bowl.head(10)) + "\n"
    )

    print("\n--- SAVED FINAL OUTPUTS ---")
    for f in sorted(FINAL.glob("*")):
        print(f"  {f.name:30s} -> {f}")
    print("\n--- SAVED ROOT OUTPUTS ---")
    for f in sorted(ROOT_FINAL.glob("*")):
        print(f"  {f.name:30s} -> {f}")


if __name__ == "__main__":
    main()
