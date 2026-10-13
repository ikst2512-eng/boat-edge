#!/usr/bin/env python3
"""V368 explicit-cohort double replay for V366 original source-only archives.

Never discovers or backfills historical races. The caller supplies every
expected future-captured race key and an independently retained V366 manifest
SHA256. All entries are validated before any archive is read, then V367 reads
only that race's four original research files. No live SITE files, source
fetches, outcome/result endpoints, model promotion or formal cohort access.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from boat_edge_v318_shadow_freeze import canonical
from boat_edge_v367_source_only_replay import replay_one

MODEL = "BOAT_EDGE_V368_EXPLICIT_COHORT_SOURCE_ONLY_DUAL_REPLAY"
INDEX = "BOAT_EDGE_V368_EXPLICIT_SOURCE_ONLY_COHORT_V1"
KEY = re.compile(r"^20\d{6}-(?:0[1-9]|1\d|2[0-4])-(?:0[1-9]|1[0-2])$")
SHA = re.compile(r"^[0-9a-f]{64}$")
INDEX_FLAGS = ("source_capture_only", "no_result_inputs", "no_formal_fresh",
               "no_model_promotion")


def validate_index(index):
    """Validate an entire explicit selection set *before* opening anything."""
    if (not isinstance(index, dict) or set(index) !=
            {"schema", "expected", "declared_expected_count", *INDEX_FLAGS} or
            index.get("schema") != INDEX or
            any(index.get(k) is not True for k in INDEX_FLAGS)):
        raise ValueError("V368_EXPLICIT_RESEARCH_ONLY_INDEX_REQUIRED")
    rows = index["expected"]
    if (not isinstance(rows, list) or not 1 <= len(rows) <= 100 or
            type(index["declared_expected_count"]) is not int or
            index["declared_expected_count"] != len(rows)):
        raise ValueError("V368_INVALID_EXPECTED_RACE_COUNT")
    keys = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"race_key", "manifest_sha256"}:
            raise ValueError("V368_NO_IMPLICIT_PATH_OR_EXTRA_INDEX_FIELDS")
        key, sha = row["race_key"], row["manifest_sha256"]
        if (not isinstance(key, str) or KEY.fullmatch(key) is None
                or key.startswith("20261001-")):
            raise ValueError("V368_INVALID_OR_FORMAL_COHORT_RACE_KEY")
        if not isinstance(sha, str) or SHA.fullmatch(sha) is None:
            raise ValueError("V368_MANIFEST_SHA_REQUIRED")
        keys.append(key)
    if len(set(keys)) != len(keys):
        raise ValueError("V368_DUPLICATE_COHORT_RACE_KEY")
    if keys != sorted(keys):
        raise ValueError("V368_COHORT_KEY_ORDER_MUST_BE_CANONICAL")
    return rows


def audit(root, index):
    """Two entirely separate read-only V367 passes, no discovery or writes."""
    rows = validate_index(index)
    root = Path(root).resolve()
    accepted, rejected = [], []
    for item in rows:
        key, expected = item["race_key"], item["manifest_sha256"]
        try:
            run1 = replay_one(root, key, expected)
            run2 = replay_one(root, key, expected)
            bytes1, bytes2 = canonical(run1), canonical(run2)
            if bytes1 != bytes2:
                raise ValueError("V368_TWO_INDEPENDENT_REPLAY_OUTPUTS_DIVERGED")
            if (run1.get("status") != "LOCAL_ARCHIVE_REPLAY_PASS_NOT_SOURCE_AUTHENTICATION"
                    or run1.get("manifest_sha256") != expected
                    or run1.get("race_key") != key
                    or any(run1.get(flag) is not False for flag in (
                        "independent_source_or_server_timestamp_authenticated",
                        "live_race_freeze_proven", "independent_actual_course_proven",
                        "results_read", "formal_fresh_read",
                        "accuracy_improvement_proven", "writes_performed"))):
                raise ValueError("V368_UNVERIFIED_REPLAY_PASS_CLAIM")
            accepted.append({
                "race_key": key, "manifest_sha256": expected,
                "replay_sha256": hashlib.sha256(bytes1).hexdigest(),
                "two_independent_replay_outputs_byte_identical": True,
            })
        except (OSError, ValueError, TypeError, KeyError, UnicodeError) as exc:
            rejected.append({"race_key": key, "reason": str(exc)})
    pass_count = len(accepted)
    complete = pass_count == len(rows) and not rejected
    return {
        "model_id": MODEL,
        "status": ("ALL_DECLARED_LOCAL_SOURCE_ARCHIVES_REPLAYED_NOT_FORMAL"
                   if complete else "DECLARED_LOCAL_SOURCE_ARCHIVES_INCOMPLETE_OR_INVALID"),
        "expected_count": len(rows),
        "replayed_count": pass_count,
        "rejected_count": len(rejected),
        "accepted": accepted,
        "rejected": rejected,
        "all_declared_sources_locally_verified": complete,
        "replay_report_digest_sha256": hashlib.sha256(canonical(accepted)).hexdigest(),
        "cross_run_first_seen_or_server_time_verified": False,
        "external_source_authenticity_verified": False,
        "boaters_and_kyoteibiyori_original_exhibition_verified": False,
        "v336_research_freeze_proven": False,
        "research_full_3x120_rankings_verified": False,
        "results_read": False, "formal_fresh_read": False,
        "accuracy_improvement_proven": False,
        "production_model_changed": False,
        "writes_performed": False,
    }


def main():
    p = argparse.ArgumentParser(description="Offline explicit V366 archive dual replay")
    p.add_argument("--root", type=Path, default=Path("."))
    p.add_argument("--index", type=Path, required=True,
                   help="Caller-supplied canonical JSON with 1..100 exact expected race keys + SHA")
    args = p.parse_args()
    # Explicit selection file is provided by the caller, not discovered from
    # data/results, site predictions, Git, or any external network service.
    if args.index.is_symlink() or not args.index.is_file():
        raise ValueError("V368_INDEX_FILE_NOT_REGULAR")
    raw = args.index.read_bytes()
    if len(raw) > 32_768:
        raise ValueError("V368_INDEX_OVERSIZE")
    try:
        index = json.loads(raw)
    except (UnicodeError, ValueError) as exc:
        raise ValueError("V368_INDEX_JSON_INVALID") from exc
    if canonical(index) + b"\n" != raw:
        raise ValueError("V368_INDEX_NOT_CANONICAL")
    print(json.dumps(audit(args.root, index), ensure_ascii=False,
                     sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
