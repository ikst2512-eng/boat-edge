#!/usr/bin/env python3
"""V410 S-priority opponent-relative Elo and other-boat course outcomes.

Research-only. Reads only operator-staged V400 normalized K CSV and the V404
B-only target schema; no HTTP, Formal Fresh, predictions, wagers, odds or output
labels for the target. History rights and timestamps are operator-attested and
NOT independently authenticated. Elo is opponent-relative, NOT course-causal
or calibrated. No model or source collection changes.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path

from boat_edge_v400_five_year_history_research import (
    JST, FIVE_YEAR_END_EXCLUSIVE, FIVE_YEAR_START, iter_races,
    validate_manifest,
)
from boat_edge_v404_asof_history_features import _target

MODEL = "BOAT_EDGE_V410_S_PRIOR_ELO_OTHER_BOAT_RESEARCH_V1"
ELO_PRIOR = 1500.0
K_PER_RACE = 24.0
MIN_CONDITIONAL_RACES = 20


def snapshot(raw: bytes, manifest: dict, target: dict):
    """Build an as-of descriptive snapshot for exactly one B-only target race.

    Uses actual courses and finishes exclusively for historic completed races
    recorded published before the target deadline. No actual target course,
    start time or finish is accepted in the B-only target.
    """
    target_key, deadline, venue, target_racers = _target(target)
    if type(raw) is not bytes:
        raise ValueError("V410_HISTORY_BYTES_REQUIRED")
    if not isinstance(manifest, dict):
        raise ValueError("V410_HISTORY_MANIFEST_REQUIRED")
    cutoff = datetime.combine(FIVE_YEAR_END_EXCLUSIVE, datetime.min.time(), JST)
    validate_manifest(manifest, raw, cutoff)
    try:
        data = raw.decode("utf-8-sig")
    except UnicodeError as exc:
        raise ValueError("V410_HISTORY_UTF8_REQUIRED") from exc

    # V400 enforces 6 distinct racers, six distinct finishes/courses and
    # consistent publication stamps within each race; target data is B-only.
    events = list(iter_races(data, cutoff))
    events.sort(key=lambda rows: (rows[0][7], rows[0][0]))
    ratings = {}
    starts = defaultdict(int)
    # (racer_id, own actual course, other actual course):
    # [prior eligible appearances, other boats finished 1st, 2nd, 3rd].
    others = defaultdict(lambda: [0, 0, 0, 0])
    used = 0
    excluded_target = 0
    excluded_late = 0
    excluded_outside = 0

    for rows in events:
        event_key, event_day, _, _, _, _, _, published = rows[0]
        if event_key == target_key:
            # Even a forged early publication timestamp must not leak its
            # own target outcome into the snapshot.
            excluded_target += 1
            continue
        if published >= deadline:
            excluded_late += 1
            continue
        day_age = (deadline.date() - event_day).days
        if not 0 <= day_age < 1826:
            excluded_outside += 1
            continue
        if published.date() < event_day:
            raise ValueError("V410_HISTORICAL_PUBLISHED_AT_LEAK")
        used += 1
        before = {r[4]: ratings.get(r[4], ELO_PRIOR) for r in rows}
        delta = {}
        for a in rows:
            ra, finish = a[4], a[6]
            score_delta = 0.0
            for b in rows:
                if a is b:
                    continue
                rb = b[4]
                expected = 1.0 / (1.0 + 10.0 ** ((before[rb] - before[ra]) / 400.0))
                actual = 1.0 if finish < b[6] else 0.0
                score_delta += actual - expected
            delta[ra] = K_PER_RACE * score_delta / 5.0
        # Same-race simultaneous updates; never allow an earlier finisher to
        # influence another's expectation inside the SAME race.
        for a in rows:
            racer = a[4]
            ratings[racer] = before[racer] + delta[racer]
            starts[racer] += 1
            for b in rows:
                if a is b:
                    continue
                index = (racer, a[5], b[5])
                cell = others[index]
                cell[0] += 1
                if 1 <= b[6] <= 3:
                    cell[b[6]] += 1

    out = {}
    for boat, racer in sorted(target_racers.items()):
        runs = starts[racer]
        courses = {}
        for own_course in range(1, 7):
            other_courses = {}
            for other_course in range(1, 7):
                if own_course == other_course:
                    continue
                n, first, second, third = others[(racer, own_course, other_course)]
                other_courses[str(other_course)] = {
                    "observed_races": n, "other_first": first,
                    "other_second": second, "other_third": third,
                    "sufficient_20_races_for_descriptive_rate": n >= MIN_CONDITIONAL_RACES,
                    "other_second_rate": round(second / n, 8)
                    if n >= MIN_CONDITIONAL_RACES else None,
                    "other_third_rate": round(third / n, 8)
                    if n >= MIN_CONDITIONAL_RACES else None,
                }
            courses[str(own_course)] = other_courses
        out[str(boat)] = {
            "racer_id": racer, "historic_races": runs,
            # Elo has a mathematical 1500 prior internally; when a racer has
            # zero observations, do not report the prior as measured strength.
            "opponent_relative_elo": round(ratings[racer], 8) if runs else None,
            "elo_unobserved_prior_only": runs == 0,
            "other_boat_course_outcomes": courses,
        }
    known = [out[str(i)]["opponent_relative_elo"] for i in range(1, 7)]
    center = sum(known) / 6 if all(x is not None for x in known) else None
    for i in range(1, 7):
        rating = out[str(i)]["opponent_relative_elo"]
        out[str(i)]["elo_vs_six_boat_mean"] = (
            round(rating - center, 8) if center is not None else None
        )

    return {
        "schema": MODEL, "research_only": True,
        "production_eligible": False, "prediction_probabilities_calibrated": False,
        "course_adjusted_elo": False, "causal_other_boat_effect_proven": False,
        "source_rights_independently_verified": False,
        "publication_times_independently_authenticated": False,
        "target_race_actual_entry_used": False, "target_race_result_used": False,
        "formal_fresh_read": False, "results_downloaded": False,
        "model_training_or_promotion_authorized": False,
        "accuracy_improvement_proven": False,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "target": {"race_key": target_key, "deadline_jst": deadline.isoformat(),
                   "venue": f"{venue:02d}"},
        "eligible_historical_races": used,
        "same_target_races_excluded": excluded_target,
        "not_yet_published_races_excluded": excluded_late,
        "outside_1826_calendar_days_excluded": excluded_outside,
        "elo_configuration": {"prior": ELO_PRIOR, "k_per_race": K_PER_RACE,
                               "opponent_comparisons": 5,
                               "unadjusted_for_course": True},
        "six_boats": out,
    }


def main():
    p = argparse.ArgumentParser(description="V410 operator-staged history S-feature research only")
    p.add_argument("--history-csv", type=Path, required=True)
    p.add_argument("--history-manifest", type=Path, required=True)
    p.add_argument("--b-only-target-json", type=Path, required=True)
    args = p.parse_args()
    output = snapshot(args.history_csv.read_bytes(),
                      json.loads(args.history_manifest.read_text(encoding="utf-8")),
                      json.loads(args.b_only_target_json.read_text(encoding="utf-8")))
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
