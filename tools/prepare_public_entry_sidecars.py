#!/usr/bin/env python3
"""Prepare create-only public entry sidecars from audited capture artifacts.

Never modifies original race snapshots. Publishing is allowed only before the
race deadline, and only when stored HTML, audit and derived entry still agree.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
from ingest_verified_start_order import ingest
from validate_pre_result_enrichment import JST

def prepare(races, raw_dir, enriched_dir, target, now=None):
    now = now or dt.datetime.now(JST)
    target=Path(target)
    report={"prepared":[],"skipped":[]}
    for src in sorted(Path(enriched_dir).glob("*.json")):
        key=src.stem
        race_file=Path(races)/(key+".json")
        html_file=Path(raw_dir)/(key+".beforeinfo.html")
        audit_file=Path(raw_dir)/(key+".beforeinfo.audit.json")
        destination=target/(key+".json")
        if destination.exists():
            report["skipped"].append({"key":key,"reason":"already_published"})
            continue
        try:
            race=json.loads(race_file.read_text(encoding="utf-8"))
            html=html_file.read_bytes()
            audit=json.loads(audit_file.read_text(encoding="utf-8"))
            proposed=json.loads(src.read_text(encoding="utf-8"))
            deadline=dt.datetime.fromisoformat(race["meta"]["date"]+"T"+race["meta"]["deadline"]+":00+09:00")
            if now>=deadline or now.tzinfo is None:
                raise ValueError("past_deadline")
            expected=ingest(race,html,audit,now=now)
            if expected!=proposed:
                raise ValueError("snapshot_not_verified")
            # Publishing a derived sidecar, not modifying data/races or model state.
            destination.parent.mkdir(parents=True,exist_ok=True)
            with destination.open("x",encoding="utf-8") as output:
                json.dump({"race_key":key,"actual_entry":expected["actual_entry"],
                           "source_audit":{"actual_entry":expected["source_audit"]["actual_entry"]}},
                          output,ensure_ascii=False,indent=2)
                output.write("\n")
            report["prepared"].append(key)
        except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
            report["skipped"].append({"key":key,"reason":str(exc).split(":")[0]})
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--races",type=Path,default=Path("data/races"))
    p.add_argument("--raw",type=Path,default=Path("artifacts/pre-result-captures"))
    p.add_argument("--enriched",type=Path,default=Path("artifacts/verified-entry-snapshots"))
    p.add_argument("--target",type=Path,default=Path("data/site_verified_entries"))
    args=p.parse_args()
    print(json.dumps(prepare(args.races,args.raw,args.enriched,args.target),ensure_ascii=False,indent=2))

if __name__=="__main__":main()
