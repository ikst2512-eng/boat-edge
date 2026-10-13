#!/usr/bin/env python3
"""V402: offline cross-source B/K race reconciliation, synthetic-tested only.

V400 normalized result rows and V401 exclusion ledger are compared with
operator-staged, permission-reviewed historical B (program) rosters.
This module never downloads, forecasts, reads Formal Fresh, or authorizes
model promotion. Source authenticity and historic predeadline availability
cannot be proven from self-attested local manifests.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path

from boat_edge_v400_five_year_history_research import (
    FIVE_YEAR_START, FIVE_YEAR_END_EXCLUSIVE, JST, _jst_instant,
    build_counts, iter_races, validate_manifest,
)
from boat_edge_v401_staged_k_bridge import EXCLUSION_REASONS, MODEL as K_MODEL

MODEL = "BOAT_EDGE_V402_OFFLINE_B_K_RECONCILIATION_RESEARCH_V1"
B_SCHEMA = "BOAT_EDGE_V402_STAGED_B_PROGRAM_DAY_V1"
B_MANIFEST = "BOAT_EDGE_V402_B_SOURCE_MANIFEST_V1"
RACE_RE = re.compile(r"[0-9]{12}\Z")


def sha(raw):
    if not isinstance(raw, bytes):
        raise ValueError("RAW_BYTES_REQUIRED")
    return hashlib.sha256(raw).hexdigest()


def _valid_race_key(key, day):
    return (
        isinstance(key, str) and RACE_RE.fullmatch(key) is not None
        and key[:8] == day.strftime("%Y%m%d")
        and 1 <= int(key[8:10]) <= 24 and 1 <= int(key[10:]) <= 12
    )


def reconcile(k_csv, k_manifest, k_audit, b_original, b_staged, b_manifest, as_of):
    if (not isinstance(k_manifest, dict) or not isinstance(k_audit, dict)
            or not isinstance(b_manifest, dict)
            or set(b_manifest) != {
                "schema", "source_sha256", "staged_sha256", "source_locator",
                "rights_evidence", "rights_review_status",
                "parser_name", "parser_version", "retrieved_at_jst",
            }):
        raise ValueError("EXACT_B_SOURCE_MANIFEST_REQUIRED")
    if b_manifest["schema"] != B_MANIFEST:
        raise ValueError("B_SOURCE_SCHEMA_INVALID")
    if b_manifest["rights_review_status"] != "OPERATOR_REVIEWED_OFFLINE_RESEARCH_ONLY":
        raise ValueError("B_RIGHTS_REVIEW_NOT_ATTESTED")
    for k in ("source_locator", "rights_evidence", "parser_name", "parser_version"):
        if not isinstance(b_manifest[k], str) or not b_manifest[k].strip():
            raise ValueError("B_SOURCE_PROVENANCE_MISSING:" + k)
    if b_manifest["source_sha256"] != sha(b_original):
        raise ValueError("B_SOURCE_BYTE_SHA_MISMATCH")
    if b_manifest["staged_sha256"] != sha(b_staged):
        raise ValueError("B_STAGED_BYTE_SHA_MISMATCH")
    _jst_instant(b_manifest["retrieved_at_jst"])
    validate_manifest(k_manifest, k_csv, as_of)
    if k_audit.get("schema") != K_MODEL or k_audit.get("normalized_csv_sha256") != sha(k_csv):
        raise ValueError("K_AUDIT_SOURCE_MISMATCH")
    if k_audit.get("source_raw_sha256") is None or k_audit.get("staged_sha256") is None:
        raise ValueError("K_ORIGINAL_SOURCE_HASH_MISSING")
    measured = build_counts(k_csv, k_manifest, as_of)
    if (k_audit.get("v400_manifest_sha256") != measured["manifest_sha256"]
            or k_audit.get("included_races") != measured["race_count"]):
        raise ValueError("K_AUDIT_COUNT_OR_MANIFEST_MISMATCH")
    try:
        stage = json.loads(b_staged.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("BAD_STAGED_B_JSON") from exc
    if not isinstance(stage, dict) or set(stage) != {"schema", "source_day", "races"}:
        raise ValueError("B_EXACT_STAGE_KEYS_REQUIRED")
    if stage["schema"] != B_SCHEMA or not isinstance(stage["races"], list):
        raise ValueError("B_STAGED_SCHEMA_INVALID")
    try:
        day = date.fromisoformat(stage["source_day"])
    except (TypeError, ValueError) as exc:
        raise ValueError("B_DAY_INVALID") from exc
    if not (FIVE_YEAR_START <= day < FIVE_YEAR_END_EXCLUSIVE and day < as_of.date()):
        raise ValueError("B_PROTECTED_OR_OUTSIDE_HISTORY_DAY")
    if k_audit.get("source_day") != day.isoformat():
        raise ValueError("B_K_SOURCE_DAY_MISMATCH")
    if not (0 < len(stage["races"]) <= 288):
        raise ValueError("B_DAY_RACE_LIST_EMPTY_OR_TOO_LARGE")
    entries_by_key = {}
    deadlines = {}
    for race in stage["races"]:
        if not isinstance(race, dict) or set(race) != {"race_key", "deadline_jst", "entries"}:
            raise ValueError("B_EXACT_RACE_KEYS_REQUIRED")
        key = race["race_key"]
        if not _valid_race_key(key, day) or key in entries_by_key:
            raise ValueError("B_INVALID_OR_DUPLICATE_RACE_KEY")
        deadline = _jst_instant(race["deadline_jst"])
        if deadline.date() != day or deadline >= as_of:
            raise ValueError("B_DEADLINE_INVALID")
        entries = race["entries"]
        if not isinstance(entries, list) or len(entries) != 6:
            raise ValueError("B_NOT_SIX_ENTRIES")
        boats = {}
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != {"boat", "racer_id"}:
                raise ValueError("B_EXACT_ENTRY_FIELDS_REQUIRED")
            boat, racer = entry["boat"], entry["racer_id"]
            if (type(boat) is not int or not 1 <= boat <= 6 or boat in boats
                    or not isinstance(racer, str)
                    or re.fullmatch(r"[0-9]{4}", racer) is None):
                raise ValueError("B_INVALID_BOAT_OR_RACER")
            boats[boat] = racer
        if set(boats) != set(range(1, 7)) or len(set(boats.values())) != 6:
            raise ValueError("B_SIX_UNIQUE_BOATS_AND_RACERS_REQUIRED")
        deadlines[key] = deadline
        entries_by_key[key] = boats

    k_keys = set()
    earliest = None
    for rows in iter_races(k_csv.decode("utf-8-sig"), as_of):
        key = rows[0][0]
        if not _valid_race_key(key, day) or key in k_keys:
            raise ValueError("K_INVALID_OR_DUPLICATE_RACE_KEY")
        if key not in entries_by_key:
            raise ValueError("K_RACE_MISSING_FROM_B_PROGRAM")
        boats = {r[3]: r[4] for r in rows}
        if boats != entries_by_key[key]:
            raise ValueError("B_K_BOAT_RACER_ID_MISMATCH")
        published = rows[0][7]
        if not published > deadlines[key]:
            raise ValueError("K_RESULT_PUBLISHED_BEFORE_B_DEADLINE")
        if earliest is None or deadlines[key] < earliest:
            earliest = deadlines[key]
        k_keys.add(key)

    exclusions = k_audit.get("excluded_race_rows")
    if not isinstance(exclusions, list) or len(exclusions) != k_audit.get("excluded_races"):
        raise ValueError("K_EXCLUSION_LEDGER_REQUIRED")
    exclusions_by_key = {}
    for entry in exclusions:
        if not isinstance(entry, dict) or set(entry) != {"race_key", "reason"}:
            raise ValueError("K_EXCLUSION_LEDGER_ROW_INVALID")
        key, reason = entry["race_key"], entry["reason"]
        if (not _valid_race_key(key, day) or key in exclusions_by_key
                or key in k_keys or reason not in EXCLUSION_REASONS):
            raise ValueError("K_EXCLUSION_INVALID_DUPLICATE_OR_INCLUDED")
        exclusions_by_key[key] = reason
    if dict(Counter(exclusions_by_key.values())) != k_audit.get("excluded_reasons"):
        raise ValueError("K_EXCLUSION_REASON_COUNTS_MISMATCH")
    excluded = set(exclusions_by_key)
    if excluded - set(entries_by_key):
        raise ValueError("K_EXCLUSION_NOT_IN_B_PROGRAM")
    unexplained = set(entries_by_key) - k_keys - excluded
    if unexplained:
        raise ValueError("B_K_UNEXPLAINED_MISSING_RACES")
    if not k_keys:
        raise ValueError("NO_B_K_RECONCILED_RACES")
    stamp = _jst_instant(b_manifest["retrieved_at_jst"])
    return {
        "schema": MODEL, "source_day": day.isoformat(),
        "k_normalized_sha256": sha(k_csv), "b_original_sha256": sha(b_original),
        "b_staged_sha256": sha(b_staged),
        "b_program_races_supplied": len(entries_by_key),
        "reconciled_six_boat_races": len(k_keys),
        "excluded_with_explicit_reason": len(excluded),
        "b_k_staged_race_universe_reconciled": True,
        "b_program_pre_first_deadline_capture_claim": stamp < earliest,
        "b_program_historic_capture_independently_authenticated": False,
        "k_post_deadline_publication_times_independently_authenticated": False,
        "national_daily_coverage_independently_verified": False,
        "license_independently_verified": False, "formal_fresh_read": False,
        "results_downloaded_by_this_script": False, "research_only": True,
        "trained_model_created": False, "accuracy_improvement_proven": False,
        "production_model_changed": False, "model_promotion_authorized": False,
        "wagers_authorized": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for arg in ("k-csv", "k-manifest", "k-audit", "b-original", "b-staged", "b-manifest"):
        p.add_argument("--" + arg, type=Path, required=True)
    p.add_argument("--as-of-jst", required=True)
    a = p.parse_args()
    obj = reconcile(
        a.k_csv.read_bytes(),
        json.loads(a.k_manifest.read_text(encoding="utf-8")),
        json.loads(a.k_audit.read_text(encoding="utf-8")),
        a.b_original.read_bytes(), a.b_staged.read_bytes(),
        json.loads(a.b_manifest.read_text(encoding="utf-8")),
        _jst_instant(a.as_of_jst),
    )
    print(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
