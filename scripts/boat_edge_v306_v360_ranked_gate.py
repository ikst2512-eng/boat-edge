#!/usr/bin/env python3
"""V306: read-only structural gate for V360 frozen research TopK.

No outcomes, odds, payouts, retrospective reconstruction, or Formal data reads.
Structural readiness is NOT evidence of independent predeadline publication.
"""
import argparse
import json
import re
from pathlib import Path

MODEL="BOAT_EDGE_V360_PREDEADLINE_RESEARCH_RANKED120"
MODES=("national_only","national_motor","national_motor_st")
COMBO=re.compile(r"[1-6]-[1-6]-[1-6]\Z")

def valid_combo(value):
    return isinstance(value,str) and COMBO.fullmatch(value) is not None and len(set(value.split("-")))==3

def inspect(frozen):
    if not isinstance(frozen,dict):
        return "INVALID_OBJECT"
    if frozen.get("research_ranked_120_schema") is None and frozen.get("research_ranked_120_by_mode") is None:
        return "NO_V360_RANKING"
    if frozen.get("research_ranked_120_schema")!=MODEL:
        return "INVALID_MODEL_ID"
    modes=frozen.get("research_ranked_120_by_mode")
    if not isinstance(modes,dict) or set(modes)!=set(MODES):
        return "INVALID_MODES"
    for name in MODES:
        rows=modes[name]
        if not isinstance(rows,list) or len(rows)!=120:
            return "INVALID_CARDINALITY"
        seen=set()
        for rank,row in enumerate(rows,1):
            if not isinstance(row,dict) or type(row.get("rank")) is not int or row["rank"]!=rank:
                return "INVALID_RANK"
            boat=row.get("boat_combo")
            if not valid_combo(boat) or boat in seen:
                return "INVALID_TICKET"
            seen.add(boat)
            mass=row.get("relative_model_mass")
            if type(mass) not in (int,float) or not (0<=mass<=1):
                return "INVALID_MASS"
        if len(seen)!=120 or abs(sum(r["relative_model_mass"] for r in rows)-1)>1e-8:
            return "INVALID_DISTRIBUTION"
    return "STRUCTURAL_TOP3_TOP5_TOP10_READY_NOT_ATTESTED"

def audit(root, folder):
    status=json.loads((root/"data/formal_status.json").read_text(encoding="utf-8"))
    guards=status.get("guards") or {}
    if (any(guards.get(k) is not False for k in ("results_seen","unlock","scoring"))
        or guards.get("RESULT_UNLOCK_TOKEN") is not None
        or (status.get("formalFirst100") or {}).get("races")!=0):
        raise ValueError("FORMAL_LOCK_REQUIRED")
    counts={}
    folder=Path(folder).resolve()
    if not folder.is_dir():
        return {"scope":"PRE_RESULT_V360_STRUCTURAL_ONLY","folder_present":False,
                "counts":{},"eligible_scored_races":0,"promotion_authorized":False}
    for path in sorted(folder.glob("*.json")):
        try:
            label=inspect(json.loads(path.read_text(encoding="utf-8")))
        except (OSError,ValueError):
            label="INVALID_JSON"
        counts[label]=counts.get(label,0)+1
    return {"scope":"PRE_RESULT_V360_STRUCTURAL_ONLY","folder_present":True,
            "counts":counts,"eligible_scored_races":0,"promotion_authorized":False}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--folder",type=Path,required=True,help="Explicit directory of original V332 frozen research JSON; never infer historical paths")
    args=p.parse_args()
    print(json.dumps(audit(args.root,args.folder),sort_keys=True))
