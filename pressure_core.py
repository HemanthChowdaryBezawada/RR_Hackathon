"""
pressure_core.py - reference implementation of the statistical core of the pressure model.

Purpose: replace the shortcuts in run_all.py (leaky win probability, realised-outcome pressure,
no real ridge model, fabricated bootstrap) with a leak-free, ex-ante, fully computed pipeline.

Canonical delivery-frame columns expected (rename your pipeline columns to these):
  match_id, innings (1/2 only), over (1-20), innings_ball_num, batting_team_id, bowling_team_id,
  striker_id, bowler_id, dismissed_player_id, extras_type (NaN or wide/Overstep/other/byes/legbyes/Penalty),
  dismissal_type, runs (BAT runs only), runs_total (reconstructed team runs on the delivery),
  legal (bool), wicket (0/1; Retire Out and the 12 flag-less rows are 0), batting_won (0/1),
  venue_id, comp_group (IPL/T20I/T20_other), match_date, season_year, w_opp (opposition weight)
Everything is computed from data; nothing is hard-coded except documented defaults.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import lightgbm as lgb
from joblib import Parallel, delayed
from scipy import sparse
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import Ridge
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

SEED = 42
OUTCOMES = ["dot", "1", "2", "3", "4", "6", "W", "wd", "nb"]
OUT_RUNS = np.array([0, 1, 2, 3, 4, 6, 0, 1, 1], float)
OUT_LEGAL = np.array([1, 1, 1, 1, 1, 1, 1, 0, 0], int)
OUT_WKT = np.array([0, 0, 0, 0, 0, 0, 1, 0, 0], int)
RUN_LUT = np.array([0, 1, 2, 3, 4, 4, 5])  # rounded team runs 0..6 -> outcome index
HSCALE = 30.0  # scale of the unpenalised HIGH main-effect column (effective penalty / HSCALE**2)


# ----------------------------------------------------------------------------- state, Elo, weights
def add_state(df: pd.DataFrame) -> pd.DataFrame:
    """Pre-delivery state. `target` exists ONLY for innings 2 (first-innings total + 1).
    NEVER give the first-innings final total to an innings-1 row (that is leakage)."""
    df = df.sort_values(["match_id", "innings", "innings_ball_num"]).reset_index(drop=True)
    df["legal"] = df["legal"].astype(int)
    g = df.groupby(["match_id", "innings"])
    df["s_before"] = g["runs_total"].cumsum() - df["runs_total"]
    df["w_before"] = g["wicket"].cumsum() - df["wicket"]
    df["b"] = (120 - (g["legal"].cumsum() - df["legal"])).clip(lower=0)
    first_total = df[df.innings == 1].groupby("match_id")["runs_total"].sum()
    df["target"] = np.where(df.innings == 2, df.match_id.map(first_total) + 1, np.nan)
    df["phase_idx"] = np.where(df["over"] <= 6, 0, np.where(df["over"] <= 15, 1, 2))
    df["is_ipl"] = (df["comp_group"] == "IPL").astype(float)
    return df


def venue_par(df: pd.DataFrame, k: float = 10.0) -> pd.Series:
    """Leave-one-match-out venue par (shrunk to the comp_group mean). Returned per match_id."""
    t = df[df.innings == 1].groupby("match_id").agg(
        venue=("venue_id", "first"), grp=("comp_group", "first"), tot=("runs_total", "sum"))
    v_sum = t.groupby("venue")["tot"].transform("sum") - t["tot"]
    v_n = t.groupby("venue")["tot"].transform("count") - 1
    g_sum = t.groupby("grp")["tot"].transform("sum") - t["tot"]
    g_n = (t.groupby("grp")["tot"].transform("count") - 1).clip(lower=1)
    mu = g_sum / g_n
    return ((v_sum + k * mu) / (v_n + k)).rename("par")


def pre_match_elo(matches: pd.DataFrame, k: float = 20.0, base: float = 1500.0) -> pd.DataFrame:
    """Pre-match Elo (updated only AFTER each match). Columns needed: match_id, match_date,
    home_team_id, away_team_id, win_team_id, pool (e.g. IPL / NAT / A). Separate pools."""
    m = matches.sort_values(["match_date", "match_id"])
    rating: dict = {}
    out = []
    for r in m.itertuples(index=False):
        ka, kb = (r.pool, r.home_team_id), (r.pool, r.away_team_id)
        a, b = rating.setdefault(ka, base), rating.setdefault(kb, base)
        out.append((r.match_id, a, b))
        if pd.notna(r.win_team_id) and r.win_team_id in (r.home_team_id, r.away_team_id):
            e = 1.0 / (1.0 + 10 ** ((b - a) / 400.0))
            sc = float(r.win_team_id == r.home_team_id)
            rating[ka] = a + k * (sc - e)
            rating[kb] = b + k * ((1 - sc) - (1 - e))
    return pd.DataFrame(out, columns=["match_id", "home_elo", "away_elo"]).set_index("match_id")


def attach_elo(df: pd.DataFrame, elo: pd.DataFrame, home_team: pd.Series) -> pd.DataFrame:
    """elo_diff / elo_opp from the BATTING team's point of view, per match (not per team)."""
    home_elo = df.match_id.map(elo["home_elo"]).to_numpy()
    away_elo = df.match_id.map(elo["away_elo"]).to_numpy()
    bat_home = (df.batting_team_id.to_numpy() == df.match_id.map(home_team).to_numpy())
    df["elo_bat"] = np.where(bat_home, home_elo, away_elo)
    df["elo_opp"] = np.where(bat_home, away_elo, home_elo)
    df["elo_diff"] = df["elo_bat"] - df["elo_opp"]
    return df


