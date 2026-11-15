"""
selftest.py - smoke/integrity test for pressure_core.py on SIMULATED data (no real data needed).
Run:  python selftest.py            (about a minute)
It checks: no innings-1 leakage, WP calibration, ex-ante pressure separates outcomes (non-circular),
ridge/tournament/bootstrap all run, bootstrap uncertainty is realistic, P(top10) is not all 1.0.
Use it as the contract your real pipeline must satisfy.
"""
import time
import numpy as np
import pandas as pd
import pressure_core as pc

rng = np.random.default_rng(7)
N_MATCH, N_TEAM = 220, 8
OUT = ["0", "1", "2", "3", "4", "6", "W"]
BASE = {0: [.37, .32, .06, .01, .14, .06, .04], 1: [.40, .34, .07, .01, .10, .04, .04], 2: [.30, .27, .07, .01, .17, .12, .06]}
bat_skill = {t * 100 + i: rng.normal(0, .35) for t in range(1, N_TEAM + 1) for i in range(11)}
bow_skill = {t * 100 + i: rng.normal(0, .35) for t in range(1, N_TEAM + 1) for i in range(11)}
clutch = {p: rng.normal(0, .35) for p in bat_skill}


def sim_innings(mid, inn, bat_t, bow_t, target, venue_bias, pressure_fn):
    bats = [bat_t * 100 + i for i in range(11)]
    bowlers = [bow_t * 100 + i for i in range(6, 11)] + [bow_t * 100 + 5]
    rows, s, w, legal, nb, striker, ns, ibn = [], 0, 0, 0, 0, 0, 1, 0
    nxt = 2
    while legal < 120 and w < 10 and not (target is not None and s >= target):
        over = legal // 6 + 1
        bw = bowlers[(over - 1) % 5]
        st = bats[striker]
        pr = pressure_fn(inn, 120 - legal, w, s, target)
        phase = 0 if over <= 6 else (1 if over <= 15 else 2)
        p = np.array(BASE[phase]) * venue_bias
        th = bat_skill[st] - bow_skill[bw] + clutch[st] * pr
        p = p * np.exp(np.array([-.1 * th, 0, .1 * th, .1 * th, .3 * th, .35 * th, -.5 * th]))
        o = rng.choice(7, p=p / p.sum())
        ex, bat_r, tot, wk, dt, dp, lg = None, 0, 0, 0, None, None, 1
        u = rng.random()
        if u < .03:
            ex, tot, lg = "wide", 1, 0
        elif u < .038:
            ex, lg = "Overstep", 0
            bat_r = [0, 1, 4][rng.integers(0, 3)] if o != 6 else 0
            tot = bat_r + 1
        elif u < .053:
            ex, tot = "legbyes", 1
        elif o == 6:
            wk, dt, dp = 1, rng.choice(["Caught", "Bowled", "LBW", "RunOut"], p=[.6, .2, .1, .1]), st
            if dt == "RunOut" and rng.random() < .3:
                dp = bats[ns]
        else:
            bat_r = [0, 1, 2, 3, 4, 6][o]
            tot = bat_r
        ibn += 1
        rows.append(dict(match_id=mid, innings=inn, over=over, innings_ball_num=ibn, batting_team_id=bat_t, bowling_team_id=bow_t,
                         striker_id=st, bowler_id=bw, dismissed_player_id=dp, extras_type=ex, dismissal_type=dt, runs=bat_r,
                         runs_total=float(tot), legal=lg, wicket=wk))
        s += tot
        legal += lg
        if wk:
            w += 1
            if dp == st or dt != "RunOut":
                striker = nxt
            else:
                ns = nxt
            nxt += 1
            if nxt > 10:
                break
        elif lg and (bat_r % 2 == 1 or (ex == "legbyes")):
            striker, ns = ns, striker
        if lg and legal % 6 == 0:
            striker, ns = ns, striker
    return rows, s


def pressure_fn(inn, b, w, s, t):
    if inn == 2 and t is not None:
        return 1.0 if (b <= 36 and 0 < t - s <= 40) or w >= 6 else 0.0
    return 0.0


allrows, mrows = [], []
date0 = pd.Timestamp("2022-03-01")
for m in range(N_MATCH):
    t1, t2 = rng.choice(np.arange(1, N_TEAM + 1), 2, replace=False)
    venue = int(rng.integers(1, 6))
    grp = "IPL" if m % 2 == 0 else "T20I"
    r1, s1 = sim_innings(m, 1, t1, t2, None, 1.0 + .03 * venue, pressure_fn)
    r2, s2 = sim_innings(m, 2, t2, t1, s1 + 1, 1.0 + .03 * venue, pressure_fn)
    win = t2 if s2 >= s1 + 1 else t1
    for r in r1 + r2:
        r.update(batting_won=int(r["batting_team_id"] == win), venue_id=venue, comp_group=grp,
                 match_date=date0 + pd.Timedelta(days=4 * m))
    allrows += r1 + r2
    mrows.append(dict(match_id=m, match_date=date0 + pd.Timedelta(days=4 * m), home_team_id=t1, away_team_id=t2,
                      win_team_id=win, pool="IPL" if grp == "IPL" else "NAT"))
