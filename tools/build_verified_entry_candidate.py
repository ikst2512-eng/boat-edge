#!/usr/bin/env python3
"""Produce a validated pre-result actual-entry candidate from archived source.

Fail closed on absent/ambiguous explicit boat identifiers. Does not modify
race JSON or publish a prediction. Pipe output to a reviewable candidate file.
"""
import argparse
import json
from pathlib import Path
from parse_explicit_start_order import parse_explicit_start_order
from verify_pre_result_capture import verify
from validate_pre_result_enrichment import validate

def candidate(raw, audit, race, now=None):
    report=verify(raw,audit,race)
    if not report["ok"]:
        raise ValueError("source_verification_failed:"+",".join(report["errors"]))
    entry=parse_explicit_start_order(raw)
    if entry is None:
        raise ValueError("actual_entry_not_explicit_or_ambiguous")
    evidence={k:audit[k] for k in ("status","source","fetched_at","sha256")}
    proposal={"actual_entry":entry,"source_audit":{"actual_entry":evidence}}
    checked=validate(race,proposal,now=now)
    if not checked["ok"]:
        raise ValueError("enrichment_validation_failed:"+",".join(checked["reasons"]))
    return proposal

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source_html",type=Path)
    p.add_argument("audit_json",type=Path)
    p.add_argument("race_json",type=Path)
    a=p.parse_args()
    print(json.dumps(candidate(a.source_html.read_bytes(),json.loads(a.audit_json.read_text()),
                               json.loads(a.race_json.read_text())),ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
