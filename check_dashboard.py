#!/usr/bin/env python3
"""
check_dashboard.py - pre-submission integrity gate for the static dashboard (no browser needed).

  python check_dashboard.py --docs docs

Fails (exit code 1) if:
  * a required data file/section is missing or malformed
  * rankings are inconsistent (not sorted, ranks not 1..N, intervals not around the rating, eligibility rules violated)
  * any Pakistan / Pakistan A player is in the lists, or an inactive (>365 days) player is
  * any player name or headline statistic from the data is hard-coded in HTML/JS/CSS
  * known fabricated values from earlier builds are present
  * anything about the removed "alternate list" is still in the source or data
Warnings (exit code 0): optional sections missing (the UI must hide those cards).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FAKE_VALUES = ["0.864", "0.141", "182,410", "182410", "r = 0.78", "tau = 4.18", "PI: 0.88"]
ALT_WORDS = ["rank_alt", "p_top10_alt", "removed_in_alt", "in_top10_alt", "alt_list", "alternate list", "Alternate list", "list=alt", '"alt"', "'alt'",
             "Primary list", "primary list", "rank_primary", "in_top10_primary"]
SRC_EXT = {".html", ".js", ".css", ".mjs"}
errors: list[str] = []
warnings: list[str] = []


def load(p: Path):
    if not p.exists():
        errors.append(f"missing {p}")
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        errors.append(f"bad JSON {p}: {e}")
        return None


def check_players(rows, role, meta):
    if not rows:
        errors.append(f"{role}: empty player list")
        return
    ratings = [r["rating"] for r in rows]
    if ratings != sorted(ratings, reverse=True):
        errors.append(f"{role}: rows not sorted by rating descending")
    if [r["rank"] for r in rows] != list(range(1, len(rows) + 1)):
        errors.append(f"{role}: ranks are not 1..N")
    thr = meta.get("rules", {}).get("min_high_balls", {}).get(role)
    for r in rows:
        if not (r["lo80"] <= r["rating"] <= r["hi80"]):
            errors.append(f"{role}: {r['name']} rating outside its 80% interval")
        if thr and r["n_high"] < thr:
            errors.append(f"{role}: {r['name']} has {r['n_high']} HIGH balls < minimum {thr} but is listed")
        if not (0 <= r["p_top10"] <= 1):
            errors.append(f"{role}: {r['name']} P(top10) outside [0,1]")
        teams = r.get("ipl_teams", []) + r.get("national_teams", []) + r.get("a_teams", [])
        if any(t.startswith("Pakistan") for t in teams):
            errors.append(f"{role}: Pakistan player in ranking: {r['name']}")
        if r.get("active") is False:
            errors.append(f"{role}: inactive player in ranking: {r['name']} ({r.get('days_since')} days)")
        if r.get("in_top10") != (r["rank"] <= 10):
            errors.append(f"{role}: in_top10 flag inconsistent for {r['name']}")
    if len({r["player_id"] for r in rows}) != len(rows):
        errors.append(f"{role}: duplicate player_id")
    e = sum(r["p_top10"] for r in rows[:10])
    print(f"  {role}: {len(rows)} players, expected top-10 overlap {e:.1f}/10, top-10 = {', '.join(r['name'] for r in rows[:10])}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", default="docs")
    a = ap.parse_args()
    docs = Path(a.docs)
    data = docs / "data"
    meta, bat, bow = load(data / "meta.json"), load(data / "players_batters.json"), load(data / "players_bowlers.json")
    pres, val = load(data / "pressure.json"), load(data / "validation.json")
    if meta and bat and bow:
        print("Data checks")
        check_players(bat, "batter", meta)
        check_players(bow, "bowler", meta)
        c = meta.get("counts", {})
        if c.get("eligible_batters") != len(bat) or c.get("eligible_bowlers") != len(bow):
            errors.append("meta.counts eligible_* do not match player list lengths")
        if "alt_list_also_excludes" in meta.get("rules", {}):
            errors.append("meta.rules still contains alt_list_also_excludes")
    if pres is not None:
        for k in ("definition", "high_low", "heatmap", "traces", "calibration", "high_share_by_over"):
            if not pres.get(k):
                warnings.append(f"pressure.{k} missing -> the Pressure page must hide that card")
    if val is not None:
        for k in ("wp_report", "tournament", "sensitivity", "exclusions", "reliability", "cv_hyper", "kappa", "delta_evidence"):
            if not val.get(k):
                warnings.append(f"validation.{k} missing -> the Validation page must hide that card")
        for r in (val.get("sensitivity") or []):
            if r.get("run", "").startswith(("fractional", "PI_q0.75", "half_life")) and r.get("top10_overlap") not in (None, 10):
                errors.append(f"sensitivity default row {r['run']} ({r['role']}) shows overlap {r['top10_overlap']} (must be 10)")
            if "alternate" in str(r.get("run", "")).lower():
                errors.append("sensitivity still contains an alternate-list row")

    print("Source scan")
    names = {r["name"] for r in (bat or []) + (bow or [])}
    nums = set()
    if meta:
        for v in (meta.get("counts") or {}).values():
            if isinstance(v, int) and v > 999:
                nums.add(f"{v:,}")
                nums.add(str(v))
    files = [p for p in docs.rglob("*") if p.suffix in SRC_EXT and "data" not in p.parts and "node_modules" not in p.parts]
    for p in files:
        text = p.read_text(encoding="utf-8", errors="ignore")
        for n in names:
            if len(n) > 5 and n in text:
                errors.append(f"hard-coded player name '{n}' in {p.relative_to(docs)}")
        for n in nums:
            if n in text:
                errors.append(f"hard-coded count '{n}' in {p.relative_to(docs)}")
        for f in FAKE_VALUES:
            if f in text:
                errors.append(f"known fabricated value '{f}' in {p.relative_to(docs)}")
        for w in ALT_WORDS:
            if w in text:
                errors.append(f"alternate-list remnant '{w}' in {p.relative_to(docs)}")
        if re.search(r"https?://(?!cdn\.jsdelivr\.net|www\.w3\.org|localhost)", text) and p.suffix in {".js", ".html"}:
            warnings.append(f"external URL in {p.relative_to(docs)} (check it is intended)")
    print(f"  scanned {len(files)} source files")

    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("FAIL ", e)
    print(f"\n{'PASS' if not errors else 'FAIL'}: {len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
