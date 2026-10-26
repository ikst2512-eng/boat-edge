#!/usr/bin/env python3
"""Read-only prospective V232-model receipt pair gate; never retroactively enroll."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

def _git(root, *args):
    p=subprocess.run(["git",*args],cwd=root,capture_output=True)
    return p.stdout if p.returncode==0 else None

def _time(value):
    x=dt.datetime.fromisoformat(value.replace("Z","+00:00"))
    if x.tzinfo is None: raise ValueError("NAIVE_TIME")
    return x

def verify(root, key):
    root=Path(root).resolve()
    paths=[root/"data/site_autopilot/v232_cohort"/(key+".json"),
           root/"data/site_research_model_receipts"/(key+".json")]
    if any(p.is_symlink() or not p.is_file() for p in paths):
        return {"race_key":key,"eligible":False,"reason":"PAIR_FILE_MISSING"}
    try:
        freeze,receipt=[json.loads(p.read_text(encoding="utf-8")) for p in paths]
        if freeze.get("race_key")!=key or receipt.get("race_key")!=key:
            raise ValueError("KEY_MISMATCH")
        if receipt.get("schema")!="BOAT_EDGE_PROSPECTIVE_MODEL_IDENTITY_V1":
            raise ValueError("RECEIPT_SCHEMA")
        if (receipt.get("prediction_eligibility_granted") is not False or receipt.get("formal_fresh_unlocked") is not False or receipt.get("git_first_add_before_deadline_independently_verified") is not False):
            raise ValueError("RECEIPT_GUARD")
        due=_time(freeze["deadline_jst"])
        if _time(receipt["deadline_jst"])!=due:
            raise ValueError("DEADLINE_MISMATCH")
        recorded=_time(receipt["recorded_at"])
        if not recorded<due or not _time(freeze["snapshot_saved_at"])<due:
            raise ValueError("NOT_PREDEADLINE")
        modelpath=Path(receipt["model_path"])
        if modelpath.is_absolute() or ".." in modelpath.parts:
            raise ValueError("UNSAFE_MODEL_PATH")
        sha=receipt["model_git_sha"]
        if not isinstance(sha,str) or len(sha)!=40 or any(c not in "0123456789abcdef" for c in sha):
            raise ValueError("MODEL_GIT_SHA_INVALID")
        blob=_git(root,"show",f"{sha}:{modelpath.as_posix()}")
        if blob is None or hashlib.sha256(blob).hexdigest()!=receipt.get("model_source_sha256"):
            raise ValueError("MODEL_SOURCE_SHA_MISMATCH")
        # Require both immutable first Git adds before deadline. Exact SHA of the
        # current file must match its initial committed bytes; no edited history.
        for p in paths:
            rel=p.relative_to(root).as_posix()
            raw=_git(root,"log","--diff-filter=A","--reverse","--format=%H|%cI","--",rel)
            if not raw: raise ValueError("FIRST_GIT_ADD_MISSING")
            commit,when=raw.decode().splitlines()[0].split("|",1)
            initial=_git(root,"show",f"{commit}:{rel}")
            if initial!=p.read_bytes(): raise ValueError("POST_FREEZE_BYTES_CHANGED")
            # Git's second-resolution timestamp is ambiguous if it predates a
            # microsecond-resolution record. Do not silently add tolerance.
            if p==paths[1] and not recorded<=_time(when)<due:
                raise ValueError("RECEIPT_GIT_TIME_INVALID")
            if p==paths[0] and not _time(freeze["snapshot_saved_at"])<=_time(when)<due:
                raise ValueError("FREEZE_GIT_TIME_INVALID")
        return {"race_key":key,"eligible":False,
                "reason":"PAIR_CRYPTO_AND_FIRST_ADD_PASS_BUT_INDEPENDENT_HOST_RECEIPT_NOT_ESTABLISHED",
                "model_source_verified":True,"first_git_history_verified_locally":True}
    except (OSError,ValueError,KeyError,TypeError,UnicodeError) as e:
        return {"race_key":key,"eligible":False,"reason":str(e),
                "model_source_verified":False}
