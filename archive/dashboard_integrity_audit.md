# Dashboard Integrity Audit

Audit date: 2026-11-15

## Scope

Read-only review of the static dashboard in `docs/`, using the exported JSON under
`docs/data/` as the authoritative dashboard contract. No UI or design files were
modified during this audit.

## Checks passed

- All five exported JSON files load successfully.
- All dashboard JavaScript files pass `node --check`.
- The seven configured routes render without the visible `Error rendering screen`
  fallback: Overview, Rankings, Player Deep Dive, Compare Tools, Pressure
  Definition, Sample Validation, and Methodology.
- The Overview match and delivery counts match `docs/data/meta.json`: 805 usable
  matches and 192,156 usable balls.
- The displayed primary ranking names and rounded rating/interval values match the
  first ten rows of `players_batters.json` and `players_bowlers.json`.
- Pressure dimension counts and shares are available in `docs/data/pressure.json`.

## Blocking integrity failures

### 1. Unsupported validation claims are displayed

`docs/data/validation.json` has `wp_report`, `reliability`, `cv_hyper`, `kappa`,
and `exclusions` set to `null`. Despite that, the dashboard displays hard-coded
metrics:

- Overview: AUC `0.86` and Brier `0.141`
  ([overview.js](/Users/hemanth/Documents/Projects/RR_Hackathon/docs/assets/js/screens/overview.js:82)).
- Validation: AUC `0.864`, Brier/calibration claims, split-half `r = 0.78`,
  tau values, ECE, and a deployment certification
  ([validation.js](/Users/hemanth/Documents/Projects/RR_Hackathon/docs/assets/js/screens/validation.js:46)).
- Methodology: `182,410` tracked balls and `tau = 4.18`
  ([method.js](/Users/hemanth/Documents/Projects/RR_Hackathon/docs/assets/js/screens/method.js:45)).

These values cannot be verified from the current exported data and must not be
presented as measured results.

### 2. Pressure screen does not use the exported pressure contract

The exported pressure data contains only `definition` plus dimension/share rows
(`innings`, `phase_idx`, and `over`). It does not contain a heatmap matrix,
delivery-level values, or a realised-vs-expected validation table. The pressure
screen nevertheless presents a fixed heatmap and hard-coded PI example
(`PI: 0.88`) ([pressure.js](/Users/hemanth/Documents/Projects/RR_Hackathon/docs/assets/js/screens/pressure.js:622)).

### 3. Player and comparison screens are fixed to Phil Salt

The player screen is labelled “Phil Salt”, contains fixed sample counts and
intervals, and does not read `data` ([player.js](/Users/hemanth/Documents/Projects/RR_Hackathon/docs/assets/js/screens/player.js:1)).
The comparison screen similarly hard-codes Phil Salt, Heinrich Klaasen, and Tim
David and their metrics ([compare.js](/Users/hemanth/Documents/Projects/RR_Hackathon/docs/assets/js/screens/compare.js:39)).
This makes the displayed player information stale whenever the selected player or
active list changes.

### 4. Player deep links do not route to a player

The router parses the full hash as a route key and only has a `player` route.
`#/player/6281` therefore falls back to Rankings instead of opening player 6281
([main.js](/Users/hemanth/Documents/Projects/RR_Hackathon/docs/assets/js/main.js:132)).
This was reproduced in the browser: navigating to `#/player/6281` produced the
title “Player Rankings — SupeRR Intelligence Engine”.

### 5. Rankings search is non-functional

The rankings screen has an input and attaches an input listener
([rankings.js](/Users/hemanth/Documents/Projects/RR_Hackathon/docs/assets/js/screens/rankings.js:3692)),
but typing `zzzz` left all 12 visible table rows and showed no empty-state result.
The screen is built from fixed HTML strings rather than the exported player JSON
([rankings.js](/Users/hemanth/Documents/Projects/RR_Hackathon/docs/assets/js/screens/rankings.js:3564)).

### 6. Eligibility metadata conflicts with displayed rankings

`meta.json` declares a batter minimum of 150 HIGH balls, while the displayed
primary top ten includes Rajat Patidar with 138 balls and Glenn Phillips with 142
balls. The UI labels these as low sample, but still presents them in the eligible
top-ten list. The eligibility rule and displayed list must be reconciled before
submission.

### 7. Static explanatory counts are stale

The validation and methodology screens use 182,410 balls, while the authoritative
metadata reports 192,156 usable balls. The pressure screen also contains fixed
scope/count text not present in the exported contract.

## Functional smoke results

| Area | Result |
|---|---|
| Route rendering | Pass, no visible render exception |
| Primary/alternate list shell | Control changes label, but static screen content is not data-bound |
| Player links from ranking/overview | Fail: nested player hash falls back to Rankings |
| Rankings search | Fail: query does not reduce rows or show empty state |
| Player data selection | Fail: fixed Phil Salt content |
| Compare data selection | Fail: fixed three-player content |
| Validation metrics | Fail: unsupported hard-coded values |
| Pressure metrics/heatmap | Fail: source contract mismatch |
| JavaScript syntax | Pass |

## Submission readiness

**Not ready for submission.** The current dashboard can be rendered, but the
displayed validation, pressure, player, and comparison information is not fully
derived from the available exported data, and two core interactions (player
deep-linking and rankings search) fail. These are data-integrity/functionality
blockers rather than visual/design issues.