def opp_weight(df: pd.DataFrame, a_team_ids: set, extra_down: float = 0.6) -> pd.Series:
    """w_opp = clip(Elo_opp/1500, .6, 1.1) for T20I; 1 for IPL; x0.6 for A-team / T20_other. Range [0.36,1.1]."""
    w = np.where(df.comp_group == "IPL", 1.0, np.clip(df.elo_opp / 1500.0, 0.6, 1.1))
    a_match = df.batting_team_id.isin(a_team_ids) | df.bowling_team_id.isin(a_team_ids)
    w = np.where((df.comp_group == "T20_other") | a_match, w * extra_down, w)
    return pd.Series(np.clip(w, 0.36, 1.1), index=df.index)


def time_weight(dates: pd.Series, half_life_days: float = 730.0) -> pd.Series:
    d = pd.to_datetime(dates)
    age = (d.max() - d).dt.days
    return 0.5 ** (age / half_life_days)


def assign_folds(match_ids, n_splits: int = 5, seed: int = SEED) -> pd.Series:
    """Balanced random match -> fold map, reused for WP, expected-value models and CV."""
    u = np.unique(match_ids)
    rng = np.random.default_rng(seed)
    return pd.Series(rng.permutation(len(u)) % n_splits, index=u, name="fold")


# ----------------------------------------------------------------------------- resource table
class ResourceTable:
    """Res(b, w): mean runs still to be scored from (balls left, wickets lost) in FULL first innings,
    normalised by Res(120, 0); monotone (more balls -> more, more wickets -> less)."""

    def fit(self, df: pd.DataFrame) -> "ResourceTable":
        f = df[df.innings == 1]
        end = f.groupby("match_id")["runs_total"].transform("sum")
        rem = end - f["s_before"]
        k = np.ceil(f["b"] / 6).astype(int).clip(0, 20)
        w = f["w_before"].clip(0, 9).astype(int)
        tab = (pd.DataFrame({"k": k, "w": w, "rem": rem}).groupby(["k", "w"])["rem"].mean()
               .unstack().reindex(index=range(21), columns=range(10)))
        tab = tab.interpolate(axis=1, limit_direction="both").interpolate(axis=0, limit_direction="both")
        v = tab.to_numpy(dtype=float).copy()
        v[0, :] = 0.0
        v = np.maximum.accumulate(v, axis=0)          # non-decreasing in balls left
        v = np.minimum.accumulate(v, axis=1)          # non-increasing in wickets lost
        self.tab = v / v[20, 0]
        return self

    def lookup(self, b, w) -> np.ndarray:
        k = np.clip(np.ceil(np.asarray(b, float) / 6), 0, 20).astype(int)
        j = np.clip(np.asarray(w, float), 0, 9).astype(int)
        return self.tab[k, j]


# ----------------------------------------------------------------------------- win probability
def make_features(inn: int, s, w, b, target, par, elo, ipl, res) -> pd.DataFrame:
    s, w, b, par, elo, ipl, res = (np.asarray(x, float) for x in (s, w, b, par, elo, ipl, res))
    crr = 6 * s / np.maximum(120 - b, 1)
    f = {"w": w, "b": b, "crr": crr, "par": par, "elo": elo, "ipl": ipl, "res": res}
    if inn == 1:
        f["s"] = s
        f["proj"] = s + res * par
        f["proj_gap"] = f["proj"] - par
    else:
        R = np.asarray(target, float) - s
        rrr = 6 * R / np.maximum(b, 1)
        f.update(R=R, rrr=rrr, gap=rrr - crr, parratio=R / np.maximum(res * par, 1.0), target=np.asarray(target, float))
    return pd.DataFrame(f)


_MONO = {1: {"w": -1, "proj": 1, "elo": 1},
         2: {"R": -1, "w": -1, "rrr": -1, "parratio": -1, "elo": 1}}
_LGB = dict(n_estimators=300, learning_rate=0.05, num_leaves=15, min_child_samples=200,
            subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=5.0, verbose=-1)


