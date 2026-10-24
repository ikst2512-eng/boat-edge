#!/usr/bin/env python3
"""Verify archived beforeinfo, extract explicit entry, and write NEW snapshot.

No network, no result data, no in-place mutation. The original race JSON
remains untouched. Refuses absent/ambiguous entry or invalid audit.
Usage: python tools/ingest_verified_start_order.py RACE.json HTML AUDIT.json OUTPUT.json
"""
import argparse
import json
from pathlib import Path
from build_verified_entry_candidate import candidate
from apply_pre_result_enrichment import apply, write_new_snapshot


def ingest(race, raw, audit, now=None):
    proposal=candidate(raw,audit,race,now=now)
    return apply(race,proposal,now=now)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("race",type=Path)
    p.add_argument("source_html",type=Path)
    p.add_argument("audit",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    if a.output.resolve() in {a.race.resolve(),a.source_html.resolve(),a.audit.resolve()}:
        p.error("output must not overwrite evidence or race input")
    race=json.loads(a.race.read_text(encoding="utf-8"))
    audit=json.loads(a.audit.read_text(encoding="utf-8"))
    snapshot=ingest(race,a.source_html.read_bytes(),audit)
    write_new_snapshot(a.output,snapshot)
    print(json.dumps({"ok":True,"race_key":race["race_key"],"output":str(a.output),"actual_entry":snapshot["actual_entry"]},ensure_ascii=False))


if __name__=="__main__":
    main()
