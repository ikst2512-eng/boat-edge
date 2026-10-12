#!/usr/bin/env python3
"""V255: deterministic, *descriptive* reference confidence audit.

Re-read only precommitted site-only V232 cohorts and already validated site
settlement V241. This script never accesses result endpoints, formal Fresh,
predictors, prices, rankings, paper funds, model gates or real purchases.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

BASE=Path("data/site_autopilot")
KEY=re.compile(r"^20\d{6}-\d{2}-\d{2}$")
SHA256=re.compile(r"^[a-f0-9]{64}$")

def read(path):
    try:
        result=json.loads(path.read_text(encoding="utf-8"))
        return result if isinstance(result,dict) else None
    except (OSError,ValueError,UnicodeError):return None

def sha(path):
    try:return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:return None

def stamp(value):
    try:
        d=dt.datetime.fromisoformat(str(value).replace("Z","+00:00"))
        return d.astimezone(dt.timezone.utc) if d.tzinfo else None
    except (TypeError,ValueError,OverflowError):return None

def original_git(root,path):
    relative=path.relative_to(root).as_posix()
    try:
        raw=subprocess.check_output(
            ["git","log","--diff-filter=A","--reverse","--format=%H|%cI","--",relative],
            cwd=root,text=True,stderr=subprocess.DEVNULL).splitlines()
        if not raw:return None
        commit,when=raw[0].split("|",1)
        original=subprocess.check_output(
            ["git","show",f"{commit}:{relative}"],
            cwd=root,stderr=subprocess.DEVNULL)
        return commit,stamp(when),hashlib.sha256(original).hexdigest()
    except (OSError,ValueError,subprocess.CalledProcessError):return None

def formal_guard(root):
    status=read(root/"data/formal_status.json") or {}
    g=status.get("guards") or {}
    assert all(g.get(k) is False for k in ("results_seen","unlock","scoring"))
    assert g.get("RESULT_UNLOCK_TOKEN") is None
    assert (status.get("formalFirst100") or {}).get("races",0)==0

def site_rows(root):
    report=read(root/BASE/"v241_results_current.json")
    if (report is None or report.get("schema")!="BOAT_EDGE_V241_VERIFIED_SITE_RESULTS_V1" or
        report.get("scope")!="VERIFIED_POST_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH" or
        report.get("formal_result_access") is not False or
        report.get("production_model_changed") is not False or
        report.get("accuracy_improvement_proven") is not False or
        report.get("real_or_paper_wagers_placed")!=0):
        raise ValueError("V255_SITE_RESEARCH_PROOF_MISSING")
    rows=report.get("rows")
    if not isinstance(rows,list) or len(rows)!=report.get("settled_verified_races"):
        raise ValueError("V255_SITE_SAMPLE_SIZE_MISMATCH")
    out={}
    for r in rows:
        if (not isinstance(r,dict) or not KEY.fullmatch(str(r.get("race_key",""))) or
            r["race_key"] in out or r.get("post_result_verified") is not True or
            not isinstance(r.get("top10_hit"),bool) or not isinstance(r.get("head_hit"),bool) or
            r.get("mode_outcomes",{}).get("hit",{}).get("hit") is not r["top10_hit"] or
            not SHA256.fullmatch(str(r.get("precommitted_sha256",""))) or
            not re.fullmatch("[a-f0-9]{40}",str(r.get("first_frozen_commit",""))) or
            not stamp(r.get("deadline_jst"))):raise ValueError("V255_UNVERIFIABLE_SITE_ROW")
        out[r["race_key"]]=r
    if (sum(r["top10_hit"] for r in out.values())!=report.get("top10_hits") or
        sum(r["head_hit"] for r in out.values())!=report.get("head_hits")):
        raise ValueError("V255_SITE_SUMMARY_PARITY_FAILED")
    return out

def inspect(root,key,r):
    path=root/BASE/"v232_cohort"/(key+".json")
    v=read(path)
    if v is None:return None
    when=stamp(v.get("deadline_jst"))
    snapshot=stamp(v.get("snapshot_saved_at"))
    committed=stamp(v.get("evidence_committed_at"))
    provenance=original_git(root,path)
    if (v.get("race_key")!=key or
        v.get("schema")!="BOAT_EDGE_V232_SITE_PROSPECTIVE_ACCURACY_COHORT_V1" or
        v.get("scope")!="SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH" or
        any(v.get(k) is not False for k in ("formal_results_seen","formal_gate_unlocked",
                                            "real_purchases_authorized","paper_purchases_authorized")) or
        not provenance or not when or not snapshot or not committed or
        not (snapshot<=committed<=provenance[1]<when) or
        when!=stamp(r["deadline_jst"]) or
        sha(path)!=provenance[2] or r["precommitted_sha256"]!=provenance[2] or
        r["first_frozen_commit"]!=provenance[0] or
        str(v.get("head_top1"))!=str(r.get("head_prediction")) or
        (str(v.get("head_top1"))==str(r.get("winning_combo",""))[:1])!=r["head_hit"]):
        return None
    mode=v.get("frozen_mode_tickets",{}).get("hit")
    if not isinstance(mode,list) or len(mode)!=10 or v.get("top10")!=[x.get("combo") for x in mode if isinstance(x,dict)]:
        return None
    if (str(r.get("winning_combo")) in v["top10"])!=r["top10_hit"]:return None
    weights=[]
    for x in mode:
        p=x.get("p_raw_percent")
        if not isinstance(p,(int,float)) or isinstance(p,bool) or not math.isfinite(p) or p<0 or p>100:
            return None
        weights.append(float(p))
    return {"race_key":key,"day_jst":key[:8],"head_hit":r["head_hit"],
      "top10_hit":r["top10_hit"],"relative_weight_total":round(sum(weights),6),
      "relative_weight_max":round(max(weights),6),"relative_weight_min":round(min(weights),6),
      "relative_weight_normalized_near_100":abs(sum(weights)-100)<0.02}

def wilson(hits,n):
    if n<=0:return None
    p=hits/n;z=1.96;div=1+z*z/n
    center=(p+z*z/(2*n))/div
    radius=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)/div
    return [round(100*max(0,center-radius),2),round(100*min(1,center+radius),2)]

def build(root):
    root=Path(root).resolve()
    formal_guard(root)
    rows=site_rows(root)
    checked=[]
    excluded={}
    for key,r in sorted(rows.items()):
        record=inspect(root,key,r)
        if record is None:
            excluded["V232_PRECOMMITTED_PROOF_UNVERIFIED"]=excluded.get("V232_PRECOMMITTED_PROOF_UNVERIFIED",0)+1
            continue
        checked.append(record)
    n=len(checked); head=sum(x["head_hit"] for x in checked)
    top10=sum(x["top10_hit"] for x in checked)
    normalized=sum(x["relative_weight_normalized_near_100"] for x in checked)
    day={}
    for x in checked:
        b=day.setdefault(x["day_jst"],{"day_jst":x["day_jst"],"races":0,"head_hits":0,"top10_hits":0})
        b["races"]+=1;b["head_hits"]+=x["head_hit"];b["top10_hits"]+=x["top10_hit"]
    return {
      "schema":"BOAT_EDGE_V255_SITE_ONLY_UNCALIBRATED_CONFIDENCE_AUDIT_V1",
      "scope":"SETTLED_SITE_REFERENCE_PROSPECTIVE_PROOF_NOT_FORMAL_FRESH",
      "site_settled_reference_races":len(rows),
      "prospective_source_verified_races":n,
      "excluded":dict(sorted(excluded.items())),
      "head":{"hits":head,"races":n,"rate_percent":round(100*head/n,2) if n else None,
              "wilson_95_percent":wilson(head,n)},
      "top10":{"hits":top10,"races":n,"rate_percent":round(100*top10/n,2) if n else None,
               "wilson_95_percent":wilson(top10,n)},
      "hit10_frozen_relative_weight":{"normalized_to_100_in_races":normalized,
          "verified_races":n,"all_normalized":normalized==n if n else False,
          "interpretation":"TEN_TICKET_RELATIVE_WEIGHTS_NOT_120_OUTCOME_PROBABILITY"},
      "by_day":[day[k] for k in sorted(day)],
      "rows":checked,
      "model_promotion_authorized":False,"accuracy_improvement_proven":False,
      "formal_result_access":False,"production_model_changed":False,
      "real_or_paper_wagers_placed":0,
      "note":"Internal confidence is a rank-derived heuristic, NOT a calibrated win probability. "
             "p_raw_percent in the frozen 10 tickets sums to approximately 100% within those 10 only. "
             "This is NOT a 120-combination predictive distribution.",
    }

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    p.add_argument("--check",action="store_true")
    args=p.parse_args()
    root=Path(args.root).resolve()
    result=build(root)
    data=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    path=root/BASE/"v255_confidence_current.json"
    if args.check:
        if not path.exists() or path.read_text(encoding="utf-8")!=data:
            raise SystemExit("V255_UNCALIBRATED_AUDIT_OUT_OF_DATE")
    elif not path.exists() or path.read_text(encoding="utf-8")!=data:
        path.write_text(data,encoding="utf-8")
    print("V255_SOURCE_VERIFIED_UNCALIBRATED",json.dumps({
      "n":result["prospective_source_verified_races"],"top10":result["top10"],
      "head":result["head"],"normalized":result["hit10_frozen_relative_weight"]["normalized_to_100_in_races"],
      "excluded":result["excluded"]},ensure_ascii=False,sort_keys=True))

if __name__=="__main__":main()
