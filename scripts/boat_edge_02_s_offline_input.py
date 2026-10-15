#!/usr/bin/env python3
"""BOAT EDGE 02: research-only offline S-priority PRE_RESULT input normalization.

Processes only an operator-staged, individually permission-reviewed pre-race
normalized CSV file with a cryptographically pinned byte hash. Never performs HTTP,
reads result files, unlocks Formal Fresh, trains models, or writes site artifacts.
Provenance timestamps and source rights are SELF-ATTESTED, not independently proven.
Third-party provider exports (BOATERS, Kyoteibiyori, DB, Boat-and-Data,
BoatraceCSV) are NOT admissible as inputs without a separate review and code change.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

JST = timezone(timedelta(hours=9))
SCHEMA = "BOAT_EDGE_02_S_OFFLINE_PREDEADLINE_V1"
MANIFEST_SCHEMA = "BOAT_EDGE_02_OPERATOR_STAGED_PREDEADLINE_RACECARD_V1"
SOURCE_KIND = "BOAT_EDGE_OPERATOR_STAGED_PREDEADLINE_NO_NETWORK"
RIGHTS_STATUS = "OPERATOR_ATTESTED_LOCAL_RESEARCH_ONLY"
PROTECTED_START = date(2026, 10, 1)
HISTORY_START = date(2021, 10, 1)
KEY_RE = re.compile(r"^20\d{6}(?:0[1-9]|1\d|2[0-4])(?:0[1-9]|1[0-2])$")
SHA_RE = re.compile(r"^[a-f0-9]{64}$")
REG_RE = re.compile(r"^\d{4}$")

# Only documented pre-race raw fields. No site proprietary scores and no actual
# race entry, target finish, payout, odds, race outcome or betting instructions.
FIELD_SPECS = {
    "national_win_rate": ("全国勝率", 0.0, 10.0),
    "national_quinella_pct": ("全国2連対率", 0.0, 100.0),
    "national_trio_pct": ("全国3連対率", 0.0, 100.0),
    "local_win_rate": ("当地勝率", 0.0, 10.0),
    "local_quinella_pct": ("当地2連対率", 0.0, 100.0),
    "local_trio_pct": ("当地3連対率", 0.0, 100.0),
    "avg_st": ("全国平均ST", 0.0, 1.0),
    "motor_quinella_pct": ("モーター2連対率", 0.0, 100.0),
    "motor_trio_pct": ("モーター3連対率", 0.0, 100.0),
    "boat_quinella_pct": ("ボート2連対率", 0.0, 100.0),
    "boat_trio_pct": ("ボート3連対率", 0.0, 100.0),
    "f_count": ("F本数", 0, 30),
    "l_count": ("L本数", 0, 30),
}
DERIVED = {
    "national_win_rate_relative": "national_win_rate",
    "national_quinella_pct_relative": "national_quinella_pct",
    "avg_st_relative": "avg_st",
    "motor_quinella_pct_relative": "motor_quinella_pct",
    "motor_trio_pct_relative": "motor_trio_pct",
}


def _jst(value, label):
    if not isinstance(value, str):
        raise ValueError(f"{label}_REQUIRED")
    try:
        d = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label}_BAD_FORMAT") from exc
    if d.tzinfo is None or d.utcoffset() != timedelta(hours=9):
        raise ValueError(f"{label}_MUST_BE_JST")
    return d


def _valid_race_key(key):
    if not isinstance(key, str) or KEY_RE.fullmatch(key) is None:
        raise ValueError("INVALID_TARGET_RACE_KEY")
    try:
        day = date.fromisoformat(f"{key[:4]}-{key[4:6]}-{key[6:8]}")
    except ValueError as exc:
        raise ValueError("INVALID_TARGET_DATE") from exc
    if not HISTORY_START <= day < PROTECTED_START:
        raise ValueError("TARGET_OUTSIDE_PROTECTED_OFFLINE_HISTORY_WINDOW")
    return day


def _number(value, lower, upper, field):
    if value is None or value == "":
        return None
    text = str(value).strip()
    if not re.fullmatch(r"(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)", text):
        raise ValueError("BAD_FEATURE:" + field)
    num = float(text)
    if not math.isfinite(num) or not lower <= num <= upper:
        raise ValueError("OUT_OF_RANGE_FEATURE:" + field)
    if field in ("f_count", "l_count") and not num.is_integer():
        raise ValueError("NONINTEGER_COUNT:" + field)
    return int(num) if field in ("f_count", "l_count") else num


def _manifest(manifest, data):
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema", "source_kind", "source_sha256", "race_key", "deadline_jst",
        "first_seen_at_jst", "data_available_at_jst", "rights_status", "rights_evidence",
    }:
        raise ValueError("EXACT_OPERATOR_MANIFEST_REQUIRED")
    if manifest["schema"] != MANIFEST_SCHEMA or manifest["source_kind"] != SOURCE_KIND:
        raise ValueError("THIRD_PARTY_OR_UNREVIEWED_SOURCE_FORBIDDEN")
    if manifest["rights_status"] != RIGHTS_STATUS:
        raise ValueError("OFFLINE_RIGHTS_REVIEW_REQUIRED")
    evidence = manifest["rights_evidence"]
    if not isinstance(evidence, str) or len(evidence.strip()) < 12 or len(evidence) > 500:
        raise ValueError("SPECIFIC_RIGHTS_EVIDENCE_REQUIRED")
    sha = manifest["source_sha256"]
    if not isinstance(sha, str) or SHA_RE.fullmatch(sha) is None:
        raise ValueError("SOURCE_SHA256_REQUIRED")
    if hashlib.sha256(data).hexdigest() != sha:
        raise ValueError("SOURCE_BYTES_SHA_MISMATCH")
    day = _valid_race_key(manifest["race_key"])
    deadline = _jst(manifest["deadline_jst"], "DEADLINE")
    available = _jst(manifest["data_available_at_jst"], "AVAILABLE")
    first_seen = _jst(manifest["first_seen_at_jst"], "FIRST_SEEN")
    if (deadline.date() != day or available.date() > day or first_seen.date() > day
            or not available <= first_seen < deadline):
        raise ValueError("TIME_WINDOW_OR_PREDEADLINE_PROVENANCE_FAILED")
    return day


def ingest_offline_csv(raw: bytes, manifest: dict):
    """Validate one local six-lane predeadline normalized CSV. Return no predictions.

    Allows the CSV to contain other historical rows and previous-race form fields,
    but selects only the target *PRE-RACE* allowlisted columns. The operator's
    manifest is necessary but never independent proof of rights or timestamps.
    """
    if type(raw) is not bytes or not 1 <= len(raw) <= 10_000_000:
        raise ValueError("BOUNDED_CSV_BYTES_REQUIRED")
    day = _manifest(manifest, raw)
    try:
        source = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValueError("CSV_MUST_BE_UTF8") from exc
    if "\x00" in source:
        raise ValueError("BAD_CSV_CONTROL_CHARACTER")
    reader = csv.DictReader(io.StringIO(source, newline=""))
    fields = reader.fieldnames
    if not fields or len(fields) != len(set(fields)):
        raise ValueError("MISSING_OR_DUPLICATE_CSV_HEADERS")
    if "レースコード" not in fields:
        raise ValueError("RACE_KEY_COLUMN_REQUIRED")
    if any(any(word in f for word in ("払戻", "オッズ", "確定着順", "着順結果",
                                         "独自Elo", "イロレーティング", "機力指数",
                                         "AI2着", "逃がし2着", "サイト独自"))
           for f in fields):
        raise ValueError("TARGET_OUTCOME_OR_ODDS_COLUMNS_FORBIDDEN")
    selected = []
    if len(fields) > 1500:
        raise ValueError("EXCESSIVE_UNREVIEWED_COLUMNS")
    for i, row in enumerate(reader, 1):
        if i > 500:
            raise ValueError("TOO_MANY_SOURCE_RACES")
        if None in row:
            raise ValueError("CSV_ROW_WIDTH_MISMATCH")
        if row.get("レースコード") == manifest["race_key"]:
            selected.append(row)
    if len(selected) != 1:
        raise ValueError("TARGET_MUST_HAVE_EXACTLY_ONE_RACE_ROW")
    row = selected[0]
    if "レース日" in fields and row["レース日"] and row["レース日"] != day.isoformat():
        raise ValueError("ROW_RACE_DAY_MISMATCH")
    if "レース場コード" in fields and row["レース場コード"]:
        if row["レース場コード"].zfill(2) != manifest["race_key"][8:10]:
            raise ValueError("ROW_VENUE_ID_MISMATCH")
    if "レース回" in fields and row["レース回"]:
        if row["レース回"].lstrip("0").rstrip("Rr") != str(int(manifest["race_key"][10:12])):
            raise ValueError("ROW_RACE_NUMBER_MISMATCH")
    boats = {}
    ids = set()
    for boat in range(1, 7):
        prefix = f"艇{boat}_"
        id_value = row.get(prefix + "登録番号")
        if not isinstance(id_value, str) or REG_RE.fullmatch(id_value) is None or id_value in ids:
            raise ValueError("SIX_DISTINCT_RACER_REGISTRATIONS_REQUIRED")
        ids.add(id_value)
        measures = {}
        for name, (column, lower, upper) in FIELD_SPECS.items():
            measures[name] = _number(row.get(prefix + column), lower, upper, name)
        boats[str(boat)] = {
            "racer_id": id_value,
            "values": measures,
            "missing": sorted(name for name, value in measures.items() if value is None),
        }
    for output, basis in DERIVED.items():
        six = [boats[str(boat)]["values"][basis] for boat in range(1, 7)]
        avg = sum(six) / 6 if all(v is not None for v in six) else None
        for boat in range(1, 7):
            v = boats[str(boat)]["values"][basis]
            boats[str(boat)]["values"][output] = (
                round(v - avg, 8) if avg is not None else None)
            if avg is None:
                boats[str(boat)]["missing"].append(output)
    # No proprietary ELO, motor causal effect, ST quartiles, conditioned outcomes.
    return {
        "schema": SCHEMA,
        "research_only": True,
        "source_kind": SOURCE_KIND,
        "race_key": manifest["race_key"],
        "deadline_jst": manifest["deadline_jst"],
        "source_sha256": manifest["source_sha256"],
        "source_times_operator_attested_only": True,
        "source_rights_operator_attested_only": True,
        "independent_prospective_authentication": False,
        "source_site_derived_values_imported": False,
        "proprietary_elo_imported": False,
        "st_quartiles_imported": False,
        "conditional_top_two_imported": False,
        "model_training_performed": False,
        "model_promotion_authorized": False,
        "results_read": False,
        "formal_fresh_read": False,
        "prediction_written": False,
        "boats": boats,
        "coverage": {
            "racer_rows": 6,
            "raw_fields_possible": len(FIELD_SPECS) * 6,
            "raw_fields_present": sum(v is not None for b in boats.values()
                                      for k, v in b["values"].items() if k in FIELD_SPECS),
            "further_licensed_historical_features_needed": [
                "opponent_adjusted_elo", "motor_effect_adjusted_for_racer_and_course",
                "racer_st_q1_q2_q3", "conditional_second_third_distribution",
                "entry_transition_distribution", "other_boat_response_to_attack"],
        },
    }


def main():
    ap = argparse.ArgumentParser(description="Research-only offline predeadline input; no network, no scoring")
    ap.add_argument("--csv", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--report", type=Path, help="Optional local report path; never write into data/ or production")
    args = ap.parse_args()
    report = ingest_offline_csv(args.csv.read_bytes(), json.loads(args.manifest.read_text("utf-8")))
    rendered = json.dumps(report, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    if args.report is None:
        print(rendered, end="")
    else:
        if "data" in args.report.parts or "formal" in args.report.as_posix().lower():
            raise ValueError("DO_NOT_WRITE_PRODUCTION_OR_FORMAL_DATA")
        if args.report.exists():
            raise ValueError("RESEARCH_REPORT_OVERWRITE_FORBIDDEN")
        args.report.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
