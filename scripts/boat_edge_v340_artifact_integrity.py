#!/usr/bin/env python3
"""V340 offline, read-only integrity check of explicit V336 SITE research artifacts.

Verify reported frozen JSON SHA256 and the exact local receipt/raw HTML bytes
for official, BOATERS and 競艇日和. No result/outcome/payout/odds/formal fetch,
no network, no prediction/scoring, and no on-disk writes. These checks never
authenticate the source website or independently prove capture timestamps.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from boat_edge_v314_three_source_evidence import KEY, PROVIDERS, SHA
from boat_edge_v318_shadow_freeze import parse_time
from boat_edge_v332_live_local_freeze import _local_capture
from boat_edge_v335_site_paired_outcomes import _validate_frozen

MODEL = "BOAT_EDGE_V340_SITE_RESEARCH_ARTIFACT_BYTES_AUDIT"
RUNNER = "BOAT_EDGE_V334_SITE_RESEARCH_BATCH_ONLY"
MODES = {"national_only", "national_motor", "national_motor_st"}


def _guarded_report(report):
    if not isinstance(report, dict) or report.get("model_id") != RUNNER:
        raise ValueError("V334_REPORT_REQUIRED")
    for name, expected in (
        ("capture_requested", True),
        ("results_read", False),
        ("formal_fresh_read", False),
        ("accuracy_improvement_proven", False),
        ("production_model_changed", False),
        ("wagers_authorized", False),
    ):
        if report.get(name) is not expected:
            raise ValueError("RESEARCH_ONLY_REPORT_FLAG_REQUIRED:" + name)
    window = report.get("window")
    if not isinstance(window, dict):
        raise ValueError("WINDOW_REQUIRED")
    date = window.get("date")
    if not isinstance(date, str) or re.fullmatch(r"20[0-9]{6}", date) is None or date == "20261001":
        raise ValueError("NONFORMAL_DATE_REQUIRED")
    candidates = window.get("candidates")
    completed = report.get("completed")
    if not isinstance(candidates, list) or not isinstance(completed, list):
        raise ValueError("CANDIDATES_AND_COMPLETED_LIST_REQUIRED")
    if type(report.get("completed_count")) is not int or report["completed_count"] != len(completed):
        raise ValueError("COMPLETED_COUNT_MISMATCH")
    selected = []
    for row in candidates:
        key = row.get("race_key") if isinstance(row, dict) else None
        if not isinstance(key, str) or KEY.fullmatch(key) is None or key[:8] != date:
            raise ValueError("INVALID_SELECTED_RACE")
        selected.append(key)
    if len(set(selected)) != len(selected) or len(selected) > 12:
        raise ValueError("INVALID_SELECTED_CARDINALITY")
    checked = set()
    for row in completed:
        if not isinstance(row, dict):
            raise ValueError("INVALID_COMPLETED_ROW")
        key = row.get("race_key")
        if not isinstance(key, str) or key not in selected or key in checked:
            raise ValueError("DUPLICATE_OR_UNSELECTED_COMPLETION")
        checked.add(key)
        if row.get("path") != f"data/research_local_v332/{date}/{key}.json":
            raise ValueError("NONCANONICAL_COMPLETED_PATH")
        digest = row.get("sha256")
        if not isinstance(digest, str) or SHA.fullmatch(digest) is None:
            raise ValueError("INVALID_COMPLETED_SHA")
        modes = row.get("modes")
        if not isinstance(modes, list) or set(modes) != MODES or len(modes) != 3:
            raise ValueError("PREDECLARED_MODES_REQUIRED")
    return date, completed


def _read_no_symlink(root, relative):
    # Relative path is constructed solely from regex-validated race key.
    path = root / relative
    parent = path
    while parent != root:
        if parent.is_symlink():
            raise ValueError("ARTIFACT_SYMLINK_FORBIDDEN")
        parent = parent.parent
    if not path.is_file() or not path.resolve().is_relative_to(root):
        raise ValueError("ARTIFACT_FILE_MISSING_OR_OUTSIDE_ROOT")
    return path.read_bytes()


def audit_one(root, row):
    key = row["race_key"]
    relative = Path("data/research_local_v332") / key[:8] / (key + ".json")
    raw = _read_no_symlink(root, relative)
    if hashlib.sha256(raw).hexdigest() != row["sha256"]:
        raise ValueError("FROZEN_JSON_BYTES_SHA_MISMATCH")
    frozen = json.loads(raw)
    validated_key, deadline, modes = _validate_frozen(frozen)
    if validated_key != key:
        raise ValueError("FROZEN_RACE_ID_MISMATCH")
    if set(modes) != MODES or set(row["modes"]) != MODES:
        raise ValueError("FROZEN_MODES_MISMATCH")
    frozen_time = parse_time(frozen.get("frozen_at_jst"))
    if (frozen_time >= deadline or
            frozen.get("entry_basis") != "START_EXHIBITION_PROVISIONAL_NOT_ACTUAL"):
        raise ValueError("FROZEN_PREDEADLINE_ENTRY_REQUIRED")
    if frozen["candidate"].get("deadline_jst") != deadline.isoformat():
        raise ValueError("CANDIDATE_DEADLINE_MISMATCH")
    if frozen["candidate"].get("model_id") != "BOAT_EDGE_V312_UNCALIBRATED_EXHIBITION_ENTRY_ABLATION":
        raise ValueError("ORIGINAL_RESEARCH_MODEL_REQUIRED")
    for provider in PROVIDERS:
        capture_dir = Path("data/source_captures") / key[:8] / key
        _read_no_symlink(root, capture_dir / (provider + ".html"))
        _read_no_symlink(root, capture_dir / (provider + ".receipt.json"))
        # _local_capture validates canonical local receipt path, provider URL,
        # race ID, predeadline timestamp, fields=[] and SHA of raw HTML bytes.
        receipt = _local_capture(root, key, provider, deadline, frozen_time)
        if receipt != frozen["source_receipts"][provider]:
            raise ValueError("FROZEN_RECEIPT_VS_RAW_MISMATCH:" + provider)
    return {
        "race_key": key, "reported_sha256": row["sha256"],
        "raw_capture_provider_count": len(PROVIDERS),
        "frozen_json_bytes_sha_match": True,
        "three_local_raw_html_sha_matches": True,
        "local_receipts_match_frozen_copy": True,
        "predeadline_timestamps_self_reported_only": True,
        "provider_identity_extracted_from_raw_html": False,
        "original_exhibition_fields_parsed": False,
        "site_race_card_original_bytes_rehashed": False,
    }


def audit(root, report):
    date, completed = _guarded_report(report)  # Reject unsafe scope before reading files.
    root = Path(root).resolve()
    verified, rejected = [], []
    for row in completed:
        try:
            verified.append(audit_one(root, row))
        except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
            rejected.append({"race_key": row["race_key"], "reason": str(exc)})
    return {
        "model_id": MODEL, "date": date,
        "reported_completed": len(completed),
        "local_artifacts_verified": len(verified),
        "local_artifacts_rejected": len(rejected),
        "verified": verified, "rejected": rejected,
        "all_reported_artifacts_locally_consistent": bool(completed) and len(rejected) == 0,
        "complete_actions_history_or_global_uniqueness_attested": False,
        "raw_source_identity_independently_verified": False,
        "source_capture_time_independently_attested": False,
        "original_exhibition_verified": False,
        "formal_fresh_read": False, "results_read": False,
        "accuracy_improvement_proven": False,
        "production_model_changed": False,
        "wagers_authorized": False, "writes_performed": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Inspect an explicitly supplied V336 artifact bundle offline")
    parser.add_argument("--root", required=True, type=Path,
                        help="Unpacked Actions artifact root (data/research_local_v332, data/source_captures)")
    parser.add_argument("--report", required=True, type=Path,
                        help="Explicit V336 v336_report.json")
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    print(json.dumps(audit(args.root, report), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
