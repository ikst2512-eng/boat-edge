#!/usr/bin/env python3
"""V326 strict as-of-time audit of SITE race JSON pre-result metadata.

A current race JSON with postdeadline updated_at or source fetched_at MUST
NOT be treated as the frozen predeadline source, even when its SHA matches.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path

from boat_edge_v323_site_source_sha import inspect_source
from boat_edge_v320_site_v232_baseline_adapter import baseline_from_v232


def asof_audit(root, key):
    base = inspect_source(root, key)
    root = root.resolve()
    race = json.loads((root / "data/races" / (key + ".json")).read_text(encoding="utf-8"))
    saved = json.loads((root / "data/site_autopilot/v232_cohort" / (key + ".json")).read_text(encoding="utf-8"))
    baseline = baseline_from_v232(saved)
    deadline = datetime.fromisoformat(baseline["deadline_jst"])
    issues = []
    meta = race.get("meta")
    if not isinstance(meta, dict) or meta.get("phase") != "PRE_RESULT":
        issues.append("RACE_META_NOT_PRE_RESULT")
    if isinstance(meta, dict) and any(meta.get(k) is not False for k in ("results_seen", "unlock", "scoring")):
        issues.append("RACE_META_LOCK_FLAGS_INVALID")
    timestamps = [("meta.updated_at", meta.get("updated_at") if isinstance(meta, dict) else None)]
    audits = race.get("source_audit")
    if not isinstance(audits, dict):
        issues.append("SOURCE_AUDIT_MISSING")
        audits = {}
    for provider, data in audits.items():
        if not isinstance(data, dict):
            issues.append("SOURCE_AUDIT_ENTRY_INVALID:" + provider)
            continue
        if data.get("status") == "ok":
            timestamps.append(("source_audit." + provider + ".fetched_at", data.get("fetched_at")))
    for field, raw in timestamps:
        try:
            parsed = datetime.fromisoformat(raw)
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError("naive timestamp")
        except (ValueError, TypeError):
            issues.append("MISSING_OR_INVALID_TIMESTAMP:" + field)
            continue
        if parsed >= deadline:
            issues.append("POSTDEADLINE_TIMESTAMP:" + field)
    if not base["source_race_file_byte_match"]:
        issues.append("RACE_FILE_SHA_MISMATCH")
    return {
        "schema": "BOAT_EDGE_V326_SITE_ASOF_AUDIT_V1",
        "race_key": key,
        "source_race_file_byte_match": base["source_race_file_byte_match"],
        "asof_predeadline_usable": not issues,
        "issues": issues,
        "independent_source_authentication_proven": False,
        "original_exhibition_verified": False,
        "model_accuracy_proven": False,
        "formal_fresh_read": False,
        "results_read": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--race-key", required=True)
    args = parser.parse_args()
    print(json.dumps(asof_audit(args.root, args.race_key), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
