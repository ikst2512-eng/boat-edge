#!/usr/bin/env python3
"""Offline SITE research input replay; no outcome access or formal scoring.

An explicit V336 run report anchors each freeze digest. The exact input snapshot
must match race_source_sha256 and reproduce every V312 candidate field. This
does not authenticate input metadata, capture times, source HTML, first-seen Git
provenance or the completeness/uniqueness of a multi-run cohort.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from boat_edge_v318_shadow_freeze import canonical, parse_time
from boat_edge_v332_live_local_freeze import MODEL as FREEZE_MODEL, candidate_from_raw
from boat_edge_v339_cross_run_research_audit import _check_report
from boat_edge_v360_research_ranked120 import verify_saved_120

MODEL = "BOAT_EDGE_V343_SITE_EXACT_RACE_INPUT_REPLAY"
FALSE_FLAGS = (
    "git_first_seen_before_deadline_verified", "independent_capture_time_authenticated",
    "source_race_identity_extracted_from_raw", "original_exhibition_fields_parsed",
    "boaters_original_exhibition_verified", "kyoteibiyori_original_exhibition_verified",
    "actual_course_independently_verified", "results_read", "formal_fresh_read",
    "accuracy_improvement_proven", "model_promotion_authorized", "production_eligible",
    "scoring_authorized", "wagers_authorized",
)


def _file(root, relative):
    path = root / relative
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink():
            raise ValueError("REPLAY_ARTIFACT_SYMLINK_FORBIDDEN")
    if not path.resolve().is_relative_to(root) or not path.is_file():
        raise ValueError("REPLAY_ARTIFACT_MISSING_OR_OUTSIDE_ROOT")
    return path


def replay_one(frozen_raw, input_raw, key, expected_freeze_sha):
    if hashlib.sha256(frozen_raw).hexdigest() != expected_freeze_sha:
        raise ValueError("REPORTED_FREEZE_SHA_MISMATCH")
    frozen = json.loads(frozen_raw)
    if (not isinstance(frozen, dict) or frozen.get("model_id") != FREEZE_MODEL
            or frozen.get("race_key") != key
            or frozen.get("evidence_level") != "LOCAL_RECEIPT_RAW_SHA_ONLY"
            or frozen.get("entry_basis") != "START_EXHIBITION_PROVISIONAL_NOT_ACTUAL"):
        raise ValueError("REPLAY_FREEZE_CONTRACT_INVALID")
    if any(frozen.get(flag) is not False for flag in FALSE_FLAGS):
        raise ValueError("REPLAY_RESEARCH_ONLY_GUARDS_REQUIRED")
    digest = hashlib.sha256(input_raw).hexdigest()
    if digest != frozen.get("race_source_sha256"):
        raise ValueError("RACE_INPUT_SHA_MISMATCH")
    # Reconstruct from archived input at the frozen instant. No writes or live
    # current-day source reads; old captures without a snapshot fail closed.
    when = parse_time(frozen.get("frozen_at_jst"))
    candidate, deadline, race = candidate_from_raw(input_raw, key, when)
    if deadline.isoformat() != frozen.get("deadline_jst"):
        raise ValueError("REPLAY_DEADLINE_MISMATCH")
    encoded = canonical(candidate)
    if (canonical(frozen.get("candidate")) != encoded
            or hashlib.sha256(encoded).hexdigest() != frozen.get("candidate_sha256")):
        raise ValueError("CANDIDATE_INPUT_REPLAY_MISMATCH")
    full_120 = verify_saved_120(frozen, race, candidate)
    return {"race_key": key, "race_input_sha256": digest,
            "candidate_sha256": frozen["candidate_sha256"],
            "exact_candidate_reproduced": True,
            "saved_full_120_top10_and_head_parity_verified": full_120}


def verify(root, report):
    # Validate nonformal date/paths/digests/selection/flags before opening files.
    _check_report(report, 1)
    root = Path(root).resolve()
    rows = []
    for row in report["completed"]:
        key = row["race_key"]
        freeze_path = _file(root, row["path"])
        input_path = _file(root, f"data/source_captures/{key[:8]}/{key}/race_input.json")
        rows.append(replay_one(freeze_path.read_bytes(), input_path.read_bytes(),
                               key, row["sha256"]))
    return {
        "model_id": MODEL, "supplied_completed_freezes": len(rows),
        "candidate_replay_verified_within_supplied_report": bool(rows),
        "saved_full_120_verified_count": sum(
            r["saved_full_120_top10_and_head_parity_verified"] for r in rows),
        "all_supplied_full_120_verified": bool(rows) and all(
            r["saved_full_120_top10_and_head_parity_verified"] for r in rows),
        "rows": rows,
        "source_html_integrity_verified": False,
        "input_fields_independently_authenticated": False,
        "capture_times_independently_authenticated": False,
        "global_cohort_uniqueness_verified": False,
        "eligible_for_formal_fresh_scoring": False,
        "formal_fresh_read": False, "results_read": False,
        "scoring_authorized": False, "accuracy_improvement_proven": False,
        "production_model_changed": False, "wagers_authorized": False,
        "writes_performed": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Replay explicitly supplied V336 SITE research input snapshots")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    print(json.dumps(verify(args.root, report), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