class WPModel:
    """Two LightGBM classifiers (innings 1 / innings 2), monotone constraints, match-grouped
    out-of-fold predictions, cross-fitted isotonic calibration. No player/team identity."""

    def __init__(self, rt: ResourceTable, fold_of_match: pd.Series, n_jobs: int = 4):
        self.rt, self.fold_of, self.n_jobs = rt, fold_of_match, n_jobs
        self.models: dict = {1: {}, 2: {}}
        self.iso: dict = {1: {}, 2: {}}

    def _X(self, d: pd.DataFrame, inn: int) -> pd.DataFrame:
        return make_features(inn, d.s_before, d.w_before, d.b, d.target, d.par, d.elo_diff, d.is_ipl, d.res)

    def fit(self, df: pd.DataFrame) -> pd.Series:
        wp = pd.Series(np.nan, index=df.index)
        for inn in (1, 2):
            d = df[df.innings == inn]
            X, y = self._X(d, inn), d["batting_won"].to_numpy()
            fold = d.match_id.map(self.fold_of).to_numpy()
            mono = [_MONO[inn].get(c, 0) for c in X.columns]
            raw = np.zeros(len(d))
            for k in np.unique(fold):
                tr, te = fold != k, fold == k
                m = lgb.LGBMClassifier(monotone_constraints=mono, random_state=SEED, n_jobs=self.n_jobs, **_LGB)
                m.fit(X[tr], y[tr])
                self.models[inn][k] = m
                raw[te] = m.predict_proba(X[te])[:, 1]
            cal = np.zeros(len(d))
            for k in np.unique(fold):
                iso = IsotonicRegression(y_min=0.001, y_max=0.999, out_of_bounds="clip").fit(raw[fold != k], y[fold != k])
                self.iso[inn][k] = iso
                cal[fold == k] = iso.predict(raw[fold == k])
            wp.loc[d.index] = cal
        return wp

    def predict(self, inn: int, X: pd.DataFrame, fold: np.ndarray) -> np.ndarray:
        out = np.empty(len(X))
        for k in np.unique(fold):
            m = fold == k
            out[m] = self.iso[inn][k].predict(self.models[inn][k].predict_proba(X[m])[:, 1])
        return out


def wp_report(df: pd.DataFrame, col: str = "wp_before") -> pd.DataFrame:
    """Log-loss, Brier, AUC and weighted ECE by innings and comp_group (all out-of-fold)."""
    rows = []
    for inn in (1, 2):
        for grp in ["all"] + sorted(df.comp_group.unique()):
            d = df[(df.innings == inn) & ((df.comp_group == grp) | (grp == "all"))]
            if len(d) < 200 or d.batting_won.nunique() < 2:
                continue
            p, y = d[col].to_numpy(), d.batting_won.to_numpy()
            bins = np.clip((p * 10).astype(int), 0, 9)
            ece = sum(abs(p[bins == i].mean() - y[bins == i].mean()) * (bins == i).mean() for i in range(10) if (bins == i).any())
            rows.append(dict(innings=inn, group=grp, n=len(d), log_loss=log_loss(y, p), brier=brier_score_loss(y, p),
                             auc=roc_auc_score(y, p), ece=ece, base_logloss=log_loss(y, np.full(len(y), y.mean()))))
    return pd.DataFrame(rows)


def chain_wp(df: pd.DataFrame) -> pd.DataFrame:
    """dWP from the BATTING team's perspective. Last ball of innings 1 hands over to the chase
    (wp_after = 1 - WP2 at the start of the chase); only the last ball of the match uses the result."""
    nxt = df.groupby(["match_id", "innings"])["wp_before"].shift(-1)
    start2 = df[df.innings == 2].groupby("match_id")["wp_before"].first()
    last1 = nxt.isna() & (df.innings == 1)
    nxt[last1] = 1 - df.loc[last1, "match_id"].map(start2)
    last2 = nxt.isna() & (df.innings == 2)
    nxt[last2] = df.loc[last2, "batting_won"]
    df["wp_after"] = nxt
    df["dWP"] = df["wp_after"] - df["wp_before"]
    assert df["dWP"].notna().all(), "dWP has NaN: some match lacks innings 2"
    return df


# ----------------------------------------------------------------------------- ex-ante pressure
def outcome_index(df: pd.DataFrame) -> np.ndarray:
    ex = df["extras_type"].fillna("")
    r = np.clip(np.rint(df["runs_total"].to_numpy()), 0, 6).astype(int)
    idx = RUN_LUT[r]
    idx = np.where(df["wicket"].to_numpy() == 1, 6, idx)
    idx = np.where(ex.isin(["Overstep", "other"]).to_numpy(), 8, idx)
    return np.where(ex.eq("wide").to_numpy(), 7, idx)


def bucket_id(inn, over, w, b) -> np.ndarray:
    ph = np.where(over <= 6, 0, np.where(over <= 15, 1, 2))
    wg = np.where(w <= 2, 0, np.where(w <= 5, 1, 2))
    bt = np.where(b > 80, 0, np.where(b > 40, 1, 2))
    return (np.asarray(inn, int) - 1) * 27 + ph * 9 + wg * 3 + bt


