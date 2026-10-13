#!/usr/bin/env python3
"""V400: strictly offline, research-only five-year historical count builder.

Accepts an operator-staged normalized CSV with documented source rights. It
never downloads race results or interacts with the site's Formal Fresh data.
No output in this module is a trained production model or hit-rate claim.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

MODEL = "BOAT_EDGE_V400_FIVE_YEAR_HISTORICAL_COUNTS_RESEARCH_V1"
JST = timezone(timedelta(hours=9))
PROTECTED_FROM = date(2026, 10, 1)  # Never import protected Formal Fresh dates.
FIVE_YEAR_START = date(2021, 10, 1)
FIVE_YEAR_END_EXCLUSIVE = date(2026, 10, 1)
COLUMNS = ("race_key", "boat", "racer_id", "actual_course", "finish", "published_at")
WINDOWS = (90, 365, 1095, 1826)
HALF_LIFE_DAYS = 180
SHA_PATTERN = re.compile(r"[a-f0-9]{64}\Z")
RACE_PATTERN = re.compile(r"[0-9]{12}\Z")


def _jst_instant(value):
    if not isinstance(value, str):
        raise ValueError("JST_TIMESTAMP_REQUIRED")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("INVALID_TIMESTAMP") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(hours=9):
        raise ValueError("EXPLICIT_JST_OFFSET_REQUIRED")
    return parsed


def _str_digest(data):
    return hashlib.sha256(data).hexdigest()


def validate_manifest(manifest, raw, as_of):
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema", "csv_sha256", "source_name", "source_locator",
        "rights_evidence", "rights_review_status", "normalization_protocol",
    }:
        raise ValueError("EXACT_SOURCE_MANIFEST_REQUIRED")
    if manifest["schema"] != "BOAT_EDGE_V400_STAGED_HISTORY_MANIFEST_V1":
        raise ValueError("SOURCE_MANIFEST_SCHEMA_MISMATCH")
    if (not isinstance(manifest["csv_sha256"], str)
            or SHA_PATTERN.fullmatch(manifest["csv_sha256"]) is None
            or manifest["csv_sha256"] != _str_digest(raw)):
        raise ValueError("RAW_HISTORY_SHA256_MISMATCH")
    if manifest["rights_review_status"] != "OPERATOR_REVIEWED_OFFLINE_RESEARCH_ONLY":
        raise ValueError("SOURCE_RIGHTS_REVIEW_NOT_ATTESTED")
    for key in ("source_name", "source_locator", "rights_evidence", "normalization_protocol"):
        if not isinstance(manifest[key], str) or not manifest[key].strip():
            raise ValueError("SOURCE_PROVENANCE_FIELD_MISSING:" + key)
    if (not isinstance(as_of, datetime) or as_of.tzinfo is None
            or as_of.utcoffset() != timedelta(hours=9)
            or not (FIVE_YEAR_START < as_of.date() <= PROTECTED_FROM)
            or as_of > datetime.combine(PROTECTED_FROM, datetime.min.time(), JST)):
        raise ValueError("AS_OF_OUTSIDE_PROTECTED_HISTORICAL_WINDOW")
    return _str_digest(json.dumps(manifest, sort_keys=True, ensure_ascii=False,
                                 separators=(",", ":")).encode("utf-8"))


def parse_row(row, as_of):
    if not isinstance(row, dict) or set(row) != set(COLUMNS):
        raise ValueError("EXACT_NORMALIZED_COLUMNS_REQUIRED")
    race_key = row["race_key"]
    if not isinstance(race_key, str) or not RACE_PATTERN.fullmatch(race_key):
        raise ValueError("INVALID_RACE_KEY")
    try:
        race_date = date.fromisoformat(f"{race_key[:4]}-{race_key[4:6]}-{race_key[6:8]}")
        venue = int(race_key[8:10]); number = int(race_key[10:])
        boat = int(row["boat"]); course = int(row["actual_course"])
        finish = int(row["finish"])
    except (TypeError, ValueError) as exc:
        raise ValueError("INVALID_RACE_FIELDS") from exc
    if not (FIVE_YEAR_START <= race_date < FIVE_YEAR_END_EXCLUSIVE
            and 1 <= venue <= 24 and 1 <= number <= 12
            and 1 <= boat <= 6 and 1 <= course <= 6 and 1 <= finish <= 6):
        raise ValueError("RACE_OUTSIDE_ALLOWED_RANGE_OR_INVALID_PERMUTATION")
    racer = row["racer_id"]
    if not isinstance(racer, str) or not re.fullmatch(r"[0-9]{4}", racer):
        raise ValueError("INVALID_RACER_ID")
    published = _jst_instant(row["published_at"])
    if not (datetime.combine(race_date, datetime.min.time(), JST) <= published < as_of
            and race_date < as_of.date()):
        raise ValueError("HISTORICAL_PUBLISHED_AT_LEAK_OR_TARGET_RACE")
    return (race_key, race_date, venue, boat, racer, course, finish, published)


def iter_races(text, as_of):
    import io
    source = csv.DictReader(io.StringIO(text, newline=""))
    if source.fieldnames is None or tuple(source.fieldnames) != COLUMNS:
        raise ValueError("EXACT_NORMALIZED_CSV_HEADER_REQUIRED")
    current = None
    rows = []
    previous = None
    for number, raw in enumerate(source, 2):
        item = parse_row(raw, as_of)
        key = item[0]
        if previous is not None and (key, item[3]) <= previous:
            raise ValueError("HISTORY_NOT_SORTED_OR_DUPLICATE")
        previous = (key, item[3])
        if current is not None and key != current:
            yield _complete_race(rows)
            rows = []
        current = key
        rows.append(item)
    if rows:
        yield _complete_race(rows)


def _complete_race(rows):
    if len(rows) != 6 or {r[3] for r in rows} != set(range(1, 7)):
        raise ValueError("INCOMPLETE_SIX_BOAT_RACE")
    if {r[5] for r in rows} != set(range(1, 7)):
        raise ValueError("ACTUAL_COURSE_NOT_SIX_WAY_PERMUTATION")
    if {r[6] for r in rows} != set(range(1, 7)):
        raise ValueError("FINISH_NOT_SIX_UNIQUE_POSITIONS")
    if len({r[4] for r in rows}) != 6 or len({r[7] for r in rows}) != 1:
        raise ValueError("DUPLICATE_RACER_OR_MIXED_PUBLISHED_AT")
    return rows


def build_counts(raw, manifest, as_of):
    """Return strict descriptive counts, not a predictor or a calibrated probability.

    Year-5 scope is fixed to unprotected 2021-10-01..2026-09-30; within
    each window counts are disjoint-by-race (nested windows are not additive).
    A 180-day half-life supplies a separate recency measure, never an imputed
    unobserved result. No target's actual entry is read by this model.
    """
    if not isinstance(raw, bytes):
        raise ValueError("CSV_BYTES_REQUIRED")
    manifest_digest = validate_manifest(manifest, raw, as_of)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("UTF8_STAGED_CSV_REQUIRED") from exc
    table = defaultdict(lambda: {str(w): [0, 0, 0, 0] for w in WINDOWS})
    weighted = defaultdict(lambda: [0., 0., 0., 0.])
    races = 0
    min_race = None; max_race = None
    for rows in iter_races(text, as_of):
        event_date = rows[0][1]
        age = (as_of.date() - event_date).days
        if age < 1 or age > WINDOWS[-1]:
            raise ValueError("HISTORY_RACE_NOT_IN_TRAILING_FIVE_YEARS")
        races += 1
        min_race = min(min_race, event_date) if min_race else event_date
        max_race = max(max_race, event_date) if max_race else event_date
        weight = math.exp2(-age / HALF_LIFE_DAYS)
        for row in rows:
            _, _, venue, _, racer, course, finish, _ = row
            for group in (f"venue:{venue:02d}/course:{course}",
                          f"racer:{racer}/course:{course}",
                          f"all/course:{course}"):
                for window in WINDOWS:
                    if age <= window:
                        slot = table[group][str(window)]
                        slot[0] += 1
                        if finish <= 3:
                            slot[finish] += 1
                summary = weighted[group]
                summary[0] += weight
                if finish <= 3:
                    summary[finish] += weight
    if not races:
        raise ValueError("HISTORICAL_DATASET_EMPTY")
    metrics = {
        group: {
            "windows_days": {window: {"sample_count": vals[0],
                                      "first": vals[1], "second": vals[2], "third": vals[3]}
                             for window, vals in sorted(entries.items(), key=lambda e: int(e[0]))},
            "half_life_180d_weighted": {key: round(val, 12) for key, val in zip(
                ("effective_entries", "first", "second", "third"), weighted[group])},
        }
        for group, entries in sorted(table.items())
    }
    return {
        "schema": MODEL, "research_only": True, "production_eligible": False,
        "formal_fresh_used": False, "results_downloaded_by_this_script": False,
        "rights_independently_verified_by_script": False,
        "publisher_timestamps_independently_verified": False,
        "calibrated": False, "accuracy_improvement_proven": False,
        "model_promotion_authorized": False, "wagers_authorized": False,
        "as_of_exclusive_jst": as_of.isoformat(), "protected_from": PROTECTED_FROM.isoformat(),
        "history_start": min_race.isoformat(), "history_end": max_race.isoformat(),
        "race_count": races, "six_boat_rows": races * 6,
        "csv_sha256": _str_digest(raw), "manifest_sha256": manifest_digest,
        "windows_days": list(WINDOWS), "half_life_days": HALF_LIFE_DAYS,
        "count_tables": metrics,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged-csv", type=Path, required=True,
                        help="Operator-normalized local licensed input; never downloaded")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--as-of-jst", required=True, help="Exclusive train cutoff, JST ISO8601")
    args = parser.parse_args()
    result = build_counts(args.staged_csv.read_bytes(),
                          json.loads(args.manifest.read_text(encoding="utf-8")),
                          _jst_instant(args.as_of_jst))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
