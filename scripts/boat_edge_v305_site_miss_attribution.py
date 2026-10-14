#!/usr/bin/env python3
"""Read-only SITE-only ordered-leg miss attribution on V301-attested rows."""
import argparse
import json
from pathlib import Path
from scripts.boat_edge_v301_paired_evidence import BASE, CONFIG, EvidenceError, checked_row, formal_lock

def category(row):
    if row["winning"] in row["baseline"]:
        return "top10_hit"
    head, second, third = row["winning"].split("-")
    tickets = [ticket.split("-") for ticket in row["baseline"]]
    if not any(t[0] == head for t in tickets):
        return "head_missing"
    if not any(t[0] == head and t[1] == second for t in tickets):
        return "second_missing_given_head"
    if not any(t[0] == head and t[1] == second and t[2] == third for t in tickets):
        return "third_missing_given_head_second"
    raise EvidenceError("MISS_CLASSIFICATION_INCONSISTENT")

def summarize(rows):
    counts = {name:0 for name in ("top10_hit","head_missing","second_missing_given_head","third_missing_given_head_second")}
    for row in rows:
        counts[category(row)] += 1
    if sum(counts.values()) != len(rows):
        raise EvidenceError("MISS_COUNTS_NOT_EXHAUSTIVE")
    return {"races":len(rows),"counts":counts,"misses":len(rows)-counts["top10_hit"],
            "entry_attribution_unavailable":True,"scenario_attribution_unavailable":True,
            "model_improvement_proven":False}

def audit(root):
    root=Path(root).resolve()
    formal_lock(root)
    unique={}
    studies={}
    for study in CONFIG:
        folder=root/BASE/(study+"_scored")
        if not folder.is_dir():
            raise EvidenceError("SCORED_COHORT_DIRECTORY_MISSING_"+study)
        rows=[]
        for path in sorted(folder.glob("*.json")):
            row=checked_row(root,study,path)
            rows.append(row)
            key=row["key"]
            if key in unique and (unique[key]["winning"]!=row["winning"] or unique[key]["baseline"]!=row["baseline"]):
                raise EvidenceError("CROSS_STUDY_RACE_OR_BASELINE_CONFLICT_"+key)
            unique[key]=row
        studies[study]=summarize(rows)
    return {"schema":"BOAT_EDGE_V305_SITE_ONLY_MISS_ATTRIBUTION_V1",
            "scope":"V301_VERIFIED_SITE_ONLY_NOT_FORMAL_FRESH",
            "studies":studies,"unique_races":summarize(list(unique.values())),
            "formal_results_read":False,"promotion_authorized":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    args=p.parse_args()
    print(json.dumps(audit(args.root),sort_keys=True,indent=2))

if __name__=="__main__":
    main()
