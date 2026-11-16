# SupeRR Lab: Pressure Index Analytics Engine

An institutional-grade, static, build-free analytics dashboard served directly from `docs/` for GitHub Pages. It visualizes empirical Bayes player ratings, 80% intervals (bootstrap), pre-ball pressure taxonomy, hyperparameter sensitivity, and hold-out validation diagnostics.

---

## 1. Executive Purpose & Architecture

The **Pressure Index (PI)** engine quantifies pre-delivery match leverage independently of player execution. Using pre-delivery game state (leverage potential, win probability proximity to 50:50, and resource scarcity), deliveries are categorized into **HIGH-pressure** situations (top 25% of PI). Player clutch performance is evaluated via hierarchical empirical Bayes shrinkage and out-of-fold cross-validation.

There is **ONE official ranking list**. Pakistan and Pakistan A players are excluded (not permitted in the IPL), and players without a tracked match in the last 365 days are filtered out. Bangladeshi players are included as eligible IPL participants.

---

## 2. Interpretation Guide

- **Metric Units**:
  - `rating`, `lo80`, `hi80`, `beta`, `delta`: Calibrated runs delivered above contextual match expectation per 100 high-pressure deliveries.
  - `wpa`: Win-probability added points per 100 deliveries.
- **80% Interval (Bootstrap) Range (`[lo80, hi80]`)**:
  - Computed via 300 match-level bootstrap iterations. Whiskers demarcate where the true player latent skill lies with an 80% interval (bootstrap). Overlapping whiskers indicate statistical parity rather than deterministic separation.
- **Top 10 Probability ($P(\text{top 10})$)**:
  - The share of bootstrap resamples in which a player finishes inside the tournament top 10. Ranks with $P(\text{top 10}) \ge 80\%$ demonstrate high certainty, while $P(\text{top 10}) < 50\%$ indicates statistical ties.
- **Decomposition**:
  - $\beta$ (**Baseline / Usual Level**): Player's general underlying ability across all match situations.
  - $\delta$ (**Pressure Shift**): The specific clutch elevation or suppression attributable to high-leverage deliveries ($\text{Rating} = \beta + \delta$).

---

## 3. Data Refresh Pipeline

To regenerate all model tables, JSON datasets, and report assets:

```bash
# 1. Regenerate model tables and freeze rankings
.venv/bin/python pressure_model/src/final_outputs.py

# 2. Export validated JSON schema to dashboard
.venv/bin/python export_dashboard_data.py --src outputs/final --out docs/data --matches data_pack/matches.csv --teams data_pack/teams.csv

# 3. Regenerate all report figures
.venv/bin/python make_report_assets.py --src outputs/final --out report_assets
```

---

## 4. Verification & Testing

Every commit and data refresh must pass all three test gates:

```bash
# 1. Pre-submission integrity gate (zero fake values, no alternate-list remnants, data rules verified)
.venv/bin/python check_dashboard.py --docs docs

# 2. JavaScript syntax integrity
node --check docs/assets/js/data.js docs/assets/js/format.js docs/assets/js/charts.js docs/assets/js/main.js docs/assets/js/screens/*.js

# 3. Playwright end-to-end tests (console errors, data binding, routing, search, CSV export)
npx playwright test
```

### Lighthouse Audit Scores (Desktop)
- **Overview**: Performance: **95**, Accessibility: **96**, Best Practices: **96**
- **Rankings**: Performance: **96**, Accessibility: **96**, Best Practices: **96**

---

## 5. Analytical Limitations & Governance

1. **Pressure-Specific Variance**: Pressure-specific elevation beyond general talent baseline is statistically small and difficult to isolate; individual outcomes in crunch situations are predominantly governed by established baseline ability.
2. **Statistical Ties in Chasing Tier**: Outside the top 3–5 ranks, 80% intervals (bootstrap) exhibit extensive mutual overlap. Ranks 7–12 represent statistical ties where exact ordering is subject to sampling variance.
3. **Extras Reconstruction**: Bye and leg-bye run attribution uses post-hoc trajectory inference rather than explicit tracking telemetry.
4. **Asymmetric Win-Probability Horizon**: Innings-1 win-probability models naturally possess lower discrimination (AUC ~0.66) than Innings-2 chase models (AUC ~0.86) due to unresolved target scores and first-innings pitch trajectory variance.

---

## 6. GitHub Pages Deployment

1. Commit and push the repository:
   ```bash
   git add .
   git commit -m "Deploy SupeRR Intelligence Engine dashboard"
   git push origin main
   ```
2. In GitHub repository: **Settings → Pages → Build and deployment**.
3. Source: **Deploy from a branch**.
4. Branch: `main`, folder: `/docs`.
5. Once deployed, the dashboard is accessible at your repository's GitHub Pages URL (e.g. `https://<username>.github.io/<repo>/`).
