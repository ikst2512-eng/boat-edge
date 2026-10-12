#!/usr/bin/env python3
"""V318 research-only immutable predeadline shadow freeze.

Consumes a V316 report and candidate model output; never reads results.
A source receipt bundle is not authenticated third-party race data. This
records a proposal for future prospective audit, not a production forecast.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re

JST = timezone(timedelta(hours=9))
KEY = re.compile(r"^20[0-9]{6}-(?:0[1-9]|1[0-9]|2[0-4])-(?:0[1-9]|1[0-2])$")
MODEL = "BOAT_EDGE_V318_SHADOW_FREEZE_RESEARCH_ONLY"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def parse_time(value):
    if not isinstance(value, str) or not value.endswith("+09:00"):
        raise ValueError("JST_TIMESTAMP_REQUIRED")
    dt = datetime.fromisoformat(value)
    if dt.utcoffset() != timedelta(hours=9):
        raise ValueError("JST_OFFSET_REQUIRED")
    return dt


def build_freeze(bundle_report, candidate, now):
    if not isinstance(bundle_report, dict) or not isinstance(candidate, dict):
        raise ValueError("INVALID_RESEARCH_INPUT")
    bundle = bundle_report.get("bundle")
    evidence = bundle_report.get("evidence_audit")
    if not isinstance(bundle, dict) or not isinstance(evidence, dict):
        raise ValueError("V316_EVIDENCE_REQUIRED")
    key = bundle.get("race_key")
    if not isinstance(key, str) or KEY.fullmatch(key) is None:
        raise ValueError("INVALID_RACE_KEY")
    deadline = parse_time(bundle.get("deadline_jst"))
    now = now.astimezone(JST) if isinstance(now, datetime) and now.tzinfo else None
    if now is None or now >= deadline:
        raise ValueError("SHADOW_FREEZE_NOT_BEFORE_DEADLINE")
    if (not bundle_report.get("ready_for_research_review")
            or not evidence.get("all_three_document_bundles_consistent")):
        raise ValueError("THREE_SOURCE_DOCUMENT_BUNDLE_NOT_READY")
    if candidate.get("race_key") != key:
        raise ValueError("CANDIDATE_RACE_KEY_MISMATCH")
    if candidate.get("production_eligible") is not False or candidate.get("scoring_authorized") is not False:
        raise ValueError("CANDIDATE_MUST_BE_RESEARCH_ONLY")
    if candidate.get("calibrated") is not False or candidate.get("improvement_proven") is not False:
        raise ValueError("UNVERIFIED_MODEL_PROMOTION_CLAIM")
    modes = candidate.get("modes")
    if not isinstance(modes, dict) or not modes:
        raise ValueError("CANDIDATE_MODES_MISSING")
    for mode in modes.values():
        if not isinstance(mode, dict):
            raise ValueError("INVALID_MODE")
        tickets = mode.get("top10_boat_research_only")
        if not isinstance(tickets, list) or len(tickets) != 10:
            raise ValueError("TEN_DISTINCT_BOAT_TICKETS_REQUIRED")
        if any(not isinstance(ticket, str) for ticket in tickets):
            raise ValueError("INVALID_TICKET")
        if len(set(tickets)) != 10:
            raise ValueError("TEN_DISTINCT_BOAT_TICKETS_REQUIRED")
        for ticket in tickets:
            if not isinstance(ticket, str):
                raise ValueError("INVALID_TICKET")
            parts = ticket.split("-")
            if len(parts) != 3 or any(x not in "123456" or len(x) != 1 for x in parts) or len(set(parts)) != 3:
                raise ValueError("INVALID_TICKET")
    # Canonical source and candidate digests are attestations of bytes passed
    # to this function, NOT of upstream website authenticity.
    source_digest = hashlib.sha256(canonical(bundle)).hexdigest()
    candidate_digest = hashlib.sha256(canonical(candidate)).hexdigest()
    return {
        "model_id": MODEL,
        "race_key": key,
        "deadline_jst": deadline.isoformat(),
        "frozen_at_jst": now.isoformat(timespec="seconds"),
        "source_bundle_sha256": source_digest,
        "candidate_sha256": candidate_digest,
        "candidate_model_id": candidate.get("model_id"),
        "entry_basis": candidate.get("entry_basis"),
        "research_top10_by_mode": {
            name: mode["top10_boat_research_only"] for name, mode in modes.items()
        },
        "raw_source_identity_authenticated": False,
        "first_github_server_receipt_before_deadline_verified": False,
        "independent_actual_entry_verified": False,
        "original_exhibition_values_verified": False,
        "source_byte_digest_revalidated": False,
        "prediction_improvement_proven": False,
        "model_promotion_authorized": False,
        "wagers_authorized": False,
        "results_read": False,
        "formal_fresh_read": False,
    }


def freeze_file(root, report, candidate, now):
    frozen = build_freeze(report, candidate, now)
    key = frozen["race_key"]
    root = root.resolve()
    target = root / "data" / "research_shadow_v318" / key[:8] / (key + ".json")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or target.exists():
        raise ValueError("SHADOW_FREEZE_ALREADY_EXISTS")
    # Exclusive file creation; never backfill or replace.
    with target.open("xb") as stream:
        stream.write(canonical(frozen) + b"\n")
    return {"path": target.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "record": frozen}


def main():
    parser = argparse.ArgumentParser(description="One-time offline PRE_RESULT shadow freeze")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--v316-report", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.v316_report.read_text(encoding="utf-8"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    result = freeze_file(args.root, report, candidate, datetime.now(JST))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
