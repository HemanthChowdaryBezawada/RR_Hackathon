# SupeRR Pressure Index: Methodology & Slide Asset Reference

This directory contains publication-ready figures, quantitative tables, and empirical facts generated directly from the frozen tournament pipeline (`outputs/final/`).

## Figures Map (`methodology/assets/figures/`)

| File | Title | Recommended Slide | Key Visual Insight | Exact Metric Callouts |
| :--- | :--- | :--- | :--- | :--- |
| `F02_high_vs_low.png` | High vs Low Pressure Volatility | **Slide 5: Pressure Index Definition** | Demonstrates empirical divergence in outcome volatility across $\Pi$ tiers. | HIGH mean $|\Delta \text{WP}| = 4.16\%$ (4x MED $1.19\%$, 20x LOW $0.20\%$). |
| `F03_pi_heatmap.png` | Average Pressure Index Heatmap | **Slide 6: Dynamic Match Leverage** | 20 overs $\times$ 10 wickets matrix showing exponential leverage concentration. | Peak leverage concentrated in overs 16–20 with $\le 4$ wickets in hand ($\Pi > 0.85$). |
| `F04_high_share_by_over.png` | High Pressure Distribution by Phase | **Slide 6: Dynamic Match Leverage** | Shows proportion of balls classified as HIGH by match over. | Powerplay: ~12–15%; Middle overs: ~20–25%; Death overs: >65% HIGH balls. |
| `F05_wp_calibration.png` | Win Probability Model Calibration | **Slide 4: Foundational WP Architecture** | Reliability diagram showing predicted win probability vs actual outcome frequency. | Innings 2: AUC $0.860$, Brier $0.1515$, ECE $1.12\%$ ($0.0112$), Log-loss $0.4647$. |
| `F06_match_trace_1.png` | Real Match Leverage Timeline #1 | **Slide 7: Micro-Level Ball Valuation** | Ball-by-ball trace of high-tension chase with wicket spikes and swing events. | Captures inflection deliveries where $\Delta \text{WP} > 15\%$ per ball. |
| `F06_match_trace_2.png` | Real Match Leverage Timeline #2 | **Slide 7: Micro-Level Ball Valuation** | Secondary case study demonstrating low-leverage dead rubber vs crunch chase. | Verifies non-circularity: pressure elevated before execution, not after. |
| `F07_tournament.png` | 100-Split Estimator Tournament | **Slide 8: Estimator Tournament Selection** | Out-of-sample Pearson $r$ distributions across 6 candidate model classes. | Batters: E3_EB wins ($r=0.246$). Bowlers: E5_ridge ($\rho=3$) wins ($r=0.252$). |
| `F08_forest_batters.png` | Forest Plot: Top 25 Batters | **Slide 10: Top-10 Batters & Tiers** | Horizontal 80% intervals (bootstrap) with posterior means and $P(\text{Top } 10)$ pills. | Abhishek Sharma (+29.0, 98.3%), Tim David (+24.9, 94.7%), SKY (+23.5, 95.0%), Phil Salt (+21.5, 87.0%). |
| `F09_forest_bowlers.png` | Forest Plot: Top 25 Bowlers | **Slide 11: Top-10 Bowlers & Tiers** | Horizontal 80% intervals (bootstrap) with posterior means and $P(\text{Top } 10)$ pills. | Sunil Narine (+29.1, 100%), Bumrah (+27.2, 96%), Varun Chakravarthy (+20.2, 82%). |
| `F10_beta_vs_delta.png` | Baseline ($\beta$) vs Pressure Shift ($\delta$) | **Slide 9: Bayesian Decomposition** | 2D scatter plot showing that clutch is predominantly elite general skill ($\beta$). | True pressure shift ($\delta$) has wide uncertainty; $\beta$ drives 80%+ of total variance. |
| `F11_p_top10.png` | Posterior $P(\text{Top } 10)$ Distribution | **Slide 12: Decision Rigor & Parity** | Quantifies probability mass in Top 10 across 300 bootstrap iterations. | Only 2–3 players per discipline have $P(\text{Top } 10) > 80\%$; the rest form statistical ties. |
| `F12_sensitivity.png` | Hyperparameter Sensitivity Analysis | **Slide 13: Sensitivity & Robustness** | Kendall's $\tau$ rank correlation across $\Pi$ thresholds, decay, and cohort rules. | Top-10 rank order is robust ($\tau = 0.78$ to $1.00$ across standard perturbations). |
| `F13_extras_reconstruction.png` | Score Reconstruction & Zero Leakage | **Slide 3: Data Integrity & Ingestion** | Reconciliation of extras, run reconstruction, and ex-ante match states. | Excludes corrupt/retire-out anomalies; guarantees strict temporal ex-ante evaluation. |
| `F14_data_funnel.png` | Player Qualification Attrition Funnel | **Slide 3: Data Integrity & Eligibility** | Step-by-step reduction from tracked player pool down to qualified cohorts. | 888 batters $\to$ 91 qualified batters; 647 bowlers $\to$ 104 qualified bowlers. |
| `F16a_high_vs_low_batters.png` | Batter Profiles: High vs Low Pressure | **Slide 5 / 10: Batter Clutch Divergence** | Run rate and dismissal rate shifts between HIGH and LOW pressure for top batters. | Demonstrates individual scoring rate compression and survivability under clutch conditions. |
| `F16b_high_vs_low_bowlers.png` | Bowler Profiles: High vs Low Pressure | **Slide 5 / 11: Bowler Clutch Divergence** | Economy rate and strike rate shifts between HIGH and LOW pressure for top bowlers. | Isolates elite bowlers whose economy remains suppressed even in maximum-leverage phases. |

---

## Tables Map (`methodology/assets/tables/`)

- `T01_top10_batters.csv`: Final Top 10 Batters (Rank, Player, Teams, Rating, 80% CI, P(top 10), HIGH balls, Last Match Date).
- `T02_top10_bowlers.csv`: Final Top 10 Bowlers (Rank, Player, Teams, Rating, 80% CI, P(top 10), HIGH balls, Last Match Date).
- `T03_tournament.csv`: Detailed performance of all 7 estimators across 100 cross-validation splits (mean Pearson, Spearman, top-10 lift, noise ceiling).
- `T04_sensitivity.csv`: Stress-test results across rounded ratings, base-only, PI percentiles (q0.70, q0.75, q0.80), time decay half-lives, and IPL-only.

---

## Key Model Metrics Summary

- **Database**: 805 usable matches, 192,156 usable balls (2022–2026: 352 IPL, 425 T20I, 28 T20 other).
- **WP Calibration**: Innings 2 AUC = 0.860, Brier = 0.1515, Log-loss = 0.4647, ECE = 1.12%.
- **Pressure Index**: $\Pi = 0.60 \times \text{Leverage} + 0.25 \times \text{Closeness} + 0.15 \times \text{Scarcity}$. HIGH cutoff = Top 25% ($\Pi \ge 0.70$).
- **Batters Winner**: Empirical Bayes General ($r = 0.246$).
- **Bowlers Winner**: Ridge Regression with $\rho = 3$ ($r = 0.252$).
- **Eligibility**: $\ge 150$ HIGH balls for Batters, $\ge 120$ HIGH balls for Bowlers, active within 365 days, $\ge 12$ match situations, $\ge 2$ seasons. Pakistan excluded, Bangladesh included.
