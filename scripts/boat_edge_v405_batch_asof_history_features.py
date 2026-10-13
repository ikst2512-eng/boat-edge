#!/usr/bin/env python3
"""V405: batched, timestamp-censored V404 history features (research-only).

Offline, operator-staged, rights-attested input only. No network, results API,
formal cohorts, model promotion or betting. Publication time is NOT independently
authenticated by this module. Preserves V404's calendar-day rolling windows,
including the cutoff calendar day (0 <= age < window), not sliding 24-hour intervals.
"""
from __future__ import annotations

import argparse
import hashlib
import heapq
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from boat_edge_v400_five_year_history_research import (
    FIVE_YEAR_END_EXCLUSIVE, JST, WINDOWS, iter_races, validate_manifest,
)
from boat_edge_v404_asof_history_features import MODEL as V404_MODEL, _target

MODEL = "BOAT_EDGE_V405_BATCH_ASOF_INDEX_RESEARCH_V1"
K = ("entries", "first", "second", "third")
MAX_TARGETS = 20000


def _event_groups(entry):
    _, _, venue, _, racer, course, _, _ = entry
    return (("all", "all", course),
            ("venue", venue, course),
            ("racer", racer, course))


def build_batch(raw: bytes, manifest: dict, targets: list[dict]):
    if not isinstance(raw, bytes):
        raise ValueError("HISTORY_CSV_BYTES_REQUIRED")
    if not isinstance(manifest, dict):
        raise ValueError("HISTORY_SOURCE_MANIFEST_REQUIRED")
    cutoff = datetime.combine(FIVE_YEAR_END_EXCLUSIVE, datetime.min.time(), JST)
    validate_manifest(manifest, raw, cutoff)
    if not isinstance(targets, list) or len(targets) > MAX_TARGETS:
        raise ValueError("TARGET_LIST_REQUIRED_OR_TOO_LARGE")
    parsed_targets = [_target(t) for t in targets]
    # Guard a retrospective paradox: a K result cannot be published before its
    # own race date. V404 already rejects it during iter_races validation, but
    # V405 must not turn a forged timestamp into a past feature during sweep.
    if len({key for key, _, _, _ in parsed_targets}) != len(parsed_targets):
        raise ValueError("DUPLICATE_B_ONLY_TARGET_RACE_KEY")
    try:
        src = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValueError("HISTORY_UTF8_REQUIRED") from exc
    events = [tuple(rows) for rows in iter_races(src, cutoff)]
    for rows in events:
        if rows[0][7].date() < rows[0][1]:
            raise ValueError("HISTORICAL_PUBLISHED_AT_LEAK")
    events.sort(key=lambda rows: (rows[0][7], rows[0][0]))
    event_ids = {rows[0][0]: i for i, rows in enumerate(events)}
    if len(event_ids) != len(events):
        raise ValueError("DUPLICATE_HISTORY_RACE_KEY")
    order = sorted(range(len(parsed_targets)),
                   key=lambda i: (parsed_targets[i][1], parsed_targets[i][0]))
    active = {w: set() for w in WINDOWS}
    expiry = {w: [] for w in WINDOWS}  # heap of (race-date ordinal, event id)
    day_totals = Counter()  # only largest window needs date extrema
    counters = defaultdict(lambda: [0, 0, 0, 0])
    pointer = 0
    source_sha = hashlib.sha256(raw).hexdigest()
    outputs = [None] * len(targets)

    def modify(w, idx, delta):
        rows = events[idx]
        day = rows[0][1].toordinal()
        if delta > 0:
            active[w].add(idx)
            if w == max(WINDOWS):
                day_totals[day] += 1
        else:
            active[w].remove(idx)
            if w == max(WINDOWS):
                day_totals[day] -= 1
                if not day_totals[day]:
                    del day_totals[day]
        for entry in rows:
            finish = entry[6]
            for group in _event_groups(entry):
                item = counters[(w,) + group]
                item[0] += delta
                if finish <= 3:
                    item[finish] += delta
                if min(item) < 0:
                    raise AssertionError("NEGATIVE_AGGREGATE_COUNT")

    def stats(group):
        return {str(course): {
            str(w): dict(zip(K, counters.get(
                (w, group[0], group[1], course), (0, 0, 0, 0))))
            for w in WINDOWS
        } for course in range(1, 7)}

    for position in order:
        key, deadline, venue, racers = parsed_targets[position]
        target_day = deadline.date().toordinal()

        # Only events genuinely declared available before this exact deadline
        # enter the sweep. Independent authentication is NOT asserted.
        while pointer < len(events) and events[pointer][0][7] < deadline:
            idx = pointer
            rows = events[idx]
            race_day = rows[0][1].toordinal()
            age = target_day - race_day
            if age < 0:
                raise ValueError("FUTURE_RACE_PUBLISHED_BEFORE_TARGET")
            for w in WINDOWS:
                if age < w:
                    modify(w, idx, +1)
                    heapq.heappush(expiry[w], (race_day, idx))
            pointer += 1

        for w in WINDOWS:
            lower = target_day - w
            while expiry[w] and expiry[w][0][0] <= lower:
                _, idx = heapq.heappop(expiry[w])
                # Each event is in the heap only once per window.
                if idx in active[w]:
                    modify(w, idx, -1)

        own_idx = event_ids.get(key)
        owns = []  # temporarily eliminate the target even if it has a forged early pub timestamp
        if own_idx is not None:
            for w in WINDOWS:
                if own_idx in active[w]:
                    modify(w, own_idx, -1)
                    owns.append(w)
        try:
            day_index = day_totals
            eligible = len(active[max(WINDOWS)])
            late = len(events) - pointer
            if own_idx is not None and own_idx >= pointer:
                late -= 1
            result = {
                "schema": V404_MODEL, "research_only": True,
                "target": {
                    "race_key": key, "deadline_jst": deadline.isoformat(),
                    "venue": f"{venue:02d}", "boat_racer_ids":
                    {str(b): racers[b] for b in sorted(racers)},
                },
                "source_sha256": source_sha,
                "historic_publication_timestamps_independently_verified": False,
                "historic_source_rights_independently_verified": False,
                "target_b_roster_historic_predeadline_capture_verified": False,
                "results_downloaded": False, "formal_fresh_read": False,
                "retrospective_features_only": True,
                "historical_races_eligible_before_target": eligible,
                "historical_races_not_yet_available": late,
                "same_target_outcome_excluded": int(own_idx is not None),
                "history_min_date": (
                    datetime.fromordinal(min(day_index)).date().isoformat()
                    if day_index else None),
                "history_max_date": (
                    datetime.fromordinal(max(day_index)).date().isoformat()
                    if day_index else None),
                "rolling_windows_days": list(WINDOWS),
                "national_actual_course_counts": stats(("all", "all")),
                "venue_actual_course_counts": stats(("venue", venue)),
                "racer_actual_course_counts_by_boat": {
                    str(b): {
                        "racer_id": racers[b],
                        "course_counts": stats(("racer", racers[b])),
                    } for b in sorted(racers)
                },
                "actual_course_of_target_not_observed_or_inferred": True,
                "calibrated": False, "accuracy_improvement_proven": False,
                "production_model_changed": False,
                "model_promotion_authorized": False, "wagers_authorized": False,
            }
            outputs[position] = result
        finally:
            for w in owns:
                modify(w, own_idx, +1)

    return {
        "schema": MODEL, "research_only": True,
        "input_history_sha256": source_sha,
        "target_count": len(targets),
        "history_race_count": len(events),
        "asof_method": "published_at_strictly_before_B_only_deadline",
        "target_output_schema": V404_MODEL,
        "V404_parity_target": True,  # fixture-only contract; not verified on actual K/B
        "timestamps_and_rights_independently_verified": False,
        "formal_fresh_read": False, "trained_model_created": False,
        "accuracy_improvement_proven": False,
        "production_model_changed": False, "model_promotion_authorized": False,
        "wagers_authorized": False, "snapshots": outputs,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--history-csv", type=Path, required=True)
    p.add_argument("--history-manifest", type=Path, required=True)
    p.add_argument("--b-only-targets-json", type=Path, required=True,
                   help="Array of B-only targets, NEVER result or actual-course rows")
    args = p.parse_args()
    result = build_batch(
        args.history_csv.read_bytes(),
        json.loads(args.history_manifest.read_text(encoding="utf-8")),
        json.loads(args.b_only_targets_json.read_text(encoding="utf-8")),
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
