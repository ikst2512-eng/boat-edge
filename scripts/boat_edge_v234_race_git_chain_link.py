#!/usr/bin/env python3
"""Read-only race-level first-add and source-tree linkage diagnostic.

The Git commit first adding an on-disk prediction snapshot identifies the
repository tree at publication; it does not prove which code executed or
provide an independent GitHub reception timestamp. No eligibility decisions.
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path

CHAIN=(".github/workflows/V235.yml","scripts/boat_edge_v229_atomic_freeze.py",
       "scripts/boat_edge_v228_freeze_only.py","scripts/boat_edge_v232_pre_result_cohort.py")
KEY=re.compile(r"20[0-9]{6}-[0-9]{2}-[0-9]{2}\\Z")


def git(root,*args):
    p=subprocess.run(["git",*args],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    return p.stdout if p.returncode==0 else None


def classify(root,key):
    if not KEY.fullmatch(key):
        return {"race_key":key,"status":"INVALID_KEY"}
    root=Path(root).resolve()
    snapshot=f"data/site_prediction_snapshots/{key}.json"
    freeze=f"data/site_autopilot/v232_cohort/{key}.json"
    entries={}
    for kind,rel in (("snapshot",snapshot),("cohort",freeze)):
        file=root/rel
        if file.is_symlink() or not file.is_file():
            return {"race_key":key,"status":kind.upper()+"_FILE_MISSING"}
        log=git(root,"log","--diff-filter=A","--reverse","--format=%H|%cI","--",rel)
        if not log:
            return {"race_key":key,"status":kind.upper()+"_FIRST_ADD_MISSING"}
        try:
            sha,stamp=log.decode("utf-8").splitlines()[0].split("|",1)
            when=dt.datetime.fromisoformat(stamp)
            if when.tzinfo is None: raise ValueError("naive")
        except (UnicodeError,ValueError):
            return {"race_key":key,"status":kind.upper()+"_GIT_TIME_INVALID"}
        blob=git(root,"show",f"{sha}:{rel}")
        if blob is None or blob!=file.read_bytes():
            return {"race_key":key,"status":kind.upper()+"_BYTES_CHANGED"}
        entries[kind]={"commit":sha,"git_committer_time":when.isoformat(),
                       "sha256":hashlib.sha256(blob).hexdigest()}
    chain={}
    for rel in CHAIN:
        blob=git(root,"show",f"{entries['snapshot']['commit']}:{rel}")
        if blob is None:
            return {"race_key":key,"status":"CHAIN_BLOB_UNAVAILABLE","missing":rel}
        chain[rel]=hashlib.sha256(blob).hexdigest()
    try:
        cohort=json.loads((root/freeze).read_text(encoding="utf-8"))
        snap=json.loads((root/snapshot).read_text(encoding="utf-8"))
        due=dt.datetime.fromisoformat(cohort["deadline_jst"].replace("Z","+00:00"))
        saved=dt.datetime.fromisoformat(cohort["snapshot_saved_at"].replace("Z","+00:00"))
        if due.tzinfo is None or saved.tzinfo is None:
            raise ValueError("naive")
        if cohort.get("snapshot_sha256")!=entries["snapshot"]["sha256"]:
            return {"race_key":key,"status":"COHORT_SNAPSHOT_SHA_MISMATCH"}
        if snap.get("race_key")!=key:
            return {"race_key":key,"status":"SNAPSHOT_KEY_MISMATCH"}
        first=dt.datetime.fromisoformat(entries["snapshot"]["git_committer_time"])
        if first>=due:
            status="SNAPSHOT_COMMIT_NOT_PREDEADLINE"
        elif first<saved:
            status="SNAPSHOT_COMMIT_BEFORE_RECORDED_SAVE_AMBIGUOUS"
        else:
            status="STATIC_GIT_TREE_LINK_ONLY_NOT_EXECUTION_ATTESTATION"
    except (OSError,ValueError,TypeError,KeyError):
        return {"race_key":key,"status":"FREEZE_TIME_OR_METADATA_INVALID"}
    return {"race_key":key,"status":status,"first_add":entries,
            "snapshot_commit_static_chain_sha256":chain,
            "github_server_receive_time_independently_verified":False,
            "prediction_generator_runtime_attested":False,
            "model_full_dependency_closure_attested":False,
            "prediction_eligibility_granted":False,
            "formal_fresh_unlocked":False}


def audit(root,limit=20):
    root=Path(root).resolve()
    paths=sorted((root/"data/site_autopilot/v232_cohort").glob("20??????-??-??.json"))
    if limit<1: raise ValueError("LIMIT_MUST_BE_POSITIVE")
    rows=[classify(root,p.stem) for p in paths[-limit:]]
    counts={}
    for row in rows:counts[row["status"]]=counts.get(row["status"],0)+1
    return {"schema":"BOAT_EDGE_RACE_GIT_CHAIN_LINK_DIAGNOSTIC_V1",
            "scope":"SITE_ONLY_READ_ONLY_NOT_FORMAL_FRESH",
            "sample":"LAST_N_BY_RACE_KEY_NOT_STATISTICALLY_RANDOM",
            "sample_size":len(rows),"available_freezes":len(paths),
            "reason_counts":counts,"records":rows,
            "prospective_eligibility_established":False,
            "accuracy_improvement_proven":False}


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("."))
    p.add_argument("--limit",type=int,default=20)
    args=p.parse_args()
    print(json.dumps(audit(args.root,args.limit),ensure_ascii=False,indent=2,sort_keys=True))
