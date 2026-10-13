#!/usr/bin/env python3
"""V408 local B (program) TXT -> strict V402 B-only day JSON, research-only.

Never downloads results, calls a live API, estimates historical capture times,
modifies Formal Fresh, or authorizes production/promotion. Operator already
holds independently authorized decompressed local B text. An optional
third-party ScheduleParser is only a parsing convenience, not verified proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from boat_edge_v400_five_year_history_research import (
    FIVE_YEAR_START, FIVE_YEAR_END_EXCLUSIVE, _jst_instant,
)
from boat_edge_v402_offline_b_k_reconciliation import B_SCHEMA
from boat_edge_v404_asof_history_features import TARGET_SCHEMA, _target
from boat_edge_v407_local_performance_bridge import load_local_txt_sources, MAX_LOCAL_FILES

MODEL = "BOAT_EDGE_V408_LOCAL_B_STAGE_RESEARCH_V1"
MAX_RACES = 288


def _identity(entry, day):
    """Strict date+venue+race; reject missing source fields, no inference."""
    try:
        actual_date, venue, race, boat, racer = (
            entry.race_date, entry.venue_code, entry.race_number,
            entry.boat_number, entry.racer_number,
        )
    except AttributeError as exc:
        raise ValueError("B_PARSER_MISSING_ENTRY_FIELD") from exc
    if (type(actual_date) is not date or actual_date != day
            or not isinstance(venue, str) or len(venue) != 2
            or not venue.isascii() or not venue.isdecimal()
            or type(race) is not int or not 1 <= race <= 12
            or not 1 <= int(venue) <= 24):
        raise ValueError("B_PARSER_INVALID_DATE_VENUE_RACE")
    if type(boat) is not int or not 1 <= boat <= 6:
        raise ValueError("B_PARSER_INVALID_BOAT")
    if type(racer) is not int or not 1000 <= racer <= 9999:
        raise ValueError("B_PARSER_INVALID_RACER")
    return f"{day:%Y%m%d}{venue}{race:02d}", boat, str(racer)


def _race_identity(race, day):
    try:
        d, venue, n = race.race_date, race.venue_code, race.race_number
    except AttributeError as exc:
        raise ValueError("B_PARSER_MISSING_RACE_ID") from exc
    if (type(d) is not date or d != day or type(n) is not int
            or not 1 <= n <= 12 or not isinstance(venue, str)
            or len(venue) != 2 or not venue.isascii()
            or not venue.isdecimal() or not 1 <= int(venue) <= 24):
        raise ValueError("B_PARSER_INVALID_RACE_ID")
    return f"{day:%Y%m%d}{venue}{n:02d}"


def stage_b_schedule(entries, closes, races, source_day):
    """Require exact 6-boat B rosters and one scheduled deadline per race.

    The schedule close_time is a SCHEDULED deadline, not evidence that a
    particular B capture was available before that deadline.
    """
    if type(source_day) is not date or not (FIVE_YEAR_START <= source_day < FIVE_YEAR_END_EXCLUSIVE):
        raise ValueError("PROTECTED_OR_OUTSIDE_HISTORICAL_B_DATE")
    if not all(isinstance(x, (list, tuple)) for x in (entries, closes, races)):
        raise ValueError("PARSER_ENTRY_CLOSE_AND_RACE_LISTS_REQUIRED")
    if not races or len(races) > MAX_RACES or not closes or len(closes) > MAX_RACES:
        raise ValueError("B_RACE_LIST_EMPTY_OR_OVER_LIMIT")
    declared = []
    for race in races:
        declared.append(_race_identity(race, source_day))
    if len(set(declared)) != len(declared):
        raise ValueError("DUPLICATE_B_PARSER_RACE")
    declared = set(declared)
    rosters = defaultdict(dict)
    for entry in entries:
        key, boat, racer = _identity(entry, source_day)
        if key not in declared:
            raise ValueError("B_ENTRY_WITHOUT_RACE")
        if boat in rosters[key]:
            raise ValueError("B_DUPLICATE_BOAT")
        rosters[key][boat] = racer
    deadlines = {}
    for item in closes:
        try:
            venue, number, close = item.venue_code, item.race_number, item.close_time
        except AttributeError as exc:
            raise ValueError("B_CLOSE_MISSING_FIELDS") from exc
        if (not isinstance(venue, str) or len(venue) != 2
                or not venue.isascii() or not venue.isdecimal()
                or not 1 <= int(venue) <= 24
                or type(number) is not int or not 1 <= number <= 12):
            raise ValueError("B_CLOSE_INVALID_RACE_ID")
        key = f"{source_day:%Y%m%d}{venue}{number:02d}"
        if key not in declared:
            raise ValueError("B_CLOSE_NOT_IN_RACE_SET")
        if key in deadlines:
            raise ValueError("DUPLICATE_B_CLOSE")
        if (not isinstance(close, datetime) or close.date() != source_day):
            raise ValueError("B_CLOSE_WRONG_OR_MISSING_DAY")
        stamp = _jst_instant(close.isoformat())
        if stamp.second or stamp.microsecond:
            raise ValueError("B_CLOSE_UNEXPECTED_SECOND_OR_FRACTION")
        deadlines[key] = stamp
    if set(rosters) != declared or set(deadlines) != declared:
        raise ValueError("B_PARSER_RACE_OR_CLOSE_COVERAGE_INCOMPLETE")
    result = []
    for key in sorted(declared):
        boat_racers = rosters[key]
        if set(boat_racers) != set(range(1, 7)) or len(set(boat_racers.values())) != 6:
            raise ValueError("B_REQUIRES_SIX_DISTINCT_BOATS_AND_RACERS")
        row = {
            "race_key": key, "deadline_jst": deadlines[key].isoformat(),
            "entries": [{"boat": boat, "racer_id": boat_racers[boat]}
                        for boat in range(1, 7)],
        }
        _target({"schema": TARGET_SCHEMA, **row})
        result.append(row)
    return {
        "schema": B_SCHEMA,
        "source_day": source_day.isoformat(),
        "races": result,
    }


def parse_local_b_files(sources, source_day):
    """Optional parser for one or more locally decompressed B venue TXT files."""
    if not isinstance(sources, dict) or not 0 < len(sources) <= MAX_LOCAL_FILES:
        raise ValueError("LOCAL_B_SOURCE_MAP_REQUIRED")
    if type(source_day) is not date:
        raise ValueError("OPERATOR_SOURCE_DAY_REQUIRED")
    decoded = {}
    for filename, raw in sources.items():
        if (not isinstance(filename, str) or not filename.lower().endswith(".txt")
                or not isinstance(raw, bytes) or not raw):
            raise ValueError("LOCAL_B_TEXT_BYTES_REQUIRED")
        try:
            decoded[filename] = raw.decode("cp932", errors="strict")
        except UnicodeError as exc:
            raise ValueError("LOCAL_B_CP932_DECODE_FAILED") from exc
    try:
        from boatrace_lzh.schedule import ScheduleParser
    except ImportError as exc:
        raise RuntimeError("OPTIONAL_LOCAL_B_SCHEDULE_PARSER_NOT_INSTALLED") from exc
    parser = ScheduleParser()
    structured = parser.parse(decoded)
    closes = parser.parse_schedule_with_close_times(decoded, source_day)
    return stage_b_schedule(structured.entries, closes, structured.races, source_day)


def parse_local_b_txt(raw, source_day):
    """Compatibility for single local B TXT; no archive extraction/network."""
    return parse_local_b_files({"operator_local_B.txt": raw}, source_day)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    local = p.add_mutually_exclusive_group(required=True)
    local.add_argument("--local-b-txt", type=Path,
                       help="Single licensed and decompressed local B TXT")
    local.add_argument("--local-b-dir", type=Path,
                       help="Directory of locally decompressed venue B TXT files")
    p.add_argument("--source-day", required=True, help="YYYY-MM-DD, historical only")
    p.add_argument("--output-json", type=Path, required=True,
                   help="Private staged B JSON for V402, never commit source bytes")
    a = p.parse_args()
    try:
        source_day = date.fromisoformat(a.source_day)
    except ValueError as exc:
        raise ValueError("INVALID_B_SOURCE_DAY") from exc
    sources = load_local_txt_sources(a.local_b_txt, a.local_b_dir)
    staged = parse_local_b_files(sources, source_day)
    lineage = {name: hashlib.sha256(data).hexdigest()
               for name, data in sorted(sources.items())}
    if a.output_json.exists():
        raise ValueError("REFUSE_OVERWRITE_EXISTING_B_STAGE")
    a.output_json.write_text(
        json.dumps(staged, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":")) + "\n", encoding="utf-8",
    )
    print(json.dumps({
        "schema": MODEL, "source_day": source_day.isoformat(),
        "b_source_sha256": next(iter(lineage.values())) if len(lineage) == 1 else None,
        "b_local_source_sha256_by_filename": lineage,
        "b_local_source_count": len(lineage),
        "b_parsed_races": len(staged["races"]),
        "b_source_historic_predeadline_capture_verified": False,
        "source_data_rights_independently_verified": False,
        "historical_outcomes_downloaded": False, "formal_fresh_read": False,
        "model_promotion_authorized": False, "accuracy_improvement_proven": False,
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