def outcome_probs(df: pd.DataFrame) -> np.ndarray:
    """P(outcome | innings, phase, wickets group, balls-left tercile); Laplace-smoothed; players ignored."""
    bid = bucket_id(df.innings, df.over, df.w_before, df.b)
    cnt = np.ones((54, 9))
    np.add.at(cnt, (bid, outcome_index(df)), 1.0)
    return cnt / cnt.sum(1, keepdims=True)


def expected_leverage(df: pd.DataFrame, wpm: WPModel, probs: np.ndarray) -> np.ndarray:
    """LI = sum_o P(o|bucket) * |WP(state after o) - WP(state)|. Depends ONLY on the pre-delivery state,
    never on what actually happened (that was the circularity bug: LI = realised |dWP|)."""
    inn, s, w, b = (df[c].to_numpy() for c in ("innings", "s_before", "w_before", "b"))
    tgt, par, elo, ipl = (df[c].to_numpy() for c in ("target", "par", "elo_diff", "is_ipl"))
    fold = df.match_id.map(wpm.fold_of).to_numpy()
    wp0 = df["wp_before"].to_numpy()
    P = probs[bucket_id(inn, df.over, w, b)]
    li = np.zeros(len(df))
    for j in range(9):
        s1, w1, b1 = s + OUT_RUNS[j], np.minimum(w + OUT_WKT[j], 10), b - OUT_LEGAL[j]
        wp1 = np.zeros(len(df))
        m2 = inn == 2
        won = m2 & (s1 >= tgt)
        lost = m2 & ~won & ((w1 >= 10) | (b1 <= 0))
        wp1[won], wp1[lost] = 1.0, 0.0
        live2 = m2 & ~won & ~lost
        m1 = inn == 1
        end1 = m1 & ((w1 >= 10) | (b1 <= 0))
        live1 = m1 & ~end1
        for mask, innn in ((live1, 1), (live2, 2)):
            if mask.any():
                X = make_features(innn, s1[mask], w1[mask], b1[mask], tgt[mask], par[mask], elo[mask], ipl[mask],
                                  wpm.rt.lookup(b1[mask], w1[mask]))
                wp1[mask] = wpm.predict(innn, X, fold[mask])
        if end1.any():  # innings ends: chasing side faces target s1+1 from a fresh start
            X = make_features(2, np.zeros(end1.sum()), np.zeros(end1.sum()), np.full(end1.sum(), 120.0), s1[end1] + 1,
                              par[end1], -elo[end1], ipl[end1], np.ones(end1.sum()))
            wp1[end1] = 1 - wpm.predict(2, X, fold[end1])
        li += P[:, j] * np.abs(wp1 - wp0)
    return li


def pressure_index(df: pd.DataFrame, rt: ResourceTable, weights=(0.60, 0.25, 0.15), hi_q=0.75, lo_q=0.50) -> pd.DataFrame:
    """PI = .6 pct(LI) + .25 closeness + .15 resource scarcity; HIGH = top quartile, LOW = bottom half."""
    df["LI_pct"] = df["LI"].rank(pct=True)
    df["closeness"] = 1 - 2 * (df["wp_before"] - 0.5).abs()
    df["scarcity"] = 1 - rt.lookup(df["b"], df["w_before"])
    df["PI"] = weights[0] * df["LI_pct"] + weights[1] * df["closeness"] + weights[2] * df["scarcity"]
    hi, lo = df["PI"].quantile(hi_q), df["PI"].quantile(lo_q)
    df["set"] = np.where(df["PI"] >= hi, "HIGH", np.where(df["PI"] <= lo, "LOW", "MEDIUM"))
    df["w_p"] = np.where(df["set"] == "HIGH", 1 + (df["PI"] - hi) / (1 - hi), 1.0)
    return df


def high_low_table(df: pd.DataFrame) -> pd.DataFrame:
    """Non-circular validation: pressure is ex-ante, so every column below is an OUTCOME it should explain."""
    rows = []
    for name in ("HIGH", "MEDIUM", "LOW"):
        d = df[df["set"] == name]
        rows.append(dict(set=name, n=len(d), mean_abs_dWP=d.dWP.abs().mean(), sd_dWP=d.dWP.std(),
                         wicket_rate=d.wicket.mean(), dot_pct=(d.runs_total == 0).mean(), run_rate=6 * d.runs_total.mean(),
                         undecided_share=((d.wp_before - 0.5).abs() < 0.25).mean(), mean_expected_LI=d.LI.mean()))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- expected value and ball value
