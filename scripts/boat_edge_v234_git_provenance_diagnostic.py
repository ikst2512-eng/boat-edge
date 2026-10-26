#!/usr/bin/env python3
"""Read-only diagnostics for V232 freezes excluded by the V234 scorer.

Do not modify evidence, backfill commits, or read formal predictions/results.
Only classify *provenance* problems from local Git history and frozen bytes.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess

UTC = dt.timezone.utc


def git(root, *args):
    p = subprocess.run(["git", *args], cwd=root, capture_output=True, check=False)
    return p.stdout if p.returncode == 0 else None


def classify(root, path):
    rel = path.relative_to(root).as_posix()
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        deadline = dt.datetime.fromisoformat(record["deadline_jst"].replace("Z", "+00:00"))
        saved = dt.datetime.fromisoformat(record["snapshot_saved_at"].replace("Z", "+00:00"))
        recorded = dt.datetime.fromisoformat(record["evidence_committed_at"].replace("Z", "+00:00"))
        if any(v.tzinfo is None for v in (deadline, saved, recorded)):
            return "missing_or_naive_evidence_time", None
        if not saved <= recorded < deadline:
            return "invalid_claimed_prededline_times", None
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return "invalid_freeze_metadata", None
    log = git(root, "log", "--diff-filter=A", "--reverse", "--format=%H|%cI", "--", rel)
    if log is None:
        return "git_history_unavailable", None
    if not log.strip():
        return "no_git_creation_commit", None
    try:
        commit, when = log.decode().strip().splitlines()[0].split("|", 1)
        first = dt.datetime.fromisoformat(when.replace("Z", "+00:00"))
    except (ValueError, UnicodeError):
        return "git_creation_metadata_invalid", None
    first_blob = git(root, "show", f"{commit}:{rel}")
    if first_blob is None:
        return "first_commit_blob_unavailable", commit
    if hashlib.sha256(first_blob).digest() != hashlib.sha256(path.read_bytes()).digest():
        return "frozen_bytes_changed_after_first_commit", commit
    if first < saved:
        return "git_creation_precedes_claimed_snapshot", commit
    if first >= deadline:
        return "first_git_commit_at_or_after_deadline", commit
    return "git_provenance_valid_check_other_gate", commit


def audit(root):
    root = root.resolve()
    base = root / "data/site_autopilot/v232_cohort"
    scored = root / "data/site_autopilot/v234_scored"
    groups, examples = {}, {}
    for p in sorted(base.glob("20??????-??-??.json")):
        if (scored / p.name).is_file():
            continue
        reason, commit = classify(root, p)
        groups[reason] = groups.get(reason, 0) + 1
        examples.setdefault(reason, []).append({"race_key": p.stem, "first_commit": commit})
    return {"schema": "BOAT_EDGE_V234_GIT_PROVENANCE_DIAGNOSTIC_V1",
            "scope": "READ_ONLY_SITE_RESEARCH_NOT_FORMAL_FRESH",
            "unscored_freezes": sum(groups.values()),
            "reason_counts": groups, "records": examples,
            "does_not_establish_result_availability": True,
            "does_not_backfill_evidence": True, "accuracy_improvement_proven": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()
    print(json.dumps(audit(args.root), ensure_ascii=False, indent=2, sort_keys=True))
