#!/usr/bin/env python3
"""V401: offline, permission-gated staged-K bridge; no downloads or live outcomes.

Requires operator-parsed historical K archive and a matching source-byte
digest. It cannot independently authenticate publication times or legal
data-use rights and must not be used to claim retrospective prediction proof.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from boat_edge_v400_five_year_history_research import (
    COLUMNS, JST, _jst_instant, build_counts, parse_row, _complete_race,
)

MODEL = "BOAT_EDGE_V401_OFFLINE_STAGED_K_NORMALIZER_V1"
STAGING_SCHEMA = "BOAT_EDGE_V401_STAGED_K_EXTRACT_V1"
MANIFEST_SCHEMA = "BOAT_EDGE_V401_K_SOURCE_PROVENANCE_V1"
SOURCE_KEYS = {
    "schema", "raw_source_sha256", "staged_sha256", "source_name",
    "source_locator", "rights_evidence", "rights_review_status",
    "normalization_protocol", "parser_name", "parser_version",
    "retrieved_at_jst",
}
EXCLUSION_REASONS = {
    "CANCELLED", "SCRATCH_OR_DISQUALIFICATION", "INCOMPLETE_RESULTS",
    "UNVERIFIED_ACTUAL_COURSE", "NON_STANDARD_FINISH", "SOURCE_AMBIGUOUS",
}
RACE_KEYS = {"race_key", "published_at", "entries"}
ENTRY_KEYS = {"boat", "racer_id", "actual_course", "finish"}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sorted_bytes(csv_rows):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(csv_rows)
    return buffer.getvalue().encode("utf-8")


def normalize(source_raw: bytes, staged_raw: bytes, source_manifest: dict,
              as_of: datetime):
    """One already-parsed historical K day -> V400-ready CSV, manifest and audit.

    Caller supplies all observed fields. No inference of missing course, rank,
    result date, source availability, or legal permission is performed.
    """
    if not isinstance(source_raw, bytes) or not isinstance(staged_raw, bytes):
        raise ValueError("SOURCE_AND_STAGED_BYTES_REQUIRED")
    if not isinstance(source_manifest, dict) or set(source_manifest) != SOURCE_KEYS:
        raise ValueError("EXACT_K_SOURCE_MANIFEST_REQUIRED")
    if source_manifest["schema"] != MANIFEST_SCHEMA:
        raise ValueError("INVALID_K_SOURCE_MANIFEST_SCHEMA")
    if source_manifest["rights_review_status"] != "OPERATOR_REVIEWED_OFFLINE_RESEARCH_ONLY":
        raise ValueError("HISTORICAL_SOURCE_RIGHTS_NOT_REVIEWED")
    for key in SOURCE_KEYS - {
        "schema", "raw_source_sha256", "staged_sha256", "rights_review_status"
    }:
        value = source_manifest[key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError("MISSING_K_SOURCE_PROVENANCE:" + key)
    if source_manifest["raw_source_sha256"] != _sha(source_raw):
        raise ValueError("ORIGINAL_K_BYTES_HASH_MISMATCH")
    if source_manifest["staged_sha256"] != _sha(staged_raw):
        raise ValueError("STAGED_K_BYTES_HASH_MISMATCH")
    fetched = _jst_instant(source_manifest["retrieved_at_jst"])
    if fetched > datetime.now(JST):
        raise ValueError("IMPOSSIBLE_FUTURE_RETRIEVAL_TIME")
    if not isinstance(as_of, datetime) or as_of.tzinfo is None:
        raise ValueError("AS_OF_TIME_REQUIRED")
    try:
        data = json.loads(staged_raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("INVALID_STAGED_K_JSON") from exc
    if not isinstance(data, dict) or set(data) != {
        "schema", "source_day", "races", "excluded"
    }:
        raise ValueError("EXACT_STAGED_K_KEYS_REQUIRED")
    if data["schema"] != STAGING_SCHEMA:
        raise ValueError("INVALID_STAGED_K_SCHEMA")
    day = data["source_day"]
    if not isinstance(day, str):
        raise ValueError("INVALID_SOURCE_DAY")
    try:
        date_day = datetime.strptime(day, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("INVALID_SOURCE_DAY") from exc
    if not isinstance(data["races"], list) or not isinstance(data["excluded"], list):
        raise ValueError("RACES_AND_EXCLUSIONS_MUST_BE_LISTS")
    if len(data["races"]) > 288 or len(data["excluded"]) > 288:
        raise ValueError("DAILY_K_RACE_COUNT_TOO_LARGE")
    all_race_keys = set()
    normalized = []
    counts = Counter()
    for race in data["races"]:
        if not isinstance(race, dict) or set(race) != RACE_KEYS:
            raise ValueError("EXACT_STAGED_RACE_KEYS_REQUIRED")
        key = race["race_key"]
        if not isinstance(key, str) or key[:8] != date_day.strftime("%Y%m%d"):
            raise ValueError("SOURCE_DAY_RACE_KEY_MISMATCH")
        if key in all_race_keys:
            raise ValueError("DUPLICATE_STAGED_RACE_KEY")
        all_race_keys.add(key)
        entries = race["entries"]
        if not isinstance(entries, list) or len(entries) != 6:
            raise ValueError("K_RACE_NOT_SIX_ENTRIES")
        parsed = []
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
                raise ValueError("EXACT_STAGED_ENTRY_KEYS_REQUIRED")
            row = {
                "race_key": key, "boat": str(entry["boat"]),
                "racer_id": str(entry["racer_id"]),
                "actual_course": str(entry["actual_course"]),
                "finish": str(entry["finish"]),
                "published_at": race["published_at"],
            }
            parsed.append(parse_row(row, as_of))
        parsed.sort(key=lambda r: r[3])
        _complete_race(parsed)
        for entry in parsed:
            normalized.append({
                "race_key": entry[0], "boat": entry[3], "racer_id": entry[4],
                "actual_course": entry[5], "finish": entry[6],
                "published_at": entry[7].isoformat(),
            })
        counts[key[8:10]] += 1
    excluded_counts = Counter()
    excluded_rows = []
    for exclusion in data["excluded"]:
        if not isinstance(exclusion, dict) or set(exclusion) != {"race_key", "reason"}:
            raise ValueError("EXACT_EXCLUSION_KEYS_REQUIRED")
        key, reason = exclusion["race_key"], exclusion["reason"]
        if (not isinstance(key, str) or len(key) != 12
                or not key.isascii() or not key.isdigit()
                or key[:8] != date_day.strftime("%Y%m%d")
                or not (1 <= int(key[8:10]) <= 24 and 1 <= int(key[10:]) <= 12)):
            raise ValueError("INVALID_EXCLUDED_RACE_KEY")
        if key in all_race_keys:
            raise ValueError("EXCLUDED_RACE_DUPLICATE_OR_INCLUDED")
        all_race_keys.add(key)
        if reason not in EXCLUSION_REASONS:
            raise ValueError("UNDECLARED_EXCLUSION_REASON")
        excluded_counts[reason] += 1
        excluded_rows.append({"race_key": key, "reason": reason})
    if not normalized:
        raise ValueError("NO_COMPLETE_K_RACES_IN_SOURCE_DAY")
    normalized.sort(key=lambda x: (x["race_key"], int(x["boat"])))
    normalized_csv = _sorted_bytes(normalized)
    v400_manifest = {
        "schema": "BOAT_EDGE_V400_STAGED_HISTORY_MANIFEST_V1",
        "csv_sha256": _sha(normalized_csv),
        "source_name": source_manifest["source_name"],
        "source_locator": source_manifest["source_locator"],
        "rights_evidence": source_manifest["rights_evidence"],
        "rights_review_status": "OPERATOR_REVIEWED_OFFLINE_RESEARCH_ONLY",
        "normalization_protocol": (
            f"{MODEL}:{source_manifest['parser_name']}:{source_manifest['parser_version']}"
        ),
    }
    measured = build_counts(normalized_csv, v400_manifest, as_of)
    audit = {
        "schema": MODEL, "source_day": day, "source_raw_sha256": _sha(source_raw),
        "staged_sha256": _sha(staged_raw), "normalized_csv_sha256": _sha(normalized_csv),
        "v400_manifest_sha256": measured["manifest_sha256"],
        "included_races": measured["race_count"],
        "excluded_races": sum(excluded_counts.values()),
        "excluded_reasons": dict(sorted(excluded_counts.items())),
        "excluded_race_rows": sorted(excluded_rows, key=lambda r: r["race_key"]),
        "included_by_venue": dict(sorted(counts.items())),
        "total_races_from_source_not_independently_audited": True,
        "race_coverage_complete": False,
        "source_authenticity_independently_verified": False,
        "source_availability_at_train_cutoff_independently_verified": False,
        "rights_independently_verified": False,
        "source_retrieved_after_training_cutoff": fetched >= as_of,
        "research_only": True, "formal_fresh_read": False,
        "production_model_changed": False,
        "accuracy_improvement_proven": False,
        "model_promotion_authorized": False, "wagers_authorized": False,
    }
    return normalized_csv, v400_manifest, audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-archive", type=Path, required=True,
                        help="Already-acquired local K archive. No downloads.")
    parser.add_argument("--staged-json", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--as-of-jst", required=True)
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="Private output directory; never commit archival data.")
    args = parser.parse_args()
    normalized, v400_manifest, audit = normalize(
        args.source_archive.read_bytes(),
        args.staged_json.read_bytes(),
        json.loads(args.source_manifest.read_text(encoding="utf-8")),
        _jst_instant(args.as_of_jst),
    )
    output = args.output_dir
    if output.exists() and any(output.iterdir()):
        raise ValueError("OUTPUT_DIR_MUST_BE_EMPTY")
    output.mkdir(parents=True, exist_ok=True)
    (output / "normalized.csv").write_bytes(normalized)
    (output / "v400_manifest.json").write_text(
        json.dumps(v400_manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "v401_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(audit, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