def fit_expected(df: pd.DataFrame, fold_of_match: pd.Series, n_jobs: int = 4) -> pd.DataFrame:
    """Out-of-fold xRuns (team runs) and xWicket from STATE ONLY (no player identity)."""
    X = pd.DataFrame({"inn": df.innings, "over": df.over, "b": df.b, "w": df.w_before, "s": df.s_before,
                      "crr": 6 * df.s_before / np.maximum(120 - df.b, 1),
                      "rrr": np.where(df.innings == 2, 6 * (df.target - df.s_before) / np.maximum(df.b, 1), np.nan),
                      "par": df.par, "ipl": df.is_ipl})
    fold = df.match_id.map(fold_of_match).to_numpy()
    xr, xw = np.zeros(len(df)), np.zeros(len(df))
    p = dict(n_estimators=200, learning_rate=0.05, num_leaves=15, min_child_samples=300, subsample=0.8,
             subsample_freq=1, colsample_bytree=0.8, reg_lambda=5.0, verbose=-1, n_jobs=n_jobs, random_state=SEED)
    for k in np.unique(fold):
        tr, te = fold != k, fold == k
        xr[te] = lgb.LGBMRegressor(**p).fit(X[tr], df.runs_total[tr]).predict(X[te])
        xw[te] = lgb.LGBMClassifier(**p).fit(X[tr], df.wicket[tr]).predict_proba(X[te])[:, 1]
    df["x_runs"], df["x_wkt"] = xr, xw
    return df


def estimate_K(df: pd.DataFrame) -> dict:
    """Runs-equivalent of a wicket and WP-per-run, by OLS of dWP on (runs_total, wicket) on HIGH balls."""
    out = {}
    for name, d in [("all", df[df["set"] == "HIGH"])] + [(f"phase{p}", df[(df["set"] == "HIGH") & (df.phase_idx == p)]) for p in range(3)]:
        A = np.column_stack([np.ones(len(d)), d.runs_total, d.wicket])
        c, *_ = np.linalg.lstsq(A, d.dWP.to_numpy(), rcond=None)
        res = d.dWP.to_numpy() - A @ c
        cov = np.linalg.inv(A.T @ A) * (res @ res) / (len(d) - 3)
        out[name] = dict(kappa_run=c[1], kappa_wkt=c[2], K=-c[2] / c[1], se_run=np.sqrt(cov[1, 1]), se_wkt=np.sqrt(cov[2, 2]))
    return out


def add_ball_value(df: pd.DataFrame, K: dict) -> pd.DataFrame:
    """y = batting-side value over expectation, in runs: (runs - xRuns) - K*(wicket - xWicket)."""
    Kp = df.phase_idx.map({p: K[f"phase{p}"]["K"] for p in range(3)})
    df["y"] = (df.runs_total - df.x_runs) - Kp * (df.wicket - df.x_wkt)
    return df


def attribution(df: pd.DataFrame) -> pd.DataFrame:
    """Who gets credit: byes/legbyes/penalty -> nobody; wides -> bowler only; run-outs -> dismissed
    STRIKER only (non-striker run-outs: nobody); bowler never charged for run-outs."""
    ex = df["extras_type"].fillna("")
    runout = df["dismissal_type"].fillna("").eq("RunOut")
    nonstriker_ro = runout & (df["dismissed_player_id"] != df["striker_id"])
    df["bat_ok"] = ~ex.isin(["wide", "byes", "legbyes", "Penalty"]) & ~nonstriker_ro
    df["bow_ok"] = ~ex.isin(["byes", "legbyes", "Penalty"]) & ~runout
    return df


# ----------------------------------------------------------------------------- shrinkage and reliability
def _dl_tau2(mean: np.ndarray, n: np.ndarray, sigma2: float):
    """DerSimonian-Laird between-player variance. Weights w_i = n_i / sigma2 (inverse sampling variance).
    (The earlier moment estimator mixed n-weighted variance with an unweighted noise term, which is biased
    DOWN and returns tau2 = 0 even when real variance exists. Verified on simulated data in selftest.)"""
    w = n / sigma2
    mu_w = np.sum(w * mean) / np.sum(w)
    Q = float(np.sum(w * (mean - mu_w) ** 2))
    denom = np.sum(w) - np.sum(w ** 2) / np.sum(w)
    tau2 = max(0.0, (Q - (len(mean) - 1)) / denom)
    w2 = 1.0 / (tau2 + sigma2 / n)
    return tau2, float(np.sum(w2 * mean) / np.sum(w2))


def eb_shrink(mean, n, sigma2, n_min: int = 30) -> dict:
    """Normal-normal empirical Bayes with DerSimonian-Laird tau2 on players with n >= n_min (pooled sigma2)."""
    mean, n = np.asarray(mean, float), np.asarray(n, float)
    ok = n >= n_min
    tau2, mu0 = _dl_tau2(mean[ok], n[ok], sigma2)
    B = tau2 / (tau2 + sigma2 / np.maximum(n, 1))
    return dict(post=mu0 + B * (mean - mu0), se=np.sqrt(B * sigma2 / np.maximum(n, 1)), tau2=tau2, mu0=mu0, B=B)


