#!/usr/bin/env python3
"""V407: offline adapter from a *locally parsed* K file into V401 staging.

No download, result endpoint, web request, Formal Fresh, model fitting or
production promotion. Uses optional third-party PerformanceParser ONLY with
operator-supplied, already authorized, decompressed local K text. Does not
authenticate publication timestamps, parser fidelity or source-data rights.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from boat_edge_v400_five_year_history_research import _jst_instant
from boat_edge_v401_staged_k_bridge import STAGING_SCHEMA, EXCLUSION_REASONS
from boat_edge_v404_asof_history_features import TARGET_SCHEMA, _target

MODEL = "BOAT_EDGE_V407_LOCAL_PERFORMANCE_TO_V401_RESEARCH_V1"
PUB_SCHEMA = "BOAT_EDGE_V407_OPERATOR_K_PUBLICATION_TIMES_V1"
B_SCHEMA = "BOAT_EDGE_V402_STAGED_B_PROGRAM_DAY_V1"
REASONS = frozenset(EXCLUSION_REASONS)


def stage_local_entries(entries, b_stage, publication):
    """Convert parsed RaceEntry-like objects using an *explicit* B roster.

    An absent/ambiguous race gets an explicit exclusion; a mismatch in known
    boat-to-racer mapping is an error, not an invented finish or actual course.
    No field from a target race may be used to generate prediction features.
    """
    if (not isinstance(b_stage, dict) or set(b_stage) !=
            {"schema", "source_day", "races"} or b_stage["schema"] != B_SCHEMA
            or not isinstance(b_stage["races"], list)
            or not 0 < len(b_stage["races"]) <= 288):
        raise ValueError("EXACT_LOCAL_B_STAGE_REQUIRED")
    if (not isinstance(publication, dict) or set(publication) !=
            {"schema", "source_day", "races"} or publication["schema"] != PUB_SCHEMA
            or not isinstance(publication["races"], dict)):
        raise ValueError("EXPLICIT_K_PUBLICATION_MAP_REQUIRED")
    try:
        day = date.fromisoformat(b_stage["source_day"])
    except (TypeError, ValueError) as exc:
        raise ValueError("INVALID_B_SOURCE_DAY") from exc
    if (day.isoformat() != b_stage["source_day"] or
            publication["source_day"] != day.isoformat()):
        raise ValueError("B_K_PUBLICATION_SOURCE_DAY_MISMATCH")
    targets = {}
    for race in b_stage["races"]:
        if not isinstance(race, dict):
            raise ValueError("INVALID_B_RACE")
        key, deadline, venue, racers = _target({
            **race, "schema": TARGET_SCHEMA
        })
        if key[:8] != day.strftime("%Y%m%d") or key in targets:
            raise ValueError("B_RACE_DAY_OR_DUPLICATE_MISMATCH")
        targets[key] = (deadline, racers)

    if not isinstance(entries, (list, tuple)):
        raise ValueError("LOCAL_K_PARSED_ENTRIES_REQUIRED")
    by_race = defaultdict(list)
    for entry in entries:
        try:
            event_day = entry.race_date
            venue_code = entry.venue_code
            race_no = entry.race_number
            boat = entry.boat_number
        except AttributeError as exc:
            raise ValueError("LOCAL_K_PARSER_ENTRY_FIELDS_MISSING") from exc
        if (not isinstance(event_day, date) or type(event_day) is not date
                or event_day != day or
                not isinstance(venue_code, str)
                or len(venue_code) != 2 or not venue_code.isascii()
                or not venue_code.isdigit() or
                type(race_no) is not int or
                not 1 <= int(venue_code) <= 24 or not 1 <= race_no <= 12 or
                type(boat) is not int or not 1 <= boat <= 6):
            raise ValueError("K_PARSER_INVALID_RACE_DATE_VENUE_OR_BOAT")
        key = f"{day:%Y%m%d}{int(venue_code):02d}{race_no:02d}"
        if key not in targets:
            raise ValueError("K_RACE_NOT_IN_OPERATOR_B_STAGE")
        by_race[key].append(entry)
        if len(by_race[key]) > 6:
            raise ValueError("K_DUPLICATE_OR_EXCESS_BOAT_ROWS")

    stages = []
    excluded = []
    included = set()
    for key in sorted(targets):
        deadline, b_racers = targets[key]
        observed = by_race[key]
        if len(observed) != 6:
            reason = "INCOMPLETE_RESULTS" if observed else "SOURCE_AMBIGUOUS"
            excluded.append({"race_key": key, "reason": reason})
            continue
        boats = [e.boat_number for e in observed]
        if set(boats) != set(range(1, 7)):
            raise ValueError("K_DUPLICATE_OR_MISSING_BOAT_ID")
        try:
            k_racers = {e.boat_number: str(e.racer_number) for e in observed}
            finishes = [e.result_position for e in observed]
            courses = [e.entrance_position for e in observed]
        except AttributeError as exc:
            raise ValueError("K_PARSER_MISSING_REQUIRED_FIELDS") from exc
        if k_racers != b_racers:
            raise ValueError("B_K_RACER_NUMBER_MISMATCH")
        if any(type(f) is not int or f not in range(1, 7) for f in finishes):
            excluded.append({"race_key": key, "reason": "NON_STANDARD_FINISH"})
            continue
        if set(finishes) != set(range(1, 7)):
            raise ValueError("K_FINISH_DUPLICATE_OR_INVALID_PERMUTATION")
        if any(type(c) is not int or c not in range(1, 7) for c in courses):
            excluded.append({"race_key": key, "reason": "UNVERIFIED_ACTUAL_COURSE"})
            continue
        if set(courses) != set(range(1, 7)):
            raise ValueError("K_ACTUAL_COURSE_DUPLICATE_OR_INVALID_PERMUTATION")
        if key not in publication["races"]:
            raise ValueError("K_PUBLICATION_PROVENANCE_MISSING:" + key)
        published = _jst_instant(publication["races"][key])
        if not (published.date() >= day and published > deadline):
            raise ValueError("K_PUBLICATION_NOT_AFTER_B_DEADLINE")
        stages.append({
            "race_key": key,
            "published_at": published.isoformat(),
            "entries": [
                {
                    "boat": e.boat_number,
                    "racer_id": str(e.racer_number),
                    "actual_course": e.entrance_position,
                    "finish": e.result_position,
                }
                for e in sorted(observed, key=lambda item: item.boat_number)
            ],
        })
        included.add(key)

    if set(publication["races"]) != included:
        raise ValueError("K_PUBLICATION_MAP_MUST_COVER_EXACT_INCLUDED_RACES")
    if not stages:
        raise ValueError("NO_COMPLETE_OPERATOR_STAGED_K_RACES")
    return {
        "schema": STAGING_SCHEMA,
        "source_day": day.isoformat(),
        "races": stages,
        "excluded": excluded,
    }


MAX_LOCAL_FILES = 48
MAX_FILE_BYTES = 16 * 1024 * 1024


def load_local_txt_sources(local_txt=None, local_dir=None):
    """Read only operator-selected pre-existing local TXT, never a URL/archive.

    Supports one file or a directory of decompressed per-venue files. Refuses
    symlinks and excessive file counts/sizes. No recursive tree traversal.
    """
    if (local_txt is None) == (local_dir is None):
        raise ValueError("EXACTLY_ONE_LOCAL_FILE_OR_DIRECTORY_REQUIRED")
    if local_txt is not None:
        paths = [Path(local_txt)]
    else:
        root = Path(local_dir)
        if root.is_symlink() or not root.is_dir():
            raise ValueError("LOCAL_TXT_DIRECTORY_REQUIRED")
        paths = sorted((p for p in root.iterdir() if p.suffix.lower() == ".txt"),
                       key=lambda p: p.name)
    if not 0 < len(paths) <= MAX_LOCAL_FILES:
        raise ValueError("LOCAL_TXT_FILE_COUNT_OUT_OF_RANGE")
    sources = {}
    for p in paths:
        if p.is_symlink() or not p.is_file() or p.suffix.lower() != ".txt":
            raise ValueError("LOCAL_TXT_FILE_UNSAFE_OR_MISSING")
        if p.stat().st_size > MAX_FILE_BYTES:
            raise ValueError("LOCAL_TXT_FILE_TOO_LARGE")
        raw = p.read_bytes()
        if not raw:
            raise ValueError("LOCAL_TXT_EMPTY_FILE")
        if p.name in sources:
            raise ValueError("DUPLICATE_LOCAL_TXT_FILENAME")
        sources[p.name] = raw
    return sources


def parse_local_k_files(sources):
    """Parse local decompressed CP932 K text files, without LzhDownloader."""
    if not isinstance(sources, dict) or not 0 < len(sources) <= MAX_LOCAL_FILES:
        raise ValueError("LOCAL_K_FILE_MAP_REQUIRED")
    decoded = {}
    for filename, raw in sources.items():
        if not isinstance(filename, str) or not filename.lower().endswith(".txt"):
            raise ValueError("LOCAL_K_TXT_NAME_REQUIRED")
        if not isinstance(raw, bytes) or not raw:
            raise ValueError("LOCAL_K_TEXT_BYTES_REQUIRED")
        try:
            decoded[filename] = raw.decode("cp932", errors="strict")
        except UnicodeError as exc:
            raise ValueError("LOCAL_K_CP932_DECODE_FAILED") from exc
    try:
        from boatrace_lzh.performance import PerformanceParser
    except ImportError as exc:
        raise RuntimeError("OPTIONAL_LOCAL_BOATRACE_LZH_PARSER_NOT_INSTALLED") from exc
    parsed = PerformanceParser().parse(decoded)
    return parsed.entries


def parse_local_txt(raw: bytes):
    """Compatibility function for one local K text, no downloader."""
    return parse_local_k_files({"operator_local_K.txt": raw})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    local = p.add_mutually_exclusive_group(required=True)
    local.add_argument("--local-k-txt", type=Path,
                       help="Preauthorized single K TXT, no URL/LZH download")
    local.add_argument("--local-k-dir", type=Path,
                       help="Directory of locally decompressed venue K TXT files")
    p.add_argument("--local-b-stage", type=Path, required=True,
                   help="Explicit operator-staged B roster for all expected day races")
    p.add_argument("--publication-map", type=Path, required=True,
                   help="Operator-provided per-race K publication evidence; never invented")
    p.add_argument("--output-json", type=Path, required=True,
                   help="Private local V401 staged JSON; never commit result rows")
    a = p.parse_args()
    staged = stage_local_entries(
        parse_local_k_files(load_local_txt_sources(a.local_k_txt, a.local_k_dir)),
        json.loads(a.local_b_stage.read_text(encoding="utf-8")),
        json.loads(a.publication_map.read_text(encoding="utf-8")),
    )
    if a.output_json.exists():
        raise ValueError("REFUSE_OVERWRITE_EXISTING_K_STAGE")
    a.output_json.write_text(
        json.dumps(staged, ensure_ascii=False, sort_keys=True,
                   separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "schema": MODEL, "source_day": staged["source_day"],
        "included": len(staged["races"]), "excluded": len(staged["excluded"]),
        "rights_independently_verified": False,
        "publication_timestamps_independently_verified": False,
        "raw_K_retrieved_by_this_tool": False, "formal_fresh_read": False,
        "accuracy_improvement_proven": False, "production_model_changed": False,
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
