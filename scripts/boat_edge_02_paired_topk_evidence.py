#!/usr/bin/env python3
"""Offline research aggregation of pre-scored paired 2025 TopK rows only.

No result, payout, odds or Formal Fresh reads. This is not the existing scorer.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
from datetime import date
import json
import math
from pathlib import Path
import random
import re

SCHEMA="BOAT_EDGE_02_PAIRED_TOPK_PRE_SCORED_V1"
KEY=re.compile(r"2025[0-1][0-9][0-3][0-9]-(?:0[1-9]|1[0-9]|2[0-4])-(?:0[1-9]|1[0-2])\Z")
TOP_K=(3,5,10)

def _date(key):
    if not isinstance(key,str) or KEY.fullmatch(key) is None:
        raise ValueError("2025_HOLDOUT_RACE_KEY_REQUIRED")
    try:
        day=date.fromisoformat(key[:4]+"-"+key[4:6]+"-"+key[6:8])
    except ValueError:
        raise ValueError("INVALID_RACE_DATE") from None
    return day.isoformat()

def _hits(record,field):
    val=record.get(field)
    if not isinstance(val,dict) or set(val)!={str(k) for k in TOP_K}:
        raise ValueError("EXACT_TOPK_PRE_SCORED_FLAGS_REQUIRED")
    if any(type(val[str(k)]) is not bool for k in TOP_K):
        raise ValueError("BOOLEAN_TOPK_FLAGS_REQUIRED")
    if not (val["3"]<=val["5"]<=val["10"]):
        raise ValueError("TOPK_NESTING_VIOLATION")
    return val

def _sample_ci(days,k,*,resamples=2500,seed=2718):
    """Whole-day paired cluster bootstrap and 3-metric Bonferroni interval."""
    group=[(sum(int(x["candidate"][k])-int(x["baseline"][k]) for x in rows),len(rows))
           for rows in days.values()]
    rng=random.Random(seed)
    draws=[]
    for _ in range(resamples):
        sample=rng.choices(group,k=len(group))
        draws.append(sum(x[0] for x in sample)/sum(x[1] for x in sample))
    draws.sort()
    tail=0.05/(2*len(TOP_K))
    return [draws[int(resamples*tail)],draws[min(resamples-1,math.ceil(resamples*(1-tail)))]]

def compare(payload):
    if not isinstance(payload,dict) or payload.get("schema")!=SCHEMA:
        raise ValueError("PRE_SCORED_SCHEMA_REQUIRED")
    if payload.get("stage")!="2025_HISTORICAL_REPLAY_NOT_PROSPECTIVE":
        raise ValueError("RETROSPECTIVE_STAGE_REQUIRED")
    if payload.get("licence_archive_reviewed") is not True or payload.get("external_scoring_reviewed") is not True:
        raise ValueError("INDEPENDENT_REVIEW_FLAGS_REQUIRED")
    for key in ("archive_receipt_sha256","scoring_receipt_sha256","baseline_model_sha256","candidate_model_sha256"):
        value=payload.get(key)
        if not isinstance(value,str) or re.fullmatch("[0-9a-f]{64}",value) is None:
            raise ValueError("SCORER_AND_MODEL_RECEIPTS_REQUIRED")
    if payload["baseline_model_sha256"]==payload["candidate_model_sha256"]:
        raise ValueError("SAME_MODEL_SHA_NOT_AN_EXPERIMENT")
    records=payload.get("paired_rows")
    if not isinstance(records,list) or not records:
        raise ValueError("PAIRED_ROWS_REQUIRED")
    seen=set()
    by_day=defaultdict(list)
    for record in records:
        if not isinstance(record,dict):
            raise ValueError("ROW_INVALID")
        race_key=record.get("race_key")
        day=_date(race_key)
        if race_key in seen:
            raise ValueError("DUPLICATED_RACE")
        seen.add(race_key)
        if record.get("same_race_same_ten_ticket_budget") is not True or record.get("independent_input_cutoff_checked") is not True:
            raise ValueError("MATCHED_TEN_AND_ASOF_EVIDENCE_REQUIRED")
        baseline=_hits(record,"baseline_hits")
        candidate=_hits(record,"candidate_hits")
        by_day[day].append({"baseline":baseline,"candidate":candidate})
    n=len(records)
    result={"schema":SCHEMA,"stage":"HISTORICAL_REPLAY_ONLY","holdout_year":2025,
            "paired_races":n,"independent_dates":len(by_day),
            "model_promotion_authorized":False,
            "licence_independently_verified_by_this_tool":False,
            "source_receipt_independently_verified_by_this_tool":False,
            "formal_fresh_results_accessed":False,"metrics":{}}
    eligible=n>=500 and len(by_day)>=30
    for k in TOP_K:
        name=str(k)
        b=sum(row["baseline_hits"][name] for row in records)
        c=sum(row["candidate_hits"][name] for row in records)
        win=sum(not row["baseline_hits"][name] and row["candidate_hits"][name] for row in records)
        loss=sum(row["baseline_hits"][name] and not row["candidate_hits"][name] for row in records)
        ci=_sample_ci(by_day,name) if eligible else None
        result["metrics"][f"top{k}"]={
            "baseline_hits":b,"candidate_hits":c,
            "baseline_rate":b/n,"candidate_rate":c/n,
            "delta_percentage_points":100*(c-b)/n,
            "candidate_only_wins":win,"baseline_only_wins":loss,
            "cluster_bootstrap_bonferroni_95_family_ci_delta_pp":[100*x for x in ci] if ci else None,
            "positive_beyond_sampling_uncertainty":bool(ci and ci[0]>0),
        }
    result["research_signal_all_topk_positive"]=bool(
        eligible and all(x["positive_beyond_sampling_uncertainty"] for x in result["metrics"].values()))
    result["independent_prospective_fresh_required"]=True
    return result

def main():
    parser=argparse.ArgumentParser(description="Research-only paired pre-scored TopK aggregator")
    parser.add_argument("--pre-scored-manifest",type=Path,required=True)
    args=parser.parse_args()
    root=Path(__file__).resolve().parent.parent
    path=args.pre_scored_manifest.resolve()
    if path.is_relative_to((root/"data").resolve()):
        raise SystemExit("PROTECTED_REPOSITORY_DATA_FORBIDDEN")
    print(json.dumps(compare(json.loads(path.read_text(encoding="utf-8"))),ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
