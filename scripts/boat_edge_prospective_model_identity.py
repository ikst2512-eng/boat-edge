#!/usr/bin/env python3
"""Prospective model-source identity sidecar, research only.

Run before deadline; sidecar is NOT an eligible prediction until independently
committed to Git before deadline. Never backfill historical cohorts.
"""
import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
from pathlib import Path

KEY = re.compile(r"^20[0-9]{6}-[0-9]{2}-[0-9]{2}$")
HEX40 = re.compile(r"^[0-9a-f]{40}$")


def git(root, *args):
    p = subprocess.run(["git", *args], cwd=root, capture_output=True)
    if p.returncode:
        raise ValueError("GIT_PROVENANCE_COMMAND_FAILED")
    return p.stdout


def create(root, race_key, model_path, deadline_jst, now=None):
    root = Path(root).resolve()
    if not KEY.fullmatch(race_key):
        raise ValueError("INVALID_RACE_KEY")
    deadline = dt.datetime.fromisoformat(deadline_jst.replace("Z", "+00:00"))
    now = now or dt.datetime.now(dt.timezone.utc)
    if deadline.tzinfo is None or now.tzinfo is None or now >= deadline:
        raise ValueError("LIVE_PREDEADLINE_ONLY")
    rel = Path(model_path)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise ValueError("UNSAFE_MODEL_PATH")
    source = root / rel
    if source.is_symlink() or not source.is_file():
        raise ValueError("MODEL_SOURCE_MISSING_OR_SYMLINK")
    sha = git(root, "rev-parse", "HEAD").decode().strip()
    if not HEX40.fullmatch(sha):
        raise ValueError("INVALID_GIT_SHA")
    tracked = git(root, "ls-files", "--error-unmatch", "--", rel.as_posix())
    if not tracked:
        raise ValueError("MODEL_NOT_TRACKED")
    original = git(root, "show", f"{sha}:{rel.as_posix()}")
    local = source.read_bytes()
    if local != original:
        raise ValueError("MODEL_DIFFERS_FROM_HEAD")
    return {
        "schema": "BOAT_EDGE_PROSPECTIVE_MODEL_IDENTITY_V1",
        "scope": "SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH",
        "race_key": race_key,
        "deadline_jst": deadline.isoformat(),
        "recorded_at": now.isoformat(),
        "model_path": rel.as_posix(),
        "model_source_scope": "SINGLE_FILE_ONLY_DEPENDENCIES_NOT_ATTESTED",
        "model_git_sha": sha,
        "model_source_sha256": hashlib.sha256(original).hexdigest(),
        "git_first_add_before_deadline_independently_verified": False,
        "prediction_eligibility_granted": False,
        "accuracy_improvement_proven": False,
        "formal_fresh_unlocked": False,
    }


def save_once(root, record):
    root = Path(root).resolve()
    dest = root / "data/site_research_model_receipts" / (record["race_key"] + ".json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(record, sort_keys=True, ensure_ascii=False, indent=2) + "\n").encode()
    with dest.open("xb") as f:
        f.write(payload)
    return dest


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--race-key", required=True)
    p.add_argument("--model-path", required=True)
    p.add_argument("--deadline-jst", required=True)
    args = p.parse_args()
    record = create(args.root, args.race_key, args.model_path, args.deadline_jst)
    print(save_once(args.root, record))