def reliability_diagnostics(player: np.ndarray, value: np.ndarray, n_min: int = 30) -> dict:
    """Per-ball units. sigma2 = POOLED within-player variance; tau2 by DerSimonian-Laird (see _dl_tau2).
    Only players with n >= n_min. mean_rel = average of tau2 / (tau2 + sigma2/n_i)."""
    d = pd.DataFrame({"p": player, "v": value})
    g = d.groupby("p")["v"].agg(["count", "mean", "var"])
    g = g[g["count"] >= n_min]
    sigma2 = float(((g["count"] - 1) * g["var"]).sum() / (g["count"] - 1).sum())
    tau2, _ = _dl_tau2(g["mean"].to_numpy(), g["count"].to_numpy(float), sigma2)
    rel = tau2 / (tau2 + sigma2 / g["count"])
    return dict(n_players=len(g), mean_n=g["count"].mean(), sigma_per_ball=np.sqrt(sigma2), tau_per_ball=np.sqrt(tau2),
                tau_per_100=100 * np.sqrt(tau2), mean_rel=rel.mean(), median_rel=rel.median())


def consistency_units(df: pd.DataFrame, pid_col: str, sign: int, m_min: int, prior: float = 10.0, delta: float = 1.0) -> pd.DataFrame:
    """Units (player, match, innings) with >= m_min HIGH balls. p_pos and disaster_rate Beta-shrunk toward the pool.
    `delta` is the disaster threshold in RUNS of y (sum over the unit). Report only; do not blend unless the tournament says so."""
    h = df[(df["set"] == "HIGH") & (df[pid_col].notna())]
    u = h.groupby([pid_col, "match_id", "innings"]).agg(v=("y", lambda x: sign * x.sum()), n=("y", "size")).reset_index()
    u = u[u.n >= m_min]
    u["pos"], u["dis"] = (u.v > 0).astype(float), (u.v < -delta).astype(float)
    pool_pos, pool_dis = u.pos.mean(), u.dis.mean()
    g = u.groupby(pid_col).agg(units=("v", "size"), pos=("pos", "sum"), dis=("dis", "sum"))
    g["p_pos"] = (g.pos + prior * pool_pos) / (g.units + prior)
    g["disaster_rate"] = (g.dis + prior * pool_dis) / (g.units + prior)
    return g


# ----------------------------------------------------------------------------- hierarchical ridge
class RidgeData:
    """Rows = attributable deliveries. y is the batting-side value; batter column coefficient > 0 = good batter,
    bowler column coefficient > 0 = BAD bowler (rating = -coef). Interaction columns = column x HIGH indicator.
    Penalty alpha_d = rho * alpha_g is implemented by scaling interaction columns by 1/sqrt(rho)."""

    def __init__(self, df: pd.DataFrame, fold_of_match: pd.Series):
        d = df[df.bat_ok | df.bow_ok].reset_index(drop=True)
        self.df = d
        self.bat_ids = np.sort(d.loc[d.bat_ok, "striker_id"].unique())
        self.bow_ids = np.sort(d.loc[d.bow_ok, "bowler_id"].unique())
        bp = pd.Series(np.arange(len(self.bat_ids)), index=self.bat_ids)
        wp_ = pd.Series(np.arange(len(self.bow_ids)), index=self.bow_ids)
        self.bat_col = np.where(d.bat_ok, d.striker_id.map(bp).fillna(-1), -1).astype(int)
        self.bow_col = np.where(d.bow_ok, d.bowler_id.map(wp_).fillna(-1), -1).astype(int)
        self.nb, self.nw = len(self.bat_ids), len(self.bow_ids)
        self.y = d["y"].to_numpy(float)
        self.w = (d["w_time"] * d["w_opp"]).to_numpy(float)
        self.h = (d["set"] == "HIGH").to_numpy(float)
        self.mid = d["match_id"].to_numpy()
        self.fold = d.match_id.map(fold_of_match).to_numpy()
        n, rows = len(d), np.arange(len(d))
        mb, mw = self.bat_col >= 0, self.bow_col >= 0
        Xb = sparse.csr_matrix((np.ones(mb.sum()), (rows[mb], self.bat_col[mb])), shape=(n, self.nb))
        Xw = sparse.csr_matrix((np.ones(mw.sum()), (rows[mw], self.bow_col[mw])), shape=(n, self.nw))
        H = sparse.diags(self.h)
        self.parts = (Xb, Xw, (H @ Xb).tocsr(), (H @ Xw).tocsr())
        # HIGH main effect, scaled up so the ridge penalty on it is negligible (effectively unpenalised).
        # Without it, any average HIGH offset of y leaks into every player's pressure shift (delta).
        self.hcol = sparse.csr_matrix(self.h[:, None] * HSCALE)
        self._cache: dict = {}

    def X(self, rho: float) -> sparse.csr_matrix:
        if rho not in self._cache:
            Xb, Xw, Xbh, Xwh = self.parts
            blocks = [Xb, Xw] if np.isinf(rho) else [Xb, Xw, Xbh / np.sqrt(rho), Xwh / np.sqrt(rho)]
            self._cache[rho] = sparse.hstack(blocks + [self.hcol]).tocsr()
        return self._cache[rho]


