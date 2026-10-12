#!/usr/bin/env python3
"""V318 select latest independently Git-byte-consistent predeadline snapshots.

Supports original V315 single capture plus repeatable immutable timestamped
versions. Never treats a later unverifiable snapshot as a replacement for a
valid earlier one. Read-only and no results, bets, model tuning, or formal data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from boat_edge_v314_three_source_evidence import (
    KEY, PROVIDERS, SCHEMA, audit_bundle, capture_report, parse_jst,
)


def latest_consistent_bundle(root, race_key, deadline_jst):
    if not isinstance(race_key, str) or KEY.fullmatch(race_key) is None:
        raise ValueError("INVALID_RACE_KEY")
    deadline = parse_jst(deadline_jst)
    if deadline.strftime("%Y%m%d") != race_key[:8]:
        raise ValueError("DEADLINE_DATE_MISMATCH")
    root = root.resolve()
    folder = root / "data/source_captures" / race_key[:8] / race_key
    chosen = {}
    selection = {}
    for provider in PROVIDERS:
        candidates = [folder / (provider + ".receipt.json")]
        if (folder / "versions").is_dir() and not (folder / "versions").is_symlink():
            candidates.extend(sorted((folder / "versions").glob(provider + "-*.receipt.json")))
        valid = []
        rejected = []
        for receipt_path in candidates:
            if receipt_path.is_symlink():
                rejected.append({"path": receipt_path.name, "reason": "SYMLINK_RECEIPT"})
                continue
            if not receipt_path.is_file():
                continue
            if not receipt_path.resolve().is_relative_to(root):
                rejected.append({"path": receipt_path.name, "reason": "UNSAFE_RECEIPT_PATH"})
                continue
            try:
                rec = json.loads(receipt_path.read_text(encoding="utf-8"))
                if not isinstance(rec, dict):
                    raise ValueError("NONOBJECT_RECEIPT")
                checked = capture_report(root, race_key, provider, rec, deadline)
                if not checked["document_consistent"]:
                    rejected.append({"path": receipt_path.name,
                                     "reason": ",".join(checked["reasons"])})
                    continue
                when = parse_jst(rec["captured_at_jst"])
                valid.append((when, receipt_path.name, rec))
            except (OSError, UnicodeError, ValueError, TypeError, KeyError):
                rejected.append({"path": receipt_path.name, "reason": "INVALID_RECEIPT"})
        if valid:
            best = max(valid, key=lambda row: (row[0], row[1]))
            chosen[provider] = best[2]
            selection[provider] = {
                "selected": best[1],
                "valid_versions": len(valid),
                "rejected": rejected,
            }
        else:
            selection[provider] = {
                "selected": None,
                "valid_versions": 0,
                "rejected": rejected,
                "reason": "NO_GIT_ATTESTED_PREDEADLINE_SOURCE_CAPTURE",
            }
    bundle = {
        "schema": SCHEMA,
        "race_key": race_key,
        "deadline_jst": deadline_jst,
        "captures": chosen,
    }
    evidence = audit_bundle(root, bundle)
    return {
        "model_id": "BOAT_EDGE_V318_LATEST_IMMUTABLE_SOURCE_SELECTION",
        "selection": selection,
        "bundle": bundle,
        "evidence_audit": evidence,
        "all_three_documents_consistent": evidence["all_three_document_bundles_consistent"],
        "source_contents_parsed": False,
        "source_authentication_independent": False,
        "actual_entry_independently_verified": False,
        "production_eligible": False,
        "scoring_authorized": False,
        "formal_or_result_access": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Select attested source versions, read-only")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--race-key", required=True)
    parser.add_argument("--deadline-jst", required=True)
    args = parser.parse_args()
    print(json.dumps(latest_consistent_bundle(args.root, args.race_key, args.deadline_jst),
                     sort_keys=True, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
