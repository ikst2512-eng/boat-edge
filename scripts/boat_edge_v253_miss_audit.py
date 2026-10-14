#!/usr/bin/env python3
"""V253: descriptive site-only failure attribution from independently frozen research.

Strictly post-settlement; never queries results, official odds or formal Fresh.
No fitting, tuning, model promotion, paper wagers or synthetic returns.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
from collections import Counter
from pathlib import Path
import re
import sys

BASE=Path("data/site_autopilot")
KEY=re.compile(r"^20\d{6}-\d{2}-\d{2}$")
COMBO=re.compile(r"^[1-6]-[1-6]-[1-6]$")
SHA=re.compile(r"^[a-f0-9]{64}$")
V236_PRE="BOAT_EDGE_V236_HITRATE_FORWARD_SHADOW_V1"
V236_POST="BOAT_EDGE_V236_HITRATE_SCORE_V1"
V236_V1="PREDECLARED_HEAD_TAIL_COVERAGE_NO_ODDS_MULTIPLIER_BOOST"
V236_V2="PREDECLARED_HEAD_SECOND_COVERAGE_FROM_EXISTING_FROZEN_MODES_NO_NEW_ODDS_MULTIPLIER"
V236_V3="PREDECLARED_DISTINCT_HEAD_SECOND_TICKET_MEMBERSHIP_EXISTING_FROZEN_MODES"
V236_POLICIES=(V236_V1,V236_V2,V236_V3)
V240_PRE="BOAT_EDGE_V240_INDEPENDENT_SECOND_COVERAGE_PRE_V1"
V240_POST="BOAT_EDGE_V240_INDEPENDENT_SECOND_COVERAGE_SCORE_V1"
V241="BOAT_EDGE_V241_VERIFIED_SITE_RESULTS_V1"
MODES={
 "v236":("hit10","balance10","scenario7plus3","coverage15"),
 "v240":("hit10","pair_coverage10","second_coverage10"),
}
CATEGORIES=("hit","head_absent","second_absent_given_head","third_absent_given_head_second")

def read(p):
    try:
        value=json.loads(p.read_text(encoding="utf-8"))
        return value if isinstance(value,dict) else None
    except (OSError,UnicodeError,ValueError):return None

def digest(p):
    try:return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:return None

def time(v):
    try:
        t=dt.datetime.fromisoformat(str(v).replace("Z","+00:00"))
        if t.tzinfo:return t.astimezone(dt.timezone.utc)
    except (ValueError,TypeError,OverflowError):pass
    return None

def valid_combo(value):
    return isinstance(value,str) and bool(COMBO.fullmatch(value)) and len(set(value.split("-")))==3

def category(tickets,winning):
    if winning in tickets:return "hit"
    head,second,_=winning.split("-")
    if not any(t.startswith(head+"-") for t in tickets):return "head_absent"
    if not any(t.startswith(head+"-"+second+"-") for t in tickets):
        return "second_absent_given_head"
    return "third_absent_given_head_second"

def guard(root):
    obj=read(root/"data/formal_status.json") or {}
    g=obj.get("guards") or {}
    assert all(g.get(k) is False for k in ("results_seen","unlock","scoring")), "V253_FORMAL_RESULT_LOCK"
    assert g.get("RESULT_UNLOCK_TOKEN") is None, "V253_FORMAL_UNLOCK_TOKEN"
    assert type((obj.get("formalFirst100") or {}).get("races")) is int and (obj.get("formalFirst100") or {}).get("races")==0, "V253_FORMAL_COHORT_ACTIVE"

def verified_site_rows(root):
    doc=read(root/BASE/"v241_results_current.json")
    if (not doc or doc.get("schema")!=V241 or
        doc.get("scope")!="VERIFIED_POST_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH" or
        doc.get("formal_result_access") is not False or
        doc.get("real_or_paper_wagers_placed")!=0 or
        doc.get("production_model_changed") is not False or
        doc.get("accuracy_improvement_proven") is not False):return {}
    rows=doc.get("rows")
    if not isinstance(rows,list) or len(rows)!=doc.get("settled_verified_races"):return {}
    results={}
    for r in rows:
        if (not isinstance(r,dict) or not KEY.fullmatch(str(r.get("race_key",""))) or
            not valid_combo(r.get("winning_combo")) or r.get("post_result_verified") is not True or
            not isinstance(r.get("head_hit"),bool) or not isinstance(r.get("top10_hit"),bool) or
            r.get("mode_outcomes",{}).get("hit",{}).get("hit") is not r.get("top10_hit") or
            not isinstance(r.get("precommitted_sha256"),str) or not SHA.fullmatch(r["precommitted_sha256"]) or
            not isinstance(r.get("score_sha256"),str) or not SHA.fullmatch(r["score_sha256"]) or
            r["race_key"] in results):
            return {}
        results[r["race_key"]]=r
    if sum(x["head_hit"] for x in results.values())!=doc.get("head_hits"):return {}
    if sum(x["top10_hit"] for x in results.values())!=doc.get("top10_hits"):return {}
    return results

def validate_entry(root,lane,key,site):
    assert lane in MODES
    pre_path=root/BASE/(lane+"_frozen")/(key+".json")
    post_path=root/BASE/(lane+"_scored")/(key+".json")
    pre,post=read(pre_path),read(post_path)
    if not pre or not post:return None
    fields=MODES[lane]
    if pre.get("race_key")!=key or post.get("race_key")!=key:return None
    if not isinstance(pre.get("comparators"),dict):return None
    policy=pre.get("comparison_policy") if lane=="v236" else None
    if lane=="v236":
        if policy not in V236_POLICIES:return None
        if policy in (V236_V2,V236_V3):
            fields=fields+("headsecond10",)
            # Older V2 score rows may omit candidate_policy; V3 must be
            # explicitly tagged. No V1 record can gain a candidate later.
            tag=post.get("candidate_policy",V236_V2 if policy==V236_V2 else None)
            if tag!=policy:return None
            prefixes=post.get("prefix_outcomes")
            if not isinstance(prefixes,dict) or set(prefixes)!=set(("hit10","headsecond10")):
                return None
            for mode in ("hit10","headsecond10"):
                vals=prefixes.get(mode)
                if (not isinstance(vals,dict) or set(vals)!=set(("3","5","10"))):
                    return None
                for count in (3,5,10):
                    original=pre["comparators"].get(mode)
                    if not isinstance(original,list):return None
                    if type(vals[str(count)]) is not bool or vals[str(count)]!=(
                            site["winning_combo"] in original[:count]):
                        return None
        elif post.get("candidate_policy") is not None or post.get("prefix_outcomes") is not None:
            return None
    if not isinstance(pre.get("comparators"),dict) or set(pre["comparators"])!=set(fields):return None
    winning=site["winning_combo"]
    deadline=time(pre.get("deadline_jst"))
    freeze=time(pre.get("frozen_at"))
    first=time(pre.get("v232_first_git_committed_at" if lane=="v236" else "parent_first_commit_at"))
    parent_sha=pre.get("v232_cohort_sha256" if lane=="v236" else "parent_sha256")
    parent_git=pre.get("v232_first_git_commit" if lane=="v236" else "parent_first_commit")
    if (not deadline or not freeze or not first or not (first<deadline and freeze<deadline) or
        not SHA.fullmatch(str(parent_sha or "")) or
        not re.fullmatch("[a-f0-9]{40}",str(parent_git or "")) or
        parent_sha!=site["precommitted_sha256"]):return None
    if lane=="v236":
        if (pre.get("schema")!=V236_PRE or
            pre.get("scope")!="PROSPECTIVE_SITE_SHADOW_NOT_FORMAL_FRESH" or
            pre.get("result_seen_at_freeze") is not False or
            pre.get("production_model_changed") is not False or
            post.get("schema")!=V236_POST or
            post.get("scope")!="POST_RESULT_SITE_ONLY_NOT_FORMAL_FRESH" or
            post.get("frozen_candidate_sha256")!=digest(pre_path) or
            post.get("official_result")!=winning or
            post.get("model_promotion_authorized") is not False or
            post.get("production_accuracy_improvement_proven") is not False or
            post.get("real_or_paper_purchase") is not False or
            pre.get("v232_first_git_commit")!=site.get("first_frozen_commit")):
            return None
    else:
        if (pre.get("schema")!=V240_PRE or
            pre.get("scope")!="PRE_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH" or
            pre.get("results_seen_at_freeze") is not False or
            pre.get("formal_result_access") is not False or
            pre.get("production_model_changed") is not False or
            post.get("schema")!=V240_POST or
            post.get("scope")!="POST_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH" or
            post.get("frozen_sha256")!=digest(pre_path) or
            post.get("winning_combo")!=winning or
            post.get("v234_sha256")!=site["score_sha256"] or
            post.get("production_model_changed") is not False or
            post.get("model_promotion_authorized") is not False or
            post.get("real_or_paper_purchase") is not False or
            pre.get("parent_first_commit")!=site.get("first_frozen_commit")):
            return None
    outcomes=post.get("outcomes")
    if not isinstance(outcomes,dict) or set(outcomes)!=set(fields):return None
    classified={}
    for mode in fields:
        arr=pre["comparators"].get(mode)
        n=15 if mode=="coverage15" else 10
        if (not isinstance(arr,list) or len(arr)!=n or
            len(set(arr))!=n or not all(valid_combo(t) for t in arr) or
            not isinstance(outcomes[mode],bool) or outcomes[mode]!=(winning in arr)):
            return None
        if lane=="v236" and post.get("ticket_counts",{}).get(mode)!=n:return None
        classified[mode]=category(arr,winning)
    return {"race_key":key,"date_jst":key[:8],"winning_combo":winning,
            "actual_head":winning[0],"reported_head_hit":site["head_hit"],
            "categories":classified,"candidate_policy":policy}

def build(root):
    root=Path(root).resolve()
    guard(root)
    sites=verified_site_rows(root)
    output={}
    for lane in MODES:
        rows=[]
        excluded=Counter()
        for p in sorted((root/BASE/(lane+"_scored")).glob("20??????-??-??.json")):
            key=p.stem
            if not KEY.fullmatch(key):continue
            if key not in sites:
                excluded["site_result_not_cross_verified"]+=1
                continue
            record=validate_entry(root,lane,key,sites[key])
            if not record:
                excluded["frozen_source_or_scored_mismatch"]+=1
                continue
            rows.append(record)
        counts={mode:{c:sum(row["categories"][mode]==c for row in rows) for c in CATEGORIES}
                for mode in MODES[lane]}
        for mode,stats in counts.items():
            assert sum(stats.values())==len(rows), (lane,mode)
        output[lane]={"races_verified":len(rows),"miss_categories":counts,
          "excluded":dict(sorted(excluded.items())),
          "races":rows}
        if lane=="v236":
            # A different model/ranking policy is a different experiment.
            # Never pool V2 and V3 candidates or apply to old V1 results.
            by_policy={}
            for tag in (V236_V2,V236_V3):
                candidates=[r for r in rows if r["candidate_policy"]==tag]
                by_policy[tag]={
                  "matched_races":len(candidates),
                  "miss_categories":{
                    mode:{c:sum(r["categories"][mode]==c for r in candidates)
                          for c in CATEGORIES}
                    for mode in ("hit10","headsecond10")
                  },
                }
            output[lane]["headsecond_by_frozen_policy"]=by_policy
    result={"schema":"BOAT_EDGE_V253_SITE_ONLY_FROZEN_TICKET_MISS_DIAGNOSTICS_V1",
      "scope":"POST_RESULT_SITE_RESEARCH_ONLY_NO_FORMAL_FRESH_ACCESS",
      "formal_result_access":False,"production_model_changed":False,
      "accuracy_improvement_proven":False,"model_promotion_authorized":False,
      "real_or_paper_wagers_placed":0,
      "site_verified_reference_races":len(sites),
      "lanes":output,
      "method":"FROM_GIT_FROZEN_PRE_DEADLINE_TICKETS_MATCHED_TO_VERIFIED_SITE_RESULTS",
      "note":"Descriptive same-cohort ticket-coverage errors; no new model trained or promoted."}
    return result

def main(argv=None):
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--root",default=".")
    p.add_argument("--check",action="store_true")
    a=p.parse_args(argv)
    root=Path(a.root).resolve()
    result=build(root)
    text=json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n"
    dest=root/BASE/"v253_miss_diagnostics_current.json"
    if a.check:
        if not dest.exists() or dest.read_text(encoding="utf-8")!=text:
            raise SystemExit("V253_STORED_DIAGNOSTICS_OUT_OF_DATE")
    elif not dest.exists() or dest.read_text(encoding="utf-8")!=text:
        dest.write_text(text,encoding="utf-8")
    print("V253_SITE_ONLY_FROZEN_MISS_TAXONOMY",json.dumps({k:v["races_verified"] for k,v in result["lanes"].items()},sort_keys=True))
    return 0

if __name__=="__main__":sys.exit(main())
