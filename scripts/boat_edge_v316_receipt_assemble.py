#!/usr/bin/env python3
"""V316 assemble immutable V315 receipts and run V314 read-only audit.

Never downloads source pages or reads race results. Missing provider receipts
remain explicit absences; no source authenticity or feature extraction claim.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from boat_edge_v314_three_source_evidence import (
    KEY, PROVIDERS, SCHEMA, audit_bundle, parse_jst,
)


def assemble(root, race_key, deadline_jst):
    if not isinstance(race_key, str) or KEY.fullmatch(race_key) is None:
        raise ValueError("INVALID_RACE_KEY")
    if parse_jst(deadline_jst).strftime("%Y%m%d") != race_key[:8]:
        raise ValueError("DEADLINE_DATE_MISMATCH")
    root = root.resolve()
    folder = root / "data" / "source_captures" / race_key[:8] / race_key
    captures = {}
    unreadable = {}
    for provider in PROVIDERS:
        receipt_path = folder / (provider + ".receipt.json")
        if receipt_path.is_symlink():
            unreadable[provider] = "RECEIPT_SYMLINK_NOT_ALLOWED"
            continue
        if not receipt_path.is_file():
            unreadable[provider] = "RECEIPT_MISSING"
            continue
        try:
            data = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            unreadable[provider] = "INVALID_RECEIPT_JSON"
            continue
        if not isinstance(data, dict):
            unreadable[provider] = "INVALID_RECEIPT_OBJECT"
            continue
        captures[provider] = data
    bundle = {
        "schema": SCHEMA,
        "race_key": race_key,
        "deadline_jst": deadline_jst,
        "captures": captures,
    }
    audit = audit_bundle(root, bundle)
    return {
        "model_id": "BOAT_EDGE_V316_THREE_SOURCE_RECEIPT_ASSEMBLER",
        "bundle": bundle,
        "evidence_audit": audit,
        "missing_or_invalid_receipts": unreadable,
        "ready_for_research_review": bool(audit["all_three_document_bundles_consistent"]
                                          and not unreadable),
        "verified_race_identity_from_page": False,
        "original_exhibition_values_parsed": False,
        "actual_entry_verified": False,
        "candidate_scoring_authorized": False,
        "model_promotion_authorized": False,
        "formal_or_result_access": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Audit immutable V315 receipts, no result access")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--race-key", required=True)
    parser.add_argument("--deadline-jst", required=True)
    args = parser.parse_args()
    print(json.dumps(assemble(args.root, args.race_key, args.deadline_jst),
                     ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
