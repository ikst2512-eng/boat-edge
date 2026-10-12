#!/usr/bin/env python3
"""V345 research-only 120 ranked BOAT tickets for the existing V312 modes.

Only called by the V332 predeadline freeze path. The companion verifier runs
offline against already-frozen bytes. It never reconstructs or writes missing
historical full rankings. Relative mass is uncalibrated, not a real win rate.
No network, results, payouts, odds, Formal Fresh, promotion or wagers.
"""
from __future__ import annotations

import math

from boat_edge_v307_pl120_research import rank_120
from boat_edge_v317_ticket_mapper import map_course_mass_to_boat_tickets

MODEL = "BOAT_EDGE_V345_PREDEADLINE_RESEARCH_RANKED120"
MODES = ("national_only", "national_motor", "national_motor_st")
BOATS = set(range(1, 7))


def _near(a, b):
    return (type(a) in (int, float) and type(b) in (int, float)
            and math.isfinite(a) and math.isfinite(b)
            and math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12))


def _courses_and_features(race, candidate):
    if not isinstance(race, dict) or not isinstance(candidate, dict):
        raise ValueError("RANKED120_INPUT_REQUIRED")
    if (candidate.get("model_id") != "BOAT_EDGE_V312_UNCALIBRATED_EXHIBITION_ENTRY_ABLATION"
            or candidate.get("race_key") != race.get("race_key")
            or candidate.get("entry_basis") != "START_EXHIBITION_PROVISIONAL_NOT_ACTUAL"
            or candidate.get("production_eligible") is not False
            or candidate.get("scoring_authorized") is not False):
        raise ValueError("RANKED120_RESEARCH_CANDIDATE_REQUIRED")
    modes = candidate.get("modes")
    if not isinstance(modes, dict) or set(modes) != set(MODES):
        raise ValueError("RANKED120_THREE_MODES_REQUIRED")
    raw_courses = candidate.get("course_by_boat_exhibition")
    if (not isinstance(raw_courses, dict) or
            set(raw_courses) != {str(i) for i in BOATS} or
            any(type(v) is not int for v in raw_courses.values()) or
            set(raw_courses.values()) != BOATS):
        raise ValueError("RANKED120_EXHIBITION_PERMUTATION_REQUIRED")
    courses = {int(boat): course for boat, course in raw_courses.items()}
    entries = race.get("beforeinfo", {}).get("start_exhibition")
    if (not isinstance(entries, list) or len(entries) != 6 or
            any(not isinstance(row, dict) or
                type(row.get("lane")) is not int or type(row.get("course")) is not int
                for row in entries) or
            {row["lane"]: row["course"] for row in entries} != courses):
        raise ValueError("RANKED120_SOURCE_ENTRY_MISMATCH")
    racers = race.get("racers")
    if not isinstance(racers, list) or len(racers) != 6:
        raise ValueError("RANKED120_SIX_RACERS_REQUIRED")
    features = {}
    for racer in racers:
        if not isinstance(racer, dict):
            raise ValueError("RANKED120_RACER_INVALID")
        boat = racer.get("lane")
        if type(boat) is not int or boat not in BOATS or boat in features:
            raise ValueError("RANKED120_RACER_LANES_INVALID")
        national = racer.get("national")
        motor = racer.get("motor")
        if not isinstance(national, dict) or not isinstance(motor, dict):
            raise ValueError("RANKED120_RACER_FEATURES_MISSING")
        n, m, st = national.get("win_rate"), motor.get("quinella_rate"), racer.get("avg_st")
        if (any(type(v) not in (int, float) or not math.isfinite(v) for v in (n, m, st))
                or not 0.01 <= n <= 10 or not 0 <= m <= 100 or not 0.01 <= st <= 1):
            raise ValueError("RANKED120_FEATURES_INVALID")
        features[boat] = (float(n), float(m), float(st))
    if set(features) != BOATS:
        raise ValueError("RANKED120_RACER_LANES_INVALID")
    return modes, courses, features


def derive_120(race, candidate):
    """Recompute V312's unmodified three hypotheses and verify saved Top10/head.

    No callable on-disk backfill path exists: V332 alone commits this payload
    while its live predeadline and immutable-write checks are satisfied.
    """
    modes, courses, features = _courses_and_features(race, candidate)
    output = {}
    for name in MODES:
        weights = {}
        for boat, (national, motor, avg_st) in features.items():
            weight = national
            if name != "national_only":
                weight *= 0.5 + motor / 100
            if name == "national_motor_st":
                weight *= 1.0 / (0.1 + avg_st)
            weights[courses[boat]] = weight
        ranked = rank_120(weights)
        mapped = map_course_mass_to_boat_tickets(
            ranked, courses, "START_EXHIBITION_PROVISIONAL")
        mode = modes[name]
        if (mode.get("ranked_120_count") != 120 or
                mode.get("top10") != [x for x, _ in ranked[:10]] or
                mode.get("top10_boat_research_only") != mapped["top10_boat"]):
            raise ValueError("RESEARCH_120_TOP10_PARITY_MISMATCH:" + name)
        if (not isinstance(mode.get("head_mass"), dict) or
                not isinstance(mode.get("head_mass_boat_research_only"), dict) or
                any(not _near(mode["head_mass"].get(str(c)),
                              sum(p for combo, p in ranked
                                  if combo.startswith(str(c) + "-")))
                        for c in BOATS) or
                any(not _near(mode["head_mass_boat_research_only"].get(str(b)),
                              mapped["head_mass_boat"][str(b)])
                        for b in BOATS)):
            raise ValueError("RESEARCH_120_HEAD_MASS_PARITY_MISMATCH:" + name)
        rows = [
            {"rank": index, "course_combo": row["course_combo"],
             "boat_combo": row["boat_combo"],
             "relative_model_mass": row["relative_model_mass"]}
            for index, row in enumerate(mapped["ranked_120_boat"], 1)
        ]
        if (len(rows) != 120 or
                len({r["boat_combo"] for r in rows}) != 120 or
                not _near(sum(r["relative_model_mass"] for r in rows), 1.0)):
            raise ValueError("RESEARCH_120_MASS_OR_CARDINALITY_INVALID")
        output[name] = rows
    return output


def verify_saved_120(frozen, race, candidate):
    """True only for a complete V345 payload exactly matching the saved Top10.

    Legacy V332 freezes remain valid as Top10-only, never treated as full120.
    """
    marker = frozen.get("research_ranked_120_schema")
    saved = frozen.get("research_ranked_120_by_mode")
    if marker is None and saved is None:
        return False
    if marker != MODEL or not isinstance(saved, dict) or set(saved) != set(MODES):
        raise ValueError("RESEARCH_120_SAVED_SCHEMA_INVALID")
    expected = derive_120(race, candidate)
    if saved != expected:
        raise ValueError("RESEARCH_120_SAVED_REPLAY_MISMATCH")
    return True