def fit_ridge(rd: RidgeData, rho: float, alpha: float, rows=None, weights=None) -> dict:
    X = rd.X(rho)
    y, w = rd.y, (rd.w if weights is None else weights)
    if rows is not None:
        X, y, w = X[rows], y[rows], w[rows]
    m = Ridge(alpha=alpha, fit_intercept=True, solver="sparse_cg", tol=1e-6, max_iter=3000).fit(X, y, sample_weight=w)
    c, nb, nw = m.coef_, rd.nb, rd.nw
    inf = np.isinf(rho)
    delta = np.zeros(nb) if inf else c[nb + nw: 2 * nb + nw] / np.sqrt(rho)
    eta = np.zeros(nw) if inf else c[2 * nb + nw: 2 * nb + 2 * nw] / np.sqrt(rho)
    return dict(model=m, high_offset=float(c[-1] * HSCALE), beta=c[:nb], gamma=c[nb:nb + nw], delta=delta, eta=eta,
                bat_high=c[:nb] + delta, bow_high=-(c[nb:nb + nw] + eta), bat_gen=c[:nb], bow_gen=-c[nb:nb + nw])


def cv_hyper(rd: RidgeData, alphas, rhos, n_splits: int = 5, n_jobs: int = 4) -> pd.DataFrame:
    """Held-out weighted MSE ON HIGH BALLS for every (alpha_g, rho) over match-grouped folds, vs a no-skill baseline."""
    for r in rhos:
        rd.X(r)

    def one(k, a, r):
        te, tr = rd.fold == k, rd.fold != k
        f = fit_ridge(rd, r, a, rows=tr)
        sel = te & (rd.h == 1)
        pred = f["model"].predict(rd.X(r)[sel])
        base = np.average(rd.y[tr], weights=rd.w[tr])
        w = rd.w[sel]
        return k, a, r, float(np.sum(w * (rd.y[sel] - pred) ** 2)), float(np.sum(w * (rd.y[sel] - base) ** 2)), float(w.sum())

    res = Parallel(n_jobs=n_jobs)(delayed(one)(k, a, r) for k in range(n_splits) for a in alphas for r in rhos)
    t = pd.DataFrame(res, columns=["fold", "alpha_g", "rho", "sse", "sse_base", "wsum"])
    g = t.groupby(["alpha_g", "rho"]).sum(numeric_only=True)
    g["mse"], g["mse_base"] = g.sse / g.wsum, g.sse_base / g.wsum
    g["skill"] = 1 - g.mse / g.mse_base
    return g[["mse", "mse_base", "skill"]].reset_index().sort_values("mse")


# ----------------------------------------------------------------------------- tournament
def _wcorr(x, y, w) -> float:
    mx, my = np.average(x, weights=w), np.average(y, weights=w)
    c = np.average((x - mx) * (y - my), weights=w)
    d = np.sqrt(np.average((x - mx) ** 2, weights=w) * np.average((y - my) ** 2, weights=w))
    return float(c / d) if d > 0 else np.nan


