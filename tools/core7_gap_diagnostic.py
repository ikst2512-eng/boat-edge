#!/usr/bin/env python3
"""Read-only CORE7 failure breakdown. No results or payout access."""
import collections
import json
from pathlib import Path

ROLES=("race_cards","stt","tkz","sui","original_exhibition")

def diagnose(root,day):
    root=Path(root)
    counts=collections.Counter()
    reasons={role:collections.Counter() for role in ROLES}
    examples={role:[] for role in ROLES}
    field_failures=[]
    for path in sorted((root/"data/races").glob(f"{day}-??-??.json")):
        try:
            doc=json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, UnicodeError):
            counts["unreadable"]+=1
            continue
        if not isinstance(doc,dict) or doc.get("race_key")!=path.stem:
            counts["bad_identity"]+=1
            continue
        counts["race_documents"]+=1
        current=doc.get("current_model_input") or {}
        if current.get("core7_ready") is True:
            counts["core7_ready"]+=1
            continue
        counts["core7_failed"]+=1
        presence=current.get("source_presence") or {}
        audits=doc.get("source_audit") or {}
        missing=[role for role in ROLES if presence.get(role) is not True]
        if not missing:
            counts["all_five_present_but_failed"]+=1
            if len(field_failures)<20:field_failures.append(path.stem)
        else:
            counts["missing_source_races"]+=1
        for role in missing:
            counts["missing_"+role]+=1
            audit=audits.get(role) or {}
            reason=str(audit.get("availability_reason") or audit.get("status") or "not_recorded")
            reasons[role][reason]+=1
            if len(examples[role])<8: examples[role].append({"race_key":path.stem,"reason":reason})
    return {"schema":"core7-gap-diagnostic-v1","day":day,
            "scope":"site_only_read_only_not_formal_fresh",
            "counts":dict(sorted(counts.items())),
            "reasons":{k:dict(sorted(v.items())) for k,v in reasons.items()},
            "examples":examples,
            "all_sources_present_failed_examples":field_failures,
            "notes":["Source reasons describe stored observations, not proof of final publication",
                     "Protected historical inputs are never modified",
                     "CORE7 passing does not certify formal Fresh"]}
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("day")
    p.add_argument("--root",default=".")
    a=p.parse_args()
    if len(a.day)!=8 or not a.day.isdigit():p.error("day must be YYYYMMDD")
    print(json.dumps(diagnose(a.root,a.day),ensure_ascii=False,indent=2))
