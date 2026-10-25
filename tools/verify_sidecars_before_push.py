#!/usr/bin/env python3
"""Fail closed if any staged sidecar is past deadline before Git push."""
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

JST=dt.timezone(dt.timedelta(hours=9))
PATTERN=re.compile(r"data/site_verified_entries/(\d{8})-(\d{2})-(\d{2})\.json\Z")

def verify_staged(paths, now=None):
    now=now or dt.datetime.now(JST)
    if now.tzinfo is None or not paths:
        raise ValueError("invalid_time_or_empty_publish")
    for name in paths:
        match=PATTERN.fullmatch(name)
        if not match:
            raise ValueError("unexpected_staged_path:"+name)
        day,venue,race=match.groups()
        sidecar=json.loads(Path(name).read_text(encoding="utf-8"))
        source=Path("data/races")/(day+"-"+venue+"-"+race+".json")
        original=json.loads(source.read_text(encoding="utf-8"))
        if sidecar.get("race_key") != original.get("race_key"):
            raise ValueError("race_key_mismatch")
        meta=original.get("meta") or {}
        if meta.get("phase")!="PRE_RESULT" or any(meta.get(k) is not False for k in ("results_seen","scoring","unlock")):
            raise ValueError("unsafe_race_phase")
        cutoff=dt.datetime.fromisoformat(meta["date"]+"T"+meta["deadline"]+":00+09:00")
        if now >= cutoff:
            raise ValueError("deadline_expired:"+name)
        audit=sidecar.get("source_audit",{}).get("actual_entry",{})
        order=sidecar.get("actual_entry")
        if not isinstance(order,list) or len(order)!=6 or any(type(v) is not int or v<1 or v>6 for v in order) or len(set(order))!=6:
            raise ValueError("invalid_actual_entry")
        expected_url=f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?hd={day}&jcd={venue}&rno={int(race)}"
        if audit.get("status")!="ok" or audit.get("source")!=expected_url or not isinstance(audit.get("sha256"),str) or not re.fullmatch(r"[a-f0-9]{64}",audit["sha256"]):
            raise ValueError("invalid_entry_provenance")
        fetched=dt.datetime.fromisoformat(audit["fetched_at"])
        if fetched.tzinfo is None or fetched>=cutoff:
            raise ValueError("invalid_capture_time")
    return True

def main():
    names=subprocess.check_output(["git","diff","--cached","--name-only","--diff-filter=A"],text=True).splitlines()
    all_staged=subprocess.check_output(["git","diff","--cached","--name-only"],text=True).splitlines()
    if names!=all_staged:
        raise ValueError("non_addition_staged")
    verify_staged(names)
    print(json.dumps({"ok":True,"new_sidecars":len(names)}))

if __name__=="__main__":
    try:main()
    except (ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print("PREDEADLINE_PUBLICATION_DENIED:",exc,file=sys.stderr)
        sys.exit(1)
