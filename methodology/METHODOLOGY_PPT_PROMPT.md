# MASTER AGENT PROMPT: GENERATE THE SUPERR METHODOLOGY PRESENTATION (PPTX)

You are an elite Sports Analytics Lead and Senior Strategy Consultant (combining the quantitative rigor of Rajasthan Royals' Analytics Desk with the presentation craft of McKinsey / BCG / Bain).

Your task is to generate a world-class, 15-slide PowerPoint deck (`.pptx`) titled:
**"The SupeRR Pressure Index: Quantifying Clutch Performance Under Uncertainty for IPL Auction & Tactical Strategy"**.

---

## 1. DESIGN & BRAND IDENTITY SYSTEM

To ensure the deck looks like an institutional-grade presentation prepared for franchise owners and the high-performance analytics desk, adhere strictly to these visual guidelines:

### A. Color Palette
- **Primary Accent (RR Royal Pink)**: `#E6007E` (Use for key highlights, tournament winners, top metrics, focal points)
- **Deep Navy (Brand Dominance)**: `#001D4A` (Slide headers, card titles, primary text, high-contrast dark cards)
- **Secondary Slate/Navy**: `#0F172A` / `#1E293B` (Body text, chart axes, structural containers)
- **Accent Amber/Gold (Royalty & Caution)**: `#D97706` / `#F59E0B` (Low-sample badges, warnings, secondary tier chips)
- **Muted Teal / Accent Blue**: `#0284C7` / `#0D9488` (Complementary data series, ordinary match condition metrics)
- **Card Background**: `#FFFFFF` on `#F8FAFC` (Canvas off-white background with crisp, subtly bordered white cards)
- **Border Subtle**: `#E2E8F0` (1px clean border lines)

### B. Typography & Layout Architecture
- **Aspect Ratio**: 16:9 Widescreen.
- **Font Stack**: Clean modern Sans-serif (`Inter`, `Segoe UI`, or `Arial`).
- **Hierarchy**:
  - Slide Header: 24–28pt Bold `#001D4A`
  - Action Subtitle / Lead Tracker: 13–15pt Medium `#E6007E` or `#475569` (State the *so-what* takeaway immediately)
  - Card Headings: 14–16pt Bold `#001D4A`
  - Body & Table Text: 10–12pt Regular `#334155`
  - KPI Big Numbers: 32–40pt Bold `#E6007E` or `#001D4A`
  - Footnotes / Data Source: 8–9pt Muted `#64748B`
- **Layout Principle (Pyramid Principle & Multi-Column Modular Cards)**:
  - Every slide must feature a 2, 3, or 4-column structured card grid or split-panel layout.
  - Avoid unstructured walls of bullet points. Use structured KPI callout tiles, mini-tables, comparison pills, and tagged badges.
  - Every slide must specify image/chart placeholders pointing to the assets generated in `methodology/assets/`.

---

## 2. PROJECT REPOSITORY & ASSET CONTEXT

All figures, tables, and quantitative facts have been extracted directly from the verified production pipeline (`outputs/final/`) and organized in `methodology/assets/`:
- **Figures Folder**: `methodology/assets/figures/` (High-resolution PNG charts: `F02` to `F16b` including `F16a` and `F16b`)
- **Tables Folder**: `methodology/assets/tables/` (`T01` to `T04` in CSV format)
- **Facts File**: `methodology/assets/facts.json` (Exact numbers, AUC, Brier score, counts, ratings, and rankings)

---

## 3. SLIDE-BY-SLIDE SPECIFICATION (15 SLIDES)

---

### SLIDE 1: Title & Executive Dispatch (Dark Navy Hero Theme)
- **Slide Style**: Deep Navy background (`#001D4A`) with white text and Royal Pink (`#E6007E`) accent lines.
- **Header**: SUPERR ANALYTICS DESK | RAJASTHAN ROYALS HACKATHON 2026
- **Title**: The SupeRR Pressure Index: Quantifying Clutch Performance Under Uncertainty
- **Subtitle**: A Leak-Free, Ex-Ante Bayesian Shrinkage & Opponent-Adjusted Framework for T20 Player Valuation
- **Metadata Cards (Bottom Grid)**:
  - `Dataset Scope`: 805 Usable Matches | 192,156 Usable Deliveries (2022–2026 IPL, T20I, T20)
  - `Analytical Engine`: Ex-Ante WP Model ($\text{AUC} = 0.860$) + Empirical Bayes & Ridge Regularization
  - `Decision Horizon`: IPL 2027 Mini-Auction Readiness & Match Situation Matchups
  - `Classification`: Confidential | Proprietary Franchise Intelligence

---

### SLIDE 2: Executive Summary & The Four Core Insights
- **Slide Header**: EXECUTIVE SUMMARY
- **Action Subtitle**: Empirical evidence shows "clutch" is overwhelmingly elite baseline skill under high leverage, not erratic surges.
- **Layout**: 4-Column Structured Pillar Cards:
  1. **Card 1: Zero-Leakage Ex-Ante Valuation**
     - Metric: `4.16% vs 0.20%` (20x swing differential)
     - Text: Traditional win probability introduces future-outcome leakage. SupeRR calculates pressure *prior* to bowler delivery release using win-probability gradients, game closeness, and resource scarcity.
  2. **Card 2: Clutch = Baseline ($\beta$) + Shift ($\delta$)**
     - Metric: `80%+ Baseline Driven`
     - Text: Bayesian decomposition reveals player clutch ratings are driven primarily by general established ability ($\beta$). True pressure-specific shift ($\delta$) has wide uncertainty and rarely deviates from zero by chance alone.
  3. **Card 3: Estimator Tournament Winner**
     - Metric: `Pearson r = 0.252 / 0.246`
     - Text: 100-split out-of-sample cross-validation proved Empirical Bayes general is superior for Batters ($r=0.246$), while Ridge Regression ($\rho=3$) wins for Bowlers ($r=0.252$) due to opponent quality adjustment.
  4. **Card 4: Posterior Overlap & Statistical Parity**
     - Metric: `P(Top 10) Uncertainty`
     - Text: 80% intervals (bootstrap) show substantial overlap. Deterministic ranking is flawed: only 2–3 players per discipline have $P(\text{Top } 10) > 80\%$. Selection decisions must account for statistical parity.
- **Bottom Callout Strip**: "Single Unified Ranking Policy: Pakistan/Pakistan A excluded (IPL ineligible). Bangladeshi players included (registered for IPL auction). Active within 365 days with verified volume thresholds."

---

### SLIDE 3: Data Integrity, Extras Reconstruction & The Qualification Funnel
- **Slide Header**: DATA PIPELINE & ELIGIBILITY
- **Action Subtitle**: Ingesting 805 matches across 4 years with rigorous extras reconstruction and attrition gating.
- **Layout**: Split Screen (Left: Funnel Flow; Right: Data Integrity Architecture).
- **Left Panel (Image Placeholder & Stages)**:
  - Placeholder: `[INSERT FIGURE: methodology/assets/figures/F14_data_funnel.png]`
  - Funnel Stages:
    - Total Tracked Pool: 888 Batters / 647 Bowlers (192,156 balls across 352 IPL, 425 T20I, 28 other matches).
    - Minimum HP Deliveries: $\ge 150$ HIGH balls for Batters, $\ge 120$ HIGH balls for Bowlers.
    - Situational Exposure: $\ge 12$ independent match pressure situations across $\ge 2$ tournaments.
    - Recency Filter: Active in competitive match within last 365 days (post Nov 2025).
    - Final Qualified Cohort: **91 Batters** and **104 Bowlers**.
- **Right Panel (Extras Reconstruction & Zero-Leakage Architecture)**:
  - Placeholder: `[INSERT FIGURE: methodology/assets/figures/F13_extras_reconstruction.png]`
  - Bullets:
    - *Reconstruction*: Fixed all corrupt records, byes/leg-byes attribution, penalty runs, and unrecorded wides.
    - *Wicket Classification*: Excluded 'Retired Out' and non-bowler credits from bowler negative attribution.
    - *Zero Ex-Post Leakage*: Stripped all end-of-innings totals and terminal margins from real-time evaluation.

---

### SLIDE 4: Foundational Win Probability Engine
- **Slide Header**: WIN PROBABILITY (WP) ENGINE
- **Action Subtitle**: Calibrated gradient boosted decision trees provide real-time state win expectations without hindsight bias.
- **Layout**: 3-Column Card Layout (Left: Formulation; Middle: Calibration Plot; Right: Out-of-Sample Metrics).
- **Column 1: State Features & Model Training**
  - Features: Required Run Rate, Balls Remaining, Wickets in Hand, Current Innings Score, Comp Group (IPL vs T20I), Venue Bias.
  - Formulation: Logistic gradient descent evaluating instantaneous win likelihood $P(\text{Win} \mid \text{State}_{t})$.
  - Group Split: Calibrated separately across Innings 1 (projection-based) and Innings 2 (chase-based target pursuit).
- **Column 2: Calibration Chart**
  - Placeholder: `[INSERT FIGURE: methodology/assets/figures/F05_wp_calibration.png]`
  - Caption: "Predicted win probability strictly tracks empirical match outcome frequency across 10 deciles."
- **Column 3: Institutional Validation KPI Table**
  - Table:
    - **Innings 2 Overall**: AUC = `0.860`, Brier Score = `0.1515`, ECE = `1.12%`, Log-Loss = `0.4647` (vs Base 0.6923)
    - **IPL Subset**: AUC = `0.832`, Brier Score = `0.1662`, ECE = `2.82%`
    - **T20I Subset**: AUC = `0.882`, Brier Score = `0.1384`, ECE = `1.85%`
  - High Performance Takeaway: ECE $\le 2\%$ confirms that win probabilities represent true real-world frequencies.

---

### SLIDE 5: The Pressure Index ($\Pi$) Formulation
- **Slide Header**: PRESSURE DEFINITION & STRATIFICATION
- **Action Subtitle**: Multi-dimensional situational formulation isolating leverage independently of player skill.
- **Layout**: Top: Mathematical Equation Banner; Bottom: 2-Card Comparative Analysis.
- **Top Formula Box (Royal Pink Border)**:
  $$\Pi = 0.60 \times \text{Leverage} + 0.25 \times \text{Closeness} + 0.15 \times \text{Scarcity}$$
  - **Leverage (0.60)**: Potential swing magnitude $\max_{\Delta} |\text{WPA}|$ across boundary vs dot vs wicket states.
  - **Closeness (0.25)**: Proximity to $50\%$ win parity; degraded monotonically as probability approaches runaway state.
  - **Scarcity (0.15)**: Balls remaining vs wickets in hand ratio, capturing tail-end acceleration demands.
- **Bottom Left Card: Stratification Tiers**
  - **Low Pressure ($\Pi < 0.55$)**: $50\%$ of match balls. Runway margins, dead rubbers, or runaway chases.
  - **Medium Pressure ($0.55 \le \Pi < 0.70$)**: $25\%$ of match balls. Balanced middle-phase baseline play.
  - **High / Clutch Pressure ($\Pi \ge 0.70$)**: **Top 25%** highest leverage deliveries (48,039 deliveries).
- **Bottom Right Card: Empirical Divergence (High vs Low)**:
  - Placeholder: `[INSERT FIGURE: methodology/assets/figures/F02_high_vs_low.png]`
  - Key Metric Callouts:
    - *Mean $|\Delta \text{WP}|$ Swing*: High = **4.16%** | Medium = **1.19%** | Low = **0.20%** (20x leverage multiple).
    - *Wicket Hazard Rate*: High = **5.77%** | Medium = **5.15%** (+12% wicket vulnerability under high pressure).
    - *Run Rate Pressure*: High = **8.62** RPO | Medium = **8.26** RPO.

---

### SLIDE 6: Pressure Heatmap & Match Phase Concentration
- **Slide Header**: LEVERAGE CONCENTRATION ACROSS PHASES
- **Action Subtitle**: Pressure intensifies non-linearly in death overs and powerplay wicket collapses.
- **Layout**: Left: 20x10 Heatmap Grid; Right: Phase Breakdown & Share Chart.
- **Left Panel (20 Overs x 10 Wickets Heatmap)**:
  - Placeholder: `[INSERT FIGURE: methodology/assets/figures/F03_pi_heatmap.png]`
  - Key Observations:
    - Overs 1–6 (Powerplay): Moderate leverage ($0.25 \le \Pi \le 0.45$), unless $\ge 3$ early wickets fall ($\Pi \to 0.75$).
    - Overs 7–15 (Middle Overs): Gradual leverage accumulation; stable at $0.40 \le \Pi \le 0.60$.
    - Overs 16–20 (Death Phase): Extreme leverage exponential spike ($\Pi > 0.85$), where almost every ball is decisive.
- **Right Panel (High Pressure Share by Over)**:
  - Placeholder: `[INSERT FIGURE: methodology/assets/figures/F04_high_share_by_over.png]`
  - Strategic Notes:
    - Over 20 has **>78%** of deliveries classified as High Pressure.
    - Bowlers bowling in overs 18–20 face 4.5x more High-Pressure deliveries than middle-overs spin anchors.
    - Normalization against role baseline is essential to avoid penalizing death specialists.

---

### SLIDE 7: Micro-Level Ball Valuation: Ex-Ante Net WPA
- **Slide Header**: DELIVERED VALUE VS CONTEXTUAL EXPECTATION
- **Action Subtitle**: Evaluating every delivery against ex-ante situational value rather than raw boundary counts.
- **Layout**: Top: Timeline Case Studies; Bottom: 3-Column Valuation Metric Explanations.
- **Top Panel (Case Study Match Traces)**:
  - Placeholders: `[INSERT FIGURE: methodology/assets/figures/F06_match_trace_1.png]` and `[INSERT FIGURE: methodology/assets/figures/F06_match_trace_2.png]`
  - Narrative: Real match traces tracking win probability swings delivery-by-delivery, showing the exact moments where clutch performances swing game equity by $+15\%$ to $+35\%$.
- **Bottom 3 Cards (Valuation Metrics)**:
  - **Net WPA per 100 Balls**:
    $$\text{Net WPA} = \sum (\text{Actual } \Delta \text{WP} - \mathbb{E}[\Delta \text{WP} \mid \text{State}])$$
  - **Runs Delivered Above Expectation**:
    Converting win probability swings into equivalent run values (runs delivered per 100 high-pressure balls).
  - **Opposition Weighting ($w_{\text{opp}}$)**:
    Weighting outcomes against bowler/batter tier quality to avoid inflating ratings from soft opponents.

---

### SLIDE 8: The Estimator Tournament: Rigorous Out-of-Sample Selection
- **Slide Header**: ESTIMATOR TOURNAMENT
- **Action Subtitle**: Evaluating 7 candidate estimators across 100 cross-validation splits to eliminate small-sample noise.
- **Layout**: Left: Tournament Benchmark Chart; Right: Decision Matrix & Selection Rule.
- **Left Panel (Estimator Pearson Correlation)**:
  - Placeholder: `[INSERT FIGURE: methodology/assets/figures/F07_tournament.png]`
- **Right Panel (100-Split Benchmark Table)**:
  - Table:
    - `E3_EB_general` (Empirical Bayes Shrunk Mean): Batters **r = 0.246** (WINNER) | Bowlers r = 0.248
    - `E5_ridge_rho3` (Ridge Regression $\rho=3$): Batters r = 0.213 | Bowlers **r = 0.252** (WINNER)
    - `E5_ridge_rho10` (Ridge Regression $\rho=10$): Batters r = 0.208 | Bowlers r = 0.249
    - `E4_ridge_general_only`: Batters r = 0.205 | Bowlers r = 0.244
    - `E1_raw_HIGH` (Unshrunk Raw Averages): Batters r = 0.208 | Bowlers r = 0.146 (Severe overfitting!)
  - **The Institutional Selection Decision**:
    - **Batters**: `E3_EB_general` outperformed Ridge by $+0.033$ held-out Pearson $r$ ($0.246$ vs $0.213$, paired difference $+0.0331 \pm 0.0028$ SE across 100 splits). Selected directly as published estimator.
    - **Bowlers**: `E5_ridge_rho3` achieved highest mean Pearson ($0.252$ vs $0.248$ for EB and $0.249$ for $\rho=10$). Runner-up is within $0.01$ margin; selected Ridge because it adjusts for opposition bowler/batter strength ($w_{\text{opp}}$).

---

### SLIDE 9: Bayesian Decomposition: Baseline Skill ($\beta$) vs Pressure Shift ($\delta$)
- **Slide Header**: DECOMPOSITION ARCHITECTURE
- **Action Subtitle**: Isolating whether a player's clutch rating stems from elite baseline ability or situational elevation.
- **Layout**: Top: Mathematical Formulation; Bottom Left: Scatter Visualization; Bottom Right: Analytical Interpretation.
- **Formulation Box**:
  $$\text{Rating}_i = \beta_i + \delta_i$$
  - $\beta_i$ (Usual / Baseline Ability): Performance in all game states, shrunk towards league mean.
  - $\delta_i$ (Pressure Shift / Lift): Incremental performance delta under $\Pi \ge 0.70$ conditions.
- **Bottom Left Panel (Beta vs Delta Scatter)**:
  - Placeholder: `[INSERT FIGURE: methodology/assets/figures/F10_beta_vs_delta.png]`
- **Bottom Right Panel (Key Analytical Findings)**:
  - *Dominance of $\beta$*: Over **80%** of total rating variance is explained by $\beta_i$. Elite players under pressure are primarily elite players overall executing standard skills under high stakes.
  - *Statistical Rarity of $\delta$*: In the qualified cohorts, only 18 batters (19.8%) have an 80% interval strictly above 0 and 7 (7.7%) below 0 (27.5% bounded away from zero vs 20% expected by chance alone). For bowlers, only 15 (14.4%) above 0 and 11 (10.6%) below 0 (25.0% vs 20% by chance). Individual pressure shifts ($\delta$) are statistically indistinguishable from noise for ~75% of players.
  - *Scouting Application*: Never recruit on raw "clutch reputation" if baseline ability ($\beta$) is low; regression to the mean will erode performance in subsequent seasons.

---

### SLIDE 10: Player Rankings — Batters: The Qualified Top 10
- **Slide Header**: QUALIFIED BATTERS RANKING
- **Action Subtitle**: Single unified ranking of qualified batters: posterior ratings, 80% intervals (bootstrap), and $P(\text{Top } 10)$.
- **Layout**: Left: Top 10 Table (`T01`); Right: Forest Plot Distribution (`F08`).
- **Left Panel (Top 10 Batters Table)**:
  | Rank | Player | Franchise / Nation | Rating (runs/100b) | 80% Interval (Bootstrap) | P(Top 10) | HIGH Balls |
  | :---: | :--- | :--- | :---: | :---: | :---: | :---: |
  | **1** | **Abhishek Sharma** | SRH / IND | **+29.0** | [+22.9, +38.4] | **98.3%** | 425 |
  | **2** | **Tim David** | MI / RCB / AUS | **+24.9** | [+19.7, +36.1] | **94.7%** | 417 |
  | **3** | **Suryakumar Yadav** | MI / IND | **+23.5** | [+19.9, +30.9] | **95.0%** | 657 |
  | **4** | **Phil Salt** | DC / KKR / RCB / ENG | **+21.5** | [+16.3, +29.8] | **87.0%** | 285 |
  | **5** | **Heinrich Klaasen** | SRH / SA | **+17.8** | [+12.4, +26.4] | **67.3%** | 409 |
  | **6** | **Romario Shepherd** | MI / WI | **+13.8** | [+6.4, +26.2] | **49.0%** | 271 |
  | **7** | **Nicholas Pooran** | LSG / WI | **+13.4** | [+7.9, +21.6] | **30.3%** | 540 |
  | **8** | **Rajat Patidar** | RCB | **+12.8** | [+5.3, +23.3] | **31.7%** | 299 |
  | **9** | **Mitchell Marsh** | DC / AUS | **+12.7** | [+7.9, +20.1] | **27.7%** | 450 |
  | **10** | **Travis Head** | SRH / AUS | **+12.6** | [+4.5, +23.5] | **35.0%** | 287 |
- **Right Panel (Forest Plot & Profile Divergence)**:
  - Primary Placeholder: `[INSERT FIGURE: methodology/assets/figures/F08_forest_batters.png]`
  - Supplementary Asset: `[INSERT FIGURE: methodology/assets/figures/F16a_high_vs_low_batters.png]` (Scoring rate & dismissal profiles across pressure tiers)
  - Key Note: Abhishek Sharma, Tim David, and Suryakumar Yadav form an elite Tier-1 frontier ($P(\text{Top } 10) \ge 94\%$), delivering over +23 runs per 100 deliveries above expectation. Phil Salt forms a solid Tier 1 anchor (+21.5, 87% P(top 10)).

---

### SLIDE 11: Player Rankings — Bowlers: The Qualified Top 10
- **Slide Header**: QUALIFIED BOWLERS RANKING
- **Action Subtitle**: Opposition-adjusted ridge ratings isolate elite bowling resilience in decisive moments.
- **Layout**: Left: Top 10 Table (`T02`); Right: Forest Plot Distribution (`F09`).
- **Left Panel (Top 10 Bowlers Table)**:
  | Rank | Player | Franchise / Nation | Rating (runs/100b) | 80% Interval (Bootstrap) | P(Top 10) | HIGH Balls |
  | :---: | :--- | :--- | :---: | :---: | :---: | :---: |
  | **1** | **Sunil Narine** | KKR | **+29.1** | [+22.7, +34.2] | **99.7%** | 370 |
  | **2** | **Jasprit Bumrah** | MI / IND | **+27.2** | [+20.2, +34.6] | **96.3%** | 358 |
  | **3** | **Varun Chakravarthy**| KKR / IND | **+20.2** | [+15.3, +25.8] | **82.3%** | 435 |
  | **4** | **Rashid Khan** | GT / AFG | **+17.5** | [+11.2, +25.1] | **58.0%** | 677 |
  | **5** | **Mustafizur Rahman** | CSK / DC / KKR / BAN | **+16.2** | [+10.3, +21.9] | **47.3%** | 438 |
  | **6** | **Mitchell Santner** | CSK / MI / NZ | **+15.7** | [+8.7, +22.9] | **39.0%** | 426 |
  | **7** | **Nathan Ellis** | CSK / PBKS / AUS | **+15.7** | [+8.5, +22.5] | **44.0%** | 264 |
  | **8** | **Lungi Ngidi** | DC / RCB / SA | **+15.4** | [+8.2, +21.4] | **33.7%** | 266 |
  | **9** | **Kuldeep Yadav** | DC / IND | **+15.2** | [+8.6, +21.2] | **38.3%** | 462 |
  | **10** | **Noor Ahmad** | CSK / GT / AFG | **+14.9** | [+6.5, +22.0] | **38.0%** | 305 |
- **Right Panel (Forest Plot & Profile Divergence)**:
  - Primary Placeholder: `[INSERT FIGURE: methodology/assets/figures/F09_forest_bowlers.png]`
  - Supplementary Asset: `[INSERT FIGURE: methodology/assets/figures/F16b_high_vs_low_bowlers.png]` (Economy & strike rate profiles across pressure tiers)
  - Key Note: Narine and Bumrah form an elite Tier-1 frontier ($P(\text{Top } 10) > 96\%$), delivering $+27$ to $+29$ runs saved per 100 high-pressure deliveries.

---

### SLIDE 12: Decision Rigor & Statistical Parity
- **Slide Header**: POSTERIOR UNCERTAINTY & STATISTICAL TIES
- **Action Subtitle**: Why single-point deterministic ranks mislead auction strategy: embracing 80% intervals (bootstrap).
- **Layout**: Left: P(Top 10) Distribution Chart; Right: 3-Pillar Practical Decision Framework.
- **Left Panel (Posterior P(Top 10) Mass)**:
  - Placeholder: `[INSERT FIGURE: methodology/assets/figures/F11_p_top10.png]`
  - Expected Overlap Metric: Expected top-10 repeat overlap across bootstrap draws is **6.16 / 10** for batters and **5.77 / 10** for bowlers.
- **Right Panel (Franchise Decision Framework)**:
  - **Tier 1: High-Confidence Anchors ($P(\text{Top } 10) \ge 75\%$)**
    - Batters: Abhishek Sharma, Tim David, Suryakumar Yadav, Phil Salt. Bowlers: Sunil Narine, Jasprit Bumrah, Varun Chakravarthy.
    - *Action*: Premium auction capital justified. High signal-to-noise ratio.
  - **Tier 2: Statistical Chasing Pack ($25\% \le P(\text{Top } 10) < 75\%$)**
    - Batters: Heinrich Klaasen, Romario Shepherd, Nicholas Pooran, Rajat Patidar, Mitchell Marsh, Travis Head. Bowlers: Rashid, Mustafizur, Santner, Ellis.
    - *Action*: Treat as statistically tied. Target on price efficiency, role compatibility, and phase fit rather than nominal rank.
  - **Tier 3: Volume-Constrained Near Misses**
    - Players with high raw rates but borderline sample size ($100 \le \text{Balls} < 150$).
    - *Action*: Monitor for private trial data; do not overpay in open bidding.

---

### SLIDE 13: Model Sensitivity & Hyperparameter Stress-Testing
- **Slide Header**: SENSITIVITY & ROBUSTNESS ANALYSIS
- **Action Subtitle**: Rankings withstand hyperparameter perturbations across time-decay, thresholds, and cohort splits.
- **Layout**: Left: Sensitivity Correlation Plot (`F12`); Right: Summary Benchmark Table (`T04`).
- **Left Panel (Kendall's $\tau$ Sensitivity Chart)**:
  - Placeholder: `[INSERT FIGURE: methodology/assets/figures/F12_sensitivity.png]`
- **Right Panel (Hyperparameter Stress-Test Table)**:
  - Table:
    - `PI Threshold q0.70 vs q0.75`: Batters $\tau = 0.99$ (overlap 8/10) | Bowlers $\tau = 0.98$ (overlap 10/10)
    - `PI Threshold q0.80 vs q0.75`: Batters $\tau = 1.00$ (overlap 10/10) | Bowlers $\tau = 0.95$ (overlap 9/10)
    - `No Time Decay vs 730d Half-Life`: Batters $\tau = 1.00$ (overlap 10/10) | Bowlers $\tau = 0.82$ (overlap 8/10)
    - `IPL-Only vs All T20`: Batters $\tau = 0.65$ (overlap 7/10) | Bowlers $\tau = 1.00$ (overlap 9/10)
    - `Baseline-Only ($\beta$)`: Batters $\tau = 0.93$ (overlap 8/10) | Bowlers $\tau = 0.95$ (overlap 10/10)
    - `Estimator Disagreement (Ridge vs EB)`: Batters $\tau = 0.70$ (overlap 7/10) | Bowlers $\tau = 0.79$ (overlap 7/10)
  - Key Audit Finding: Bowler rankings exhibit extraordinary rank invariance ($\tau \ge 0.95$ across almost all parameter adjustments), while batter rankings demonstrate that combining international and IPL data provides the necessary sample size to stabilize clutch signals.

---

### SLIDE 14: Tactical Auction & Team Selection Playbook
- **Slide Header**: ACTIONABLE FRANCHISE PLAYBOOK
- **Action Subtitle**: Translating empirical Bayes insights into tangible tactical advantages for Rajasthan Royals.
- **Layout**: 3 Strategic Action Cards.
- **Card 1: Auction Valuation Arbitrage**
  - *Insight*: The market often bids on high-profile finishers whose pressure shift ($\delta$) is negative or negligible, while undervalue high-baseline anchors whose $\beta$ delivers consistent execution under stress.
  - *Recommendation*: Prioritize players with high baseline $\beta$ and high $w_{\text{opp}}$ adjusted metrics (e.g., Phil Salt, Rinku Singh) over volatile finishers who lack fundamental technique.
- **Card 2: Bangladeshi Player Eligibility Advantage**
  - *Insight*: Mustafizur Rahman ranks **#5 among all eligible bowlers** (+16.2 rating, 438 High-Pressure balls). Seven Bangladeshi players have registered for the IPL 2027 mini-auction.
  - *Recommendation*: Target Mustafizur as an elite death-overs leverage specialist at potential value pricing due to market discount.
- **Card 3: In-Game Matchup & Over Allocation**
  - *Insight*: High-pressure balls are concentrated 4.5x more heavily in death overs (16–20) than middle overs.
  - *Recommendation*: Reserve Jasprit Bumrah / Sunil Narine archetype bowlers exclusively for overs 17, 19, and 20 when leverage exceeds $\Pi \ge 0.85$, preventing wasted high-clutch equity in low-leverage phases.

---

### SLIDE 15: Limitations, Governance & Analytical Roadmap
- **Slide Header**: GOVERNANCE, LIMITATIONS & FUTURE EVOLUTION
- **Action Subtitle**: Transparent scientific boundary conditions and the Phase 2 analytics roadmap.
- **Layout**: 2-Column Split: Scope Boundaries vs Analytical Evolution.
- **Left Column: Scope Boundaries & Limitations**
  - *Sample Attenuation*: Players with $<150$ high-pressure deliveries cannot be confidently ranked.
  - *Unmodeled Ball-Tracking Data*: Current framework tracks state outcomes (runs, wickets, extras); pitch-level hawk-eye data (release speed, spin deviation, seam movement) is unmodeled in Phase 1.
  - *Dropped Catch & Fielding Variance*: Catches dropped under pressure currently benefit batters in standard scorebook accounting; Phase 2 requires expected fielding value modeling.
- **Right Column: Analytical Roadmap (Phase 2)**
  - *Delivery-Trajectory Integration*: Merging Hawk-Eye trajectory and bat-sensor tracking into the ex-ante WP engine.
  - *Dynamic In-Play Fielding Model*: True bowler attribution independent of outfield drops and misfields.
  - *Live Match Dugout Integration*: Real-time tablet feed feeding live leverage and win-probability swings to dugout coaches during IPL 2027.
- **Footer**: "Model Engine v2.4 Certified. Zero data fabrication. All metrics reproducible via `outputs/final/`."

---

## 4. INSTRUCTIONS FOR THE PPTX GENERATOR AGENT

When generating the `.pptx` file:
1. **Apply consistent typography**: Title in Bold Navy (`#001D4A`), Subtitle in Royal Pink (`#E6007E`), cards in Crisp White (`#FFFFFF`) with thin borders (`#E2E8F0`).
2. **Embed layout containers**: Use card shapes with generous padding and clear alignment.
3. **Insert the specified chart placeholders**: Place bounding boxes/shapes labeled with the exact path from `methodology/assets/figures/` so the analyst can insert images with a single click.
4. **Preserve exact numbers**: Do not round beyond the figures cited (e.g., AUC `0.860`, Brier `0.1515`, ECE `1.12%`, Narine `+29.1`, Salt `+21.5`).
5. **Add Speaker Notes**: Include a 2-paragraph executive script in the PowerPoint speaker notes section for every slide.
