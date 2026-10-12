#!/usr/bin/env python3
"""V322 build an offline, immutable pre-result SITE baseline registry.

This is a research manifest, not an independent GitHub first-seen attestation.
Reads only SITE v232 snapshots. Never reads results, payouts or formal state.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from boat_edge_v320_site_v232_baseline_adapter import baseline_from_v232
from boat_edge_v318_shadow_freeze import canonical, KEY


def build_registry(root, date):
    from boat_edge_v321_site_readiness import audit, BASELINE_DIR
    readiness = audit(root, date)
    root = root.resolve()
    entries = []
    rejected = []
    for row in readiness["rows"]:
        key = row["race_key"]
        if not row["site_baseline_predeadline_metadata"]:
            rejected.append({"race_key": key, "reasons": row["baseline_reasons"]})
            continue
        path = root / BASELINE_DIR / (key + ".json")
        raw = path.read_bytes()
        baseline = baseline_from_v232(json.loads(raw))
        entries.append({
            "race_key": key,
            "source_path": (BASELINE_DIR / (key + ".json")).as_posix(),
            "source_file_sha256": hashlib.sha256(raw).hexdigest(),
            "normalized_baseline_sha256": hashlib.sha256(canonical(baseline)).hexdigest(),
            "model_id": baseline["model_id"],
            "frozen_at_jst": baseline["frozen_at_jst"],
            "deadline_jst": baseline["deadline_jst"],
            "top10_boat": baseline["top10_boat"],
            "timestamp_independently_attested": False,
            "actual_entry_independently_verified": False,
        })
    return {
        "schema": "BOAT_EDGE_V322_SITE_BASELINE_REGISTRY_V1",
        "date": date,
        "entries": entries,
        "rejected": rejected,
        "accepted_count": len(entries),
        "rejected_count": len(rejected),
        "first_github_server_receipt_verified": False,
        "three_provider_original_exhibition_verified": False,
        "model_improvement_proven": False,
        "scoring_authorized": False,
        "formal_fresh_read": False,
        "results_read": False,
    }


def main():
    parser = argparse.ArgumentParser(description="SITE pre-result registry, no results")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    print(json.dumps(build_registry(args.root, args.date),
                     ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
