#!/usr/bin/env python3
"""Read-only site V229 eligibility diagnostics. Never reads outcomes or formal data."""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

JST=timezone(timedelta(hours=9))
def load(p):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError):
        return {}
def timestamp(s):
    try:
        d=datetime.fromisoformat(str(s))
        return d if d.tzinfo else None
    except (ValueError, TypeError, OverflowError):
        return None
def fresh(item, now, minutes):
    if item.get("status")!="ok":return False
    t=timestamp(item.get("fetched_at"))
    return t is not None and 0 <= (now-t).total_seconds() <= minutes*60
def inspect(root, now):
    day=now.astimezone(JST).strftime("%Y%m%d")
    out=[]
    for p in sorted((root/"data/site_races").glob(f"{day}-??-??.json")):
        race=load(p); key=p.stem; reasons=[]
        meta=race.get("race") or race.get("meta") or {}
        deadline=str(meta.get("deadline") or "")
        try:
            dl=datetime.fromisoformat(f"{day[:4]}-{day[4:6]}-{day[6:]}T{deadline}:00+09:00")
            mins=(dl-now).total_seconds()/60
        except (ValueError, TypeError):
            mins=None
        if mins is None:reasons.append("deadline_unknown")
        elif not 2<=mins<=10:reasons.append("outside_2_to_10_min_window")
        audit=race.get("source_audit") or {}
        if not fresh(audit.get("race_card") or {},now,16):reasons.append("race_card_missing_or_stale")
        if not fresh(audit.get("beforeinfo") or {},now,15):reasons.append("beforeinfo_missing_or_stale")
        scratch=load(root/"data/site_scratches_v182"/f"{key}.json")
        if (scratch.get("race_key")!=key or scratch.get("blocked") is not False
            or scratch.get("race_card_source_status")!="ok"
            or scratch.get("official_beforeinfo_source_status")!="ok"
            or (lambda t:t is None or not 0<=(now-t).total_seconds()<=900)(timestamp(scratch.get("checked_at")))):
            reasons.append("scratch_unverified_or_stale")
        odds=load(root/"data/site_odds"/f"{key}.json")
        rows=odds.get("trifecta_odds") or {}
        if odds.get("race_key")!=key or odds.get("phase")!="PRE_RESULT_PURCHASE_ONLY" or len(rows)!=120:
            reasons.append("odds_120_missing_or_invalid")
        else:
            t=timestamp(odds.get("fetched_at"))
            if t is None or not 0<=(now-t).total_seconds()<=900:reasons.append("odds_stale")
        if (root/"data/site_prediction_snapshots"/f"{key}.json").exists():reasons.append("snapshot_already_exists")
        out.append({"race_key":key,"minutes_to_deadline":None if mins is None else round(mins,2),"reasons":reasons,"preliminary_eligible":not reasons})
    return {"schema":"V229_READ_ONLY_ELIGIBILITY_DIAGNOSTIC_V1","as_of":now.isoformat(),"date":day,
            "scope":"SITE_ONLY_PRE_RESULT_NOT_FORMAL_FRESH","caveat":"Preliminary checks; does not certify full V229 eligibility, source authenticity, or 120-odds byte SHA.",
            "race_count":len(out),"reason_counts":dict(sorted(Counter(x for row in out for x in row["reasons"]).items())),
            "races":out}
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");ap.add_argument("--at",default=None)
    args=ap.parse_args()
    now=datetime.fromisoformat(args.at) if args.at else datetime.now(timezone.utc)
    if now.tzinfo is None:ap.error("--at must include timezone")
    print(json.dumps(inspect(Path(args.root),now),ensure_ascii=False,indent=2,sort_keys=True))
