#!/usr/bin/env python3
"""Read-only Top3/5/10 audit of V301-verified SITE-only scored records.

Never reads Formal Fresh results, results endpoints or payout APIs.
"""
import argparse
import json
from pathlib import Path
from scripts.boat_edge_v301_paired_evidence import BASE, CONFIG, EvidenceError, checked_row, formal_lock

def audit(root):
    root = Path(root).resolve()
    formal_lock(root)
    studies = {}
    unique = {}
    for study in CONFIG:
        folder = root / BASE / (study + "_scored")
        if not folder.is_dir():
            raise EvidenceError("SCORED_COHORT_DIRECTORY_MISSING_" + study)
        rows = []
        for path in sorted(folder.glob("*.json")):
            row = checked_row(root, study, path)
            rows.append(row)
            key = row["key"]
            if key in unique and (unique[key]["baseline"] != row["baseline"] or unique[key]["winning"] != row["winning"]):
                raise EvidenceError("CROSS_STUDY_BASELINE_CONFLICT_" + key)
            unique[key] = row
        studies[study] = summarize(rows)
    return {"schema":"BOAT_EDGE_V304_SITE_ONLY_RANKED_TOPK_AUDIT_V1",
            "scope":"V301_GIT_VERIFIED_SCORED_SITE_ONLY_NOT_FORMAL_FRESH",
            "studies":studies,"unique_races":summarize(list(unique.values())),
            "overlap_not_additive":True,"promotion_authorized":False,
            "accuracy_improvement_proven":False,"formal_results_read":False}

def summarize(rows):
    n = len(rows)
    hits = {str(k):sum(r["winning"] in r["baseline"][:k] for r in rows) for k in (3,5,10)}
    return {"races":n,"days":len({r["day"] for r in rows}),
            "baseline_hits":hits,
            "baseline_hit_rate":{k:(v/n if n else None) for k,v in hits.items()},
            "new_model_delta":None,
            "candidate_top3_top5_unavailable":True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    args=p.parse_args()
    print(json.dumps(audit(args.root),sort_keys=True,indent=2))

if __name__=="__main__":
    main()
