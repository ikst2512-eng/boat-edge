#!/usr/bin/env python3
"""Read-only V234 model provenance coverage audit.

Checks whether each frozen SITE prediction binds an immutable model source SHA.
Missing provenance is reported, never inferred from today's main or backfilled.
"""
import argparse
import json
import re
from pathlib import Path

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def audit(root):
    root = Path(root)
    freeze_dir = root / "data/site_autopilot/v232_cohort"
    counts = {}
    examples = {}
    total = 0
    for path in sorted(freeze_dir.glob("20??????-??-??.json")):
        total += 1
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
            if row.get("race_key") != path.stem:
                state = "race_identity_invalid"
            elif not row.get("model_id"):
                state = "model_id_missing"
            elif not HEX40.fullmatch(str(row.get("model_git_sha", ""))):
                state = "model_git_sha_missing_or_invalid"
            elif not HEX64.fullmatch(str(row.get("model_source_sha256", ""))):
                state = "model_source_sha256_missing_or_invalid"
            else:
                # Syntax alone is insufficient: independent Git blob verification
                # is required before upgrading this observation to proof.
                state = "declared_hashes_present_not_independently_verified"
        except (OSError, ValueError, UnicodeError):
            state = "unreadable_or_invalid_json"
        counts[state] = counts.get(state, 0) + 1
        examples.setdefault(state, []).append(path.stem)
    return {"schema": "BOAT_EDGE_V234_MODEL_PROVENANCE_COVERAGE_V1",
            "scope": "SITE_READ_ONLY_NOT_FORMAL_FRESH",
            "frozen_records": total, "coverage_counts": counts,
            "race_keys_by_state": examples,
            "model_source_independently_verified": False,
            "legacy_records_rewritten": False,
            "formal_fresh_unlocked": False,
            "accuracy_improvement_proven": False}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path("."))
    args = p.parse_args()
    print(json.dumps(audit(args.root), ensure_ascii=False, indent=2, sort_keys=True))
