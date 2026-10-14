#!/usr/bin/env python3
"""Offline BoatraceCSV 7-source as-of JOIN audit; research only.

No downloads, no results ingestion, no model training or promotion.
Never accesses Formal Fresh results. Accepts only historical program/preview
CSV bytes already locally staged by an operator with independently checked rights.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

SOURCES = ("race_cards", "title", "stt", "tkz", "sui", "original_exhibition")
PREVIEWS = ("stt", "tkz", "sui", "original_exhibition")
JST = timezone(timedelta(hours=9))
FIRST = date(2021, 10, 1)
LAST = date(2026, 9, 30)
SCHEMA = "BOAT_EDGE_V409_BOATRACECSV_OFFLINE_ASOF_AUDIT_V1"
KEY_RE = re.compile(r"^\d{8}(0[1-9]|1\d|2[0-4])(0[1-9]|1[0-2])$")


def parse_jst(raw):
    if not raw:
        raise ValueError("MISSING_PREVIEW_CAPTURE_TIME")
    try:
        instant = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError("INVALID_PREVIEW_CAPTURE_TIME") from exc
    if instant.tzinfo is None or instant.utcoffset() != timedelta(hours=9):
        raise ValueError("PREVIEW_CAPTURE_NOT_EXPLICIT_JST")
    return instant


def read_source(raw, source, day):
    if source not in SOURCES:
        raise ValueError("UNKNOWN_CSV_SOURCE")
    if not isinstance(raw, bytes) or not raw:
        raise ValueError("EMPTY_CSV_SOURCE")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig", errors="strict")))
        names = reader.fieldnames
        if not names or len(names) != len(set(names)) or "レースコード" not in names:
            raise ValueError("CSV_MISSING_OR_DUPLICATE_HEADER")
        if source in PREVIEWS:
            required = ("レース日", "レース場", "レース回", "締切時刻", "取得日時")
            if not all(n in names for n in required):
                raise ValueError("PREVIEW_MISSING_TIME_OR_ID_COLUMN")
        else:
            if "レース日" not in names:
                raise ValueError("PROGRAM_MISSING_DAY_COLUMN")
        rows = {}
        for row in reader:
            if None in row:
                raise ValueError("CSV_EXTRA_COLUMNS")
            key = row["レースコード"]
            if not key or not KEY_RE.fullmatch(key) or key[:8] != day.strftime("%Y%m%d"):
                raise ValueError("INVALID_OR_WRONG_DAY_RACE_KEY")
            if row["レース日"] != day.isoformat():
                raise ValueError("RACE_DAY_MISMATCH")
            if source in PREVIEWS:
                if row["レース場"] != key[8:10] or row["レース回"] != key[10:12] + "R":
                    raise ValueError("PREVIEW_VENUE_OR_RACE_MISMATCH")
            if key in rows:
                raise ValueError("DUPLICATE_SOURCE_RACE_KEY")
            rows[key] = row
    except UnicodeDecodeError as exc:
        raise ValueError("SOURCE_NOT_UTF8") from exc
    return rows


def audit(day, files):
    if type(day) is not date or not FIRST <= day <= LAST:
        raise ValueError("FORMAL_FRESH_OR_OUTSIDE_HISTORICAL_DAY")
    if not isinstance(files, dict) or "race_cards" not in files:
        raise ValueError("LOCAL_RACE_CARDS_REQUIRED")
    if any(s not in SOURCES for s in files):
        raise ValueError("RESULTS_OR_UNKNOWN_SOURCE_FORBIDDEN")
    source_rows = {s: read_source(raw, s, day) for s, raw in files.items()}
    baseline = source_rows["race_cards"]
    counters = {s: Counter() for s in PREVIEWS}
    counts = Counter()
    # No outcome fields are read, returned, or persisted.
    eligible_by_source = {name: set() for name in PREVIEWS}
    deadlines_by_source = {name: {} for name in PREVIEWS}
    for key in sorted(baseline):
        counts["race_cards"] += 1
        for source in ("title",):
            if source in source_rows:
                counts[source + "_matched"] += int(key in source_rows[source])
        for source in PREVIEWS:
            if source not in source_rows:
                counters[source]["source_not_supplied"] += 1
                continue
            row = source_rows[source].get(key)
            if row is None:
                counters[source]["race_missing"] += 1
                continue
            try:
                capture = parse_jst(row["取得日時"])
                deadline = datetime.combine(day, time.fromisoformat(row["締切時刻"]), JST)
            except ValueError:
                counters[source]["invalid_timestamp"] += 1
                continue
            deadlines_by_source[source][key] = deadline
            if capture.date() != day:
                counters[source]["capture_wrong_day"] += 1
            elif not capture < deadline:
                counters[source]["not_before_deadline"] += 1
            else:
                counters[source]["timestamp_eligible_unverified"] += 1
                eligible_by_source[source].add(key)
    for source, rows in source_rows.items():
        counts[source + "_rows"] = len(rows)
        counts[source + "_outside_race_cards"] = len(set(rows) - set(baseline))
    eligible_all_four = set.intersection(*(eligible_by_source[name] for name in PREVIEWS))
    complete_deadlines = set.intersection(*(set(deadlines_by_source[name]) for name in PREVIEWS))
    deadline_conflicts = {
        key for key in complete_deadlines
        if len({deadlines_by_source[name][key] for name in PREVIEWS}) != 1
    }
    counts["all_four_preview_deadline_conflicts"] = len(deadline_conflicts)
    counts["all_four_preview_timestamps_eligible_unverified"] = len(
        eligible_all_four - deadline_conflicts
    )
    # Never label timestamps as independently verified as-of proof.
    return {
        "schema": SCHEMA,
        "source_day": day.isoformat(),
        "race_card_rows": len(baseline),
        "counts": dict(sorted(counts.items())),
        "preview_status": {s: dict(sorted(counters[s].items())) for s in PREVIEWS},
        "source_data_rights_verified": False,
        "capture_git_first_commit_verified": False,
        "prediction_predeadline_freeze_verified": False,
        "result_or_payout_accessed": False,
        "formal_fresh_accessed": False,
        "top3_top5_top10_accuracy_measured": False,
        "model_promotion_authorized": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--day", required=True, help="YYYY-MM-DD, no 2026-10-01 or later")
    p.add_argument("--race-cards", type=Path, required=True)
    p.add_argument("--title", type=Path)
    p.add_argument("--stt", type=Path)
    p.add_argument("--tkz", type=Path)
    p.add_argument("--sui", type=Path)
    p.add_argument("--original-exhibition", type=Path)
    p.add_argument("--audit-json", type=Path, required=True)
    a = p.parse_args()
    day = date.fromisoformat(a.day)
    if not FIRST <= day <= LAST:
        raise ValueError("FORMAL_FRESH_OR_OUTSIDE_HISTORICAL_DAY")
    paths = {"race_cards": a.race_cards, "title": a.title, "stt": a.stt,
             "tkz": a.tkz, "sui": a.sui,
             "original_exhibition": a.original_exhibition}
    files = {}
    for source, path in paths.items():
        if path is not None:
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 32*1024*1024:
                raise ValueError("LOCAL_CSV_FILE_UNSAFE")
            files[source] = path.read_bytes()
    result = audit(day, files)
    if a.audit_json.exists():
        raise ValueError("REFUSE_OVERWRITE_AUDIT")
    a.audit_json.write_text(json.dumps(result, ensure_ascii=False, indent=2,
                                       sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