def _split(rd: RidgeData, s: int, rhos, alpha: float, min_balls: int, seed: int) -> list:
    rng = np.random.default_rng(seed + s)
    um = np.unique(rd.mid)
    perm = rng.permutation(um)
    A = np.isin(rd.mid, perm[: len(um) // 2])
    B1 = np.isin(rd.mid, perm[len(um) // 2: 3 * len(um) // 4])
    B2 = np.isin(rd.mid, perm[3 * len(um) // 4:])
    isH = rd.h == 1
    fits = {r: fit_ridge(rd, r, alpha, rows=A) for r in [np.inf, *rhos]}
    out = []
    for role, col, nP, sign in (("batter", rd.bat_col, rd.nb, 1.0), ("bowler", rd.bow_col, rd.nw, -1.0)):
        def stats(mask):
            m = mask & (col >= 0)
            n = np.bincount(col[m], minlength=nP).astype(float)
            sy = np.bincount(col[m], weights=sign * rd.y[m], minlength=nP)
            return n, sy / np.maximum(n, 1)
        nAh, mAh = stats(A & isH)
        nAa, mAa = stats(A)
        nBh, mBh = stats(~A & isH)
        n1, m1 = stats(B1 & isH)
        n2, m2 = stats(B2 & isH)
        v = (nAh >= min_balls) & (nBh >= min_balls)
        if v.sum() < 15:
            continue
        sig_h = np.var(sign * rd.y[A & isH & (col >= 0)])
        sig_a = np.var(sign * rd.y[A & (col >= 0)])
        est = {"E1_raw_HIGH": mAh,
               "E2_EB_HIGH": eb_shrink(mAh, nAh, sig_h)["post"],
               "E3_EB_general": eb_shrink(mAa, nAa, sig_a)["post"]}
        for r, f in fits.items():
            key = "E4_ridge_general_only" if np.isinf(r) else f"E5_ridge_rho{r:g}"
            est[key] = (f["bat_gen"] if np.isinf(r) else f["bat_high"]) if role == "batter" else (f["bow_gen"] if np.isinf(r) else f["bow_high"])
        wts = 2 / (1 / nAh[v] + 1 / nBh[v])
        obs = mBh[v]
        both = (n1 >= 15) & (n2 >= 15)
        relB = np.nan
        if both.sum() >= 15:
            r12 = np.corrcoef(m1[both], m2[both])[0, 1]
            relB = 2 * r12 / (1 + r12) if r12 > 0 else 0.0
        for name, pred in est.items():
            p = np.asarray(pred, float)[v]
            top = np.argsort(-p)[:10]
            rk = lambda z: pd.Series(z).rank().to_numpy()
            pear = _wcorr(p, obs, wts) if np.std(p) > 1e-9 else np.nan  # constant rating (tau2=0) -> undefined, not 0
            slope = np.polyfit(p, obs, 1, w=np.sqrt(wts))[0] if np.std(p) > 1e-9 else np.nan
            out.append(dict(split=s, role=role, estimator=name, n_players=int(v.sum()), mean_balls=float(nAh[v].mean()),
                            pearson=pear, spearman=float(np.corrcoef(rk(p), rk(obs))[0, 1]) if np.std(p) > 1e-9 else np.nan,
                            top10_lift=float(obs[top].mean() - obs.mean()), calib_slope=slope, rel_B=relB,
                            disattenuated=pear / np.sqrt(relB) if relB and relB > 0.02 else np.nan))
    return out


def tournament(rd: RidgeData, rhos=(3, 10, 30), alpha: float = 30.0, n_splits: int = 60, n_jobs: int = 4,
               min_balls: int = 30, seed: int = SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Every estimator is fitted on half A ONLY and judged on half B's observed HIGH value per ball.
    Returns (per-split rows, summary). Batters and bowlers are scored separately."""
    rows = Parallel(n_jobs=n_jobs)(delayed(_split)(rd, s, rhos, alpha, min_balls, seed) for s in range(n_splits))
    raw = pd.DataFrame([r for rr in rows for r in rr])
    summ = raw.groupby(["role", "estimator"]).agg(
        mean_pearson=("pearson", "mean"), sd_pearson=("pearson", "std"), p05=("pearson", lambda x: x.quantile(.05)),
        p95=("pearson", lambda x: x.quantile(.95)), mean_spearman=("spearman", "mean"), top10_lift=("top10_lift", "mean"),
        calib_slope=("calib_slope", "mean"), noise_ceiling_relB=("rel_B", "mean"), disattenuated=("disattenuated", "mean"),
        n_players=("n_players", "mean"), mean_balls=("mean_balls", "mean"), n_splits=("split", "nunique")).reset_index()
    return raw, summ.sort_values(["role", "mean_pearson"], ascending=[True, False])


# ----------------------------------------------------------------------------- bootstrap and final table
def bootstrap_ratings(rd: RidgeData, rho: float, alpha: float, reps: int = 300, n_jobs: int = 4, seed: int = SEED):
    """Match-level bootstrap that REFITS the ridge each time (hyper-parameters fixed). Returns (reps x nb, reps x nw)."""
    um, inv = np.unique(rd.mid, return_inverse=True)

    def one(r):
        rng = np.random.default_rng(seed + r)
        cnt = np.bincount(rng.integers(0, len(um), len(um)), minlength=len(um)).astype(float)
        f = fit_ridge(rd, rho, alpha, weights=rd.w * cnt[inv])
        return f["bat_high"], f["bow_high"]

    res = Parallel(n_jobs=n_jobs)(delayed(one)(r) for r in range(reps))
    return np.vstack([r[0] for r in res]), np.vstack([r[1] for r in res])


def summarize_boot(point: np.ndarray, boot: np.ndarray, eligible: np.ndarray, top: int = 10) -> pd.DataFrame:
    """80% interval, SD and P(top 10) where ranking is WITHIN the eligible pool in every replicate."""
    idx = np.where(eligible)[0]
    ranks = np.argsort(-boot[:, idx], axis=1)[:, :top]
    p_top = np.zeros(len(point))
    np.add.at(p_top, idx[ranks.ravel()], 1.0)
    return pd.DataFrame(dict(rating=point, boot_sd=boot.std(0, ddof=1), lo80=np.quantile(boot, .1, axis=0),
                             hi80=np.quantile(boot, .9, axis=0), P_top10=p_top / len(boot)))
