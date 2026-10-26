#!/usr/bin/env python3
"""Read-only first Git state audit; never establishes formal prediction eligibility."""
import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

JST = timezone(timedelta(hours=9))
RACE_KEY = re.compile(r"^20\d{6}-\d{2}-\d{2}$")

def git(*args):
    p = subprocess.run(["git", *args], text=True, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, check=False)
    if p.returncode:
        raise RuntimeError("git command failed: " + " ".join(args))
    return p.stdout.strip()

def audit(key):
    if not RACE_KEY.fullmatch(key):
        raise ValueError("Invalid race key")
    path = "data/races/" + key + ".json"
    local = Path(path)
    if not local.is_file():
        return {"race_key": key, "status": "STATE_FILE_MISSING", "formal_eligible": False}
    state = json.loads(local.read_text(encoding="utf-8"))
    if state.get("race_key") != key:
        raise ValueError("Race identity mismatch")
    history = git("log", "--all", "--diff-filter=A", "--format=%H", "--", path).splitlines()
    if not history:
        return {"race_key": key, "status": "FIRST_ADDITION_NOT_FOUND",
                "formal_eligible": False}
    # Never substitute a subsequent modification for the original Git addition.
    addition = history[-1]
    commit_iso = git("show", "-s", "--format=%cI", addition)
    first_time = datetime.fromisoformat(commit_iso)
    date = key[:8]
    clock = (state.get("meta") or {}).get("deadline")
    try:
        deadline = datetime.strptime(date + " " + str(clock), "%Y%m%d %H:%M").replace(tzinfo=JST)
    except ValueError:
        deadline = None
    original_bytes = subprocess.run(["git", "show", addition + ":" + path],
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    check=False)
    if original_bytes.returncode:
        raise RuntimeError("First-addition source blob unreadable")
    original = json.loads(original_bytes.stdout)
    stored_deadline = (original.get("meta") or {}).get("deadline")
    original_cutoff = None
    try:
        original_cutoff = datetime.strptime(date + " " + str(stored_deadline), "%Y%m%d %H:%M").replace(tzinfo=JST)
    except ValueError:
        pass
    return {
        "race_key": key, "status": "FIRST_STATE_ADDITION_FOUND",
        "first_state_commit": addition,
        "first_state_git_committer_at": first_time.isoformat(),
        "first_state_blob_sha256": hashlib.sha256(original_bytes.stdout).hexdigest(),
        "initial_state_deadline": stored_deadline,
        "current_state_deadline": clock,
        "deadline_consistent": original_cutoff is not None and original_cutoff == deadline,
        "first_state_committed_before_deadline": original_cutoff is not None and first_time < original_cutoff,
        "initial_source_presence": ((original.get("current_model_input") or {}).get("source_presence") or {}),
        "initial_core7_ready": ((original.get("current_model_input") or {}).get("core7_ready")),
        "latest_core7_ready": ((state.get("current_model_input") or {}).get("core7_ready")),
        "proof_scope": "GIT_STATE_ADDITION_ONLY_NOT_CSV_OR_PREDICTION_FREEZE",
        "formal_eligible": False,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("race_keys", nargs="*", default=["20261026-21-01", "20261026-21-02"])
    parser.add_argument("--output", default="fresh_first_git_state_audit.json")
    args = parser.parse_args()
    result = {"schema": "BOAT_EDGE_FIRST_GIT_STATE_READONLY_V1",
              "results_accessed": False, "formal_unlock_authorized": False,
              "state_audits": [audit(key) for key in args.race_keys]}
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
