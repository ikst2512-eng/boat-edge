#!/usr/bin/env python3
"""Verify immutable captured BOATRACE pre-result raw HTML against its audit.

This is a read-only verifier. It does not extract actual entry, invent values,
change a race JSON, or make network requests.
Usage: python tools/verify_pre_result_capture.py FILE.beforeinfo.html FILE.beforeinfo.audit.json RACE.json
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse,parse_qs

JST=dt.timezone(dt.timedelta(hours=9))


def verify(raw_bytes, manifest, race):
    errors=[]
    key=race.get("race_key","")
    meta=race.get("meta") or {}
    if key!=manifest.get("race_key") or not isinstance(key,str) or len(key.split("-"))!=3:
        errors.append("race_key_mismatch")
        return {"ok":False,"errors":errors}
    day,venue,rno=key.split("-")
    try:
        expected=f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd={day}&jcd={venue}&rno={int(rno)}"
        deadline=dt.datetime.fromisoformat(str(meta["date"])+"T"+str(meta["deadline"])+":00+09:00")
        fetched=dt.datetime.fromisoformat(str(manifest["fetched_at"]))
        if fetched.tzinfo is None or fetched>=deadline or fetched.astimezone(JST).date()!=deadline.date():
            errors.append("capture_not_predeadline")
        if meta["date"]!=f"{day[:4]}-{day[4:6]}-{day[6:8]}" or str(meta["venue_code"])!=venue or int(meta["race_no"])!=int(rno):
            errors.append("race_identity_mismatch")
        if manifest.get("source")!=expected:
            errors.append("source_mismatch")
    except (TypeError,ValueError,KeyError):
        errors.append("invalid_time_or_identity")
    if meta.get("phase")!="PRE_RESULT" or any(meta.get(k) is not False for k in ("results_seen","unlock","scoring")):
        errors.append("unsafe_phase")
    if manifest.get("status")!="ok" or manifest.get("kind")!="official_beforeinfo_html":
        errors.append("invalid_capture_kind")
    if type(manifest.get("bytes")) is not int or manifest["bytes"]!=len(raw_bytes) or not 0<len(raw_bytes)<=2_000_000:
        errors.append("size_mismatch")
    digest=hashlib.sha256(raw_bytes).hexdigest()
    if manifest.get("sha256")!=digest:
        errors.append("sha256_mismatch")
    if not raw_bytes.lstrip().lower().startswith((b"<!doctype html",b"<html")):
        errors.append("not_html_document")
    return {"ok":not errors,"errors":errors,"race_key":key,"sha256":digest if not errors else None}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source_html",type=Path)
    p.add_argument("audit_json",type=Path)
    p.add_argument("race_json",type=Path)
    args=p.parse_args()
    outcome=verify(args.source_html.read_bytes(),json.loads(args.audit_json.read_text()),json.loads(args.race_json.read_text()))
    print(json.dumps(outcome,ensure_ascii=False,indent=2))
    return 0 if outcome["ok"] else 1

if __name__=="__main__":
    raise SystemExit(main())