df, matches = pd.DataFrame(allrows), pd.DataFrame(mrows)
df["season_year"] = df.match_date.dt.year
print(f"simulated {len(df):,} deliveries in {N_MATCH} matches")

t0 = time.time()
df = pc.add_state(df)
df["par"] = df.match_id.map(pc.venue_par(df))
elo = pc.pre_match_elo(matches)
df = pc.attach_elo(df, elo, matches.set_index("match_id")["home_team_id"])
df["w_opp"] = pc.opp_weight(df, a_team_ids=set())
df["w_time"] = pc.time_weight(df.match_date)
rt = pc.ResourceTable().fit(df)
df["res"] = rt.lookup(df.b, df.w_before)
assert (df.loc[df.innings == 1, "target"].isna()).all(), "LEAK: innings-1 rows must not have a target"
folds = pc.assign_folds(df.match_id)

wpm = pc.WPModel(rt, folds, n_jobs=1)
df["wp_before"] = wpm.fit(df)
print(pc.wp_report(df).round(4).to_string(index=False))
df = pc.chain_wp(df)
assert abs(df.dWP.mean()) < 0.01, "mean dWP should be ~0"

probs = pc.outcome_probs(df)
df["LI"] = pc.expected_leverage(df, wpm, probs)
df = pc.pressure_index(df, rt)
hl = pc.high_low_table(df)
print(hl.round(4).to_string(index=False))
assert hl.loc[hl.set == "HIGH", "mean_abs_dWP"].iloc[0] > 1.5 * hl.loc[hl.set == "LOW", "mean_abs_dWP"].iloc[0], \
    "ex-ante HIGH should still show larger realised swings"
corr_li = np.corrcoef(df.LI, df.dWP.abs())[0, 1]
print(f"corr(expected LI, realised |dWP|) = {corr_li:.3f}  (positive but < 1: LI is NOT the realised swing)")

df = pc.fit_expected(df, folds, n_jobs=1)
K = pc.estimate_K(df)
print({k: round(v["K"], 2) for k, v in K.items()}, "kappa_run(all) =", round(K["all"]["kappa_run"], 4))
df = pc.add_ball_value(df, K)
df = pc.attribution(df)
rd = pc.RidgeData(df, folds)
print("ridge rows", len(rd.y), "batters", rd.nb, "bowlers", rd.nw)

cv = pc.cv_hyper(rd, alphas=[10, 50], rhos=[3, 30, np.inf], n_splits=3, n_jobs=1)
print(cv.round(5).to_string(index=False))
best = cv.iloc[0]
raw, summ = pc.tournament(rd, rhos=(3, 30), alpha=float(best.alpha_g), n_splits=6, n_jobs=1, min_balls=20)
print(summ.round(3).to_string(index=False))
assert not (summ[summ.role == "batter"].mean_pearson.round(6).values == summ[summ.role == "bowler"].mean_pearson.round(6).values).all()

rho = float(best.rho)
f = pc.fit_ridge(rd, rho, float(best.alpha_g))
bb, bw = pc.bootstrap_ratings(rd, rho, float(best.alpha_g), reps=12, n_jobs=1)
nb_h = np.bincount(rd.bat_col[(rd.h == 1) & (rd.bat_col >= 0)], minlength=rd.nb)
elig = nb_h >= 40
sm = pc.summarize_boot(f["bat_high"], bb, elig)
sm["n_HIGH"] = nb_h
top = sm[elig].sort_values("rating", ascending=False).head(10)
print(top.round(4).to_string())
assert 0 < sm.loc[elig, "P_top10"].mean() < 1 and (sm.loc[elig, "P_top10"] < 1).any(), "P(top10) must not be all 1.0"
true_bat = np.array([bat_skill[p] for p in rd.bat_ids])
print("corr(estimated batter rating, true planted skill) =", round(np.corrcoef(f["bat_gen"], true_bat)[0, 1], 3))
rel = pc.reliability_diagnostics(df.loc[df.bat_ok & (df.set == "HIGH"), "striker_id"].to_numpy(), df.loc[df.bat_ok & (df.set == "HIGH"), "y"].to_numpy(), n_min=20)
print({k: round(float(v), 4) for k, v in rel.items()})
print(f"ALL CHECKS PASSED in {time.time() - t0:.0f}s")

# --- estimator contract: between-player variance must be recovered (regression test for the old biased estimator)
for true_sd in (0.05, 0.10, 0.20):
    r = np.random.default_rng(3)
    P = 300
    n = r.integers(40, 300, P)
    mu = r.normal(0, true_sd, P)
    pl = np.repeat(np.arange(P), n)
    v = np.concatenate([r.normal(mu[i], 2.1, n[i]) for i in range(P)])
    est = pc.reliability_diagnostics(pl, v, 30)["tau_per_ball"]
    assert abs(est - true_sd) < 0.03, f"tau estimator broken: true {true_sd}, got {est:.3f}"
f0 = pc.fit_ridge(rd, rho, float(best.alpha_g))
print("HIGH offset (runs/ball) absorbed by the unpenalised column:", round(f0["high_offset"], 4))
print("SELFTEST EXTENDED CHECKS PASSED")
