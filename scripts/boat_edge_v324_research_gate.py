#!/usr/bin/env python3
"""V324 read-only gate matrix for source-backed prospective research.

This is an evidence readiness decision, not an outcome scoring engine.
It cannot authorize model promotion or real wagers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIREMENTS = (
    "baseline_predeadline",
    "candidate_predeadline",
    "same_race",
    "both_sha256_consistent",
    "official_raw_verified",
    "boaters_raw_verified",
    "kyoteibiyori_raw_verified",
    "original_exhibition_fields_verified",
    "scratch_status_verified",
    "actual_course_independently_verified",
    "server_first_seen_before_deadline_verified",
)


def evaluate(evidence):
    if not isinstance(evidence, dict) or set(evidence) != set(REQUIREMENTS):
        raise ValueError("EXACT_EVIDENCE_KEYS_REQUIRED")
    if any(type(value) is not bool for value in evidence.values()):
        raise ValueError("BOOLEAN_EVIDENCE_REQUIRED")
    missing = [key for key in REQUIREMENTS if not evidence[key]]
    return {
        "schema": "BOAT_EDGE_V324_RESEARCH_EVIDENCE_GATE_V1",
        "checks": {key: evidence[key] for key in REQUIREMENTS},
        "missing": missing,
        "ready_for_independent_review": not missing,
        "source_authenticated_by_this_tool": False,
        "result_access_performed": False,
        "formal_fresh_access_performed": False,
        "model_accuracy_evaluated": False,
        "model_promotion_authorized": False,
        "wagers_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Read-only prospective evidence gate")
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    obj = json.loads(args.evidence.read_text(encoding="utf-8"))
    print(json.dumps(evaluate(obj), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
