#!/usr/bin/env python3
"""PRE_RESULT-only TopK readiness check. Never read result or payout files."""
import argparse
import json
import re
from pathlib import Path

def inspect(row):
    if not isinstance(row, dict) or row.get("scope") != "SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH":
        return "INVALID_SCOPE"
    if row.get("formal_results_seen") is not False or row.get("formal_gate_unlocked") is not False:
        return "FORMAL_GATE_UNVERIFIED"
    top = row.get("top10")
    if not isinstance(top, list) or len(top) != 10:
        return "TOP10_INVALID"
    for x in top:
        if not isinstance(x, str) or not re.fullmatch(r"[1-6]-[1-6]-[1-6]", x) or len(set(x.split("-"))) != 3:
            return "COMBO_INVALID"
    if len(set(top)) != 10:
        return "TOP10_INVALID"
    modes = row.get("frozen_mode_tickets")
    if not isinstance(modes, dict) or not isinstance(modes.get("hit"), list):
        return "RANKED_HIT_MISSING"
    hit = [t.get("combo") for t in modes["hit"] if isinstance(t, dict)]
    if hit != top:
        return "RANKED_HIT_TOP10_MISMATCH"
    return "RANKED_TOP3_TOP5_TOP10_AVAILABLE"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    args=p.parse_args()
    root=Path(args.root)
    status=json.loads((root/"data/formal_status.json").read_text())
    g=status.get("guards") or {}
    if any(g.get(k) is not False for k in ("results_seen","unlock","scoring")) or g.get("RESULT_UNLOCK_TOKEN") is not None or (status.get("formalFirst100") or {}).get("races") != 0:
        raise SystemExit("FORMAL_LOCK_NOT_CONFIRMED")
    folder=root/"data/site_autopilot/v232_cohort"
    counts={}
    for path in sorted(folder.glob("*.json")):
        try:
            label=inspect(json.loads(path.read_text()))
        except (ValueError,OSError):
            label="INVALID_JSON"
        counts[label]=counts.get(label,0)+1
    print(json.dumps({"scope":"PRE_RESULT_RANKED_TOPK_READINESS_ONLY","cohorts":sum(counts.values()),"status_counts":counts,"scored_races":0,"topk_hit_rates":None,"model_promotion_authorized":False},sort_keys=True))
if __name__=="__main__":
    main()
