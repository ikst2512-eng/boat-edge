#!/usr/bin/env python3
"""V323 check real pre-result SITE source snapshot against raw race JSON.

Read-only, conservative and no outcome access. Validates V232 source SHA
against a saved data/races file and refuses to claim third-party authenticity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from boat_edge_v320_site_v232_baseline_adapter import baseline_from_v232
from boat_edge_v318_shadow_freeze import KEY


def inspect_source(root, key):
    if not isinstance(key, str) or KEY.fullmatch(key) is None:
        raise ValueError("INVALID_RACE_KEY")
    root = root.resolve()
    baseline_path = root / "data" / "site_autopilot" / "v232_cohort" / (key + ".json")
    race_path = root / "data" / "races" / (key + ".json")
    if any(path.is_symlink() for path in (baseline_path, race_path)):
        raise ValueError("SYMLINK_SOURCE_FORBIDDEN")
    baseline_record = json.loads(baseline_path.read_text(encoding="utf-8"))
    normalized = baseline_from_v232(baseline_record)
    if normalized["race_key"] != key:
        raise ValueError("BASELINE_RACE_MISMATCH")
    race_bytes = race_path.read_bytes()
    expected = baseline_record.get("source_race_sha256")
    digest = hashlib.sha256(race_bytes).hexdigest()
    race = json.loads(race_bytes)
    if race.get("race_key") != key:
        raise ValueError("RACE_FILE_IDENTITY_MISMATCH")
    return {
        "schema": "BOAT_EDGE_V323_SITE_SOURCE_SHA_AUDIT_V1",
        "race_key": key,
        "source_race_sha256_expected": expected,
        "source_race_sha256_current": digest,
        "source_race_file_byte_match": isinstance(expected, str) and expected == digest,
        "race_card_status": (race.get("source_audit") or {}).get("race_card", {}).get("status"),
        "beforeinfo_status": (race.get("source_audit") or {}).get("beforeinfo", {}).get("status"),
        "beforeinfo_start_exhibition_present": bool((race.get("beforeinfo") or {}).get("start_exhibition")),
        "original_exhibition_three_sources_verified": False,
        "race_actual_entry_independently_verified": False,
        "source_timestamp_independently_attested": False,
        "results_read": False,
        "formal_fresh_read": False,
        "scoring_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser(description="SITE source race raw SHA audit, no results")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--race-key", required=True)
    args = parser.parse_args()
    print(json.dumps(inspect_source(args.root, args.race_key),
                     ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
