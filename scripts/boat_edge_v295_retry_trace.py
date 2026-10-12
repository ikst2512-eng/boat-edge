#!/usr/bin/env python3
"""V295 read-only Git retry attestation for prospective SITE freeze only.

Records candidate identifiers from each *currently running* V235 attempt in
$RUNNER_TEMP, not in the published source tree. A previously unpushed race is
never backfilled, recreated or declared eligible. This script does not access
results, payout, formal predictions, combined APIs, odds or racer data.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess

RACE=re.compile(r"^20\d{6}-\d{2}-\d{2}$")
SCHEMA="BOAT_EDGE_V295_V235_PRE_RESULT_RETRY_TRACE_V1"


def tracked(repo: Path, relative: str) -> bool:
    return subprocess.run(["git", "-C", str(repo), "ls-files", "--error-unmatch",
                           "--", relative],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, check=False).returncode == 0


def candidates(repo: Path) -> set[str]:
    """Only newly made V229 pre-result attestation files count as candidates."""
    directory=repo/"data/site_autopilot/v229_evidence"
    if not directory.is_dir():
        return set()
    out=set()
    for path in directory.glob("20??????-??-??.json"):
        key=path.stem
        rel=f"data/site_autopilot/v229_evidence/{key}.json"
        if RACE.fullmatch(key) and path.is_file() and not path.is_symlink() and not tracked(repo,rel):
            out.add(key)
    return out


def persisted_parts(repo: Path, key: str) -> tuple[bool,bool]:
    """Git-tracked snapshot and V229 attestation are independent evidence.

    Requiring both does not assert the file contents or SHA passed validation.
    A snapshot-only commit is NEVER reported as persisted V229 proof.
    """
    snap=f"data/site_prediction_snapshots/{key}.json"
    proof=f"data/site_autopilot/v229_evidence/{key}.json"
    return ((repo/snap).is_file() and tracked(repo,snap),
            (repo/proof).is_file() and tracked(repo,proof))


def append_state(repo: Path, state_path: Path, attempt: int, now: datetime | None = None) -> dict:
    if attempt not in range(1,6):
        raise ValueError("V295_INVALID_RETRY_ATTEMPT")
    status_path=repo/"data/formal_status.json"
    formal=json.loads(status_path.read_text(encoding="utf-8"))
    guard=formal.get("guards") or {}
    if (not all(guard.get(k) is False for k in ("results_seen","unlock","scoring"))
            or guard.get("RESULT_UNLOCK_TOKEN") is not None
            or (formal.get("formalFirst100") or {}).get("races") != 0):
        raise RuntimeError("V295_FORMAL_FRESH_LOCK_NOT_CLOSED")
    current=candidates(repo)
    today=(now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat()
    if attempt==1:
        history={"schema":SCHEMA,"initial_candidate_keys":sorted(current),
                 "seen_candidate_keys":sorted(current),"observations":[]}
    else:
        if not state_path.is_file():
            raise RuntimeError("V295_RETRY_WITHOUT_PRIOR_OBSERVATION")
        history=json.loads(state_path.read_text(encoding="utf-8"))
        if history.get("schema")!=SCHEMA or len(history.get("observations") or [])!=attempt-1:
            raise RuntimeError("V295_RETRY_ATTESTATION_STATE_MISMATCH")
    initial=set(history["initial_candidate_keys"])
    seen=set(history.get("seen_candidate_keys") or []) | current
    if (any(not RACE.fullmatch(k) for k in seen | initial)
            or not initial.issubset(seen)):
        raise RuntimeError("V295_INVALID_SAVED_RACE_KEY")
    history["seen_candidate_keys"]=sorted(seen)
    parts={key:persisted_parts(repo,key) for key in seen if key not in current}
    latest_absent=sorted(k for k in parts if parts[k]==(False,False))
    # These records are only Git file-presence claims, NOT SHA verification.
    now_tracked=sorted(k for k in parts if parts[k]==(True,True))
    snap_only=sorted(k for k in parts if parts[k]==(True,False))
    proof_only=sorted(k for k in parts if parts[k]==(False,True))
    still_local=sorted(seen & current)
    row={"attempt":attempt,"checked_at_utc":today,
         "new_atomic_attestation_candidates":sorted(current),
         "seen_candidate_keys_still_local":still_local,
         "seen_candidate_keys_now_tracked":now_tracked,
         "seen_candidate_keys_snapshot_only_without_proof":snap_only,
         "seen_candidate_keys_proof_only_without_snapshot":proof_only,
         "seen_candidate_keys_absent_unpublished":latest_absent}
    history["observations"].append(row)
    state_path.parent.mkdir(parents=True,exist_ok=True)
    state_path.write_text(json.dumps(history,sort_keys=True,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    summary={"schema":SCHEMA,"attempt":attempt,
             "first_attempt_total":len(initial),"new_this_attempt":len(current),
             "ever_seen_proposed_total":len(seen),
             "seen_candidate_tracked":len(now_tracked),
             "seen_candidate_snapshot_only":len(snap_only),
             "seen_candidate_proof_only":len(proof_only),
             "seen_candidate_local":len(still_local),
             "seen_candidate_absent_unpublished":len(latest_absent),
             "potentially_lost_keys":latest_absent,
             "interpretation":"UNPUBLISHED_AFTER_RETRY_NOT_PROOF_OF_ELIGIBILITY_OR_PERMANENT_LOSS",
             "scope":"SITE_PRE_RESULT_ONLY_NO_FORMAL_NO_RESULTS",
             "tracked_means":"BOTH_FILES_GIT_TRACKED_NOT_SHA_VALIDATED"}
    return summary


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--repo",default=".")
    p.add_argument("--attempt",type=int,required=True)
    p.add_argument("--state-path",required=True)
    args=p.parse_args()
    result=append_state(Path(args.repo).resolve(),Path(args.state_path),args.attempt)
    print("V295_PROSPECTIVE_FREEZE_RETRY_TRACE "+json.dumps(result,sort_keys=True,ensure_ascii=False))
    summary=os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary,"a",encoding="utf-8") as fp:
            fp.write(f"\nV235 attempt {args.attempt}: {result['new_this_attempt']} new V229 source-evidence candidates; "
                     f"seen predeadline candidates tracked={result['seen_candidate_tracked']}, "
                     f"snapshot only={result['seen_candidate_snapshot_only']}, "
                     f"proof only={result['seen_candidate_proof_only']}, "
                     f"still local={result['seen_candidate_local']}, "
                     f"absent/unpublished={result['seen_candidate_absent_unpublished']} "
                     "(not proof of permanent loss or valid prediction).\n")


if __name__=="__main__":
    main()
