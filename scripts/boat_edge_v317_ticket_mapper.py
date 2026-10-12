#!/usr/bin/env python3
"""V317 convert ranked COURSE orders to actual BOAT-NUMBER trifecta tickets.

A course (entry position) is NOT a boat number if entry changes.
This mapping is research-only, with explicit entry basis; no real-world
probability calibration, score, result access, or wager authorization.
"""
from __future__ import annotations

import math
import re

COURSES = set(range(1, 7))
COMBO = re.compile(r"^[1-6]-[1-6]-[1-6]$")


def map_course_mass_to_boat_tickets(ranked, course_by_boat, entry_basis):
    if entry_basis not in ("START_EXHIBITION_PROVISIONAL", "ACTUAL_ENTRY_ASSERTED_NOT_AUTHENTICATED"):
        raise ValueError("ENTRY_BASIS_MUST_BE_EXPLICIT")
    if not isinstance(course_by_boat, dict) or set(course_by_boat) != COURSES:
        raise ValueError("SIX_BOATS_REQUIRED")
    if (any(type(course) is not int for course in course_by_boat.values())
            or set(course_by_boat.values()) != COURSES):
        raise ValueError("SIX_COURSE_PERMUTATION_REQUIRED")
    if not isinstance(ranked, (list, tuple)) or len(ranked) != 120:
        raise ValueError("ALL_120_COURSE_PERMUTATIONS_REQUIRED")
    boat_by_course = {course: boat for boat, course in course_by_boat.items()}
    seen_courses = set()
    tickets = []
    for row in ranked:
        if not isinstance(row, (tuple, list)) or len(row) != 2:
            raise ValueError("INVALID_RANKED_ROW")
        course_combo, mass = row
        if not isinstance(course_combo, str) or COMBO.fullmatch(course_combo) is None:
            raise ValueError("INVALID_COURSE_COMBINATION")
        parts = tuple(int(x) for x in course_combo.split("-"))
        if len(set(parts)) != 3 or parts in seen_courses:
            raise ValueError("DUPLICATED_COURSE_COMBINATION")
        seen_courses.add(parts)
        if type(mass) not in (int, float) or not math.isfinite(mass) or mass <= 0:
            raise ValueError("INVALID_UNCALIBRATED_MODEL_MASS")
        ticket = "-".join(str(boat_by_course[course]) for course in parts)
        tickets.append({"boat_combo": ticket, "course_combo": course_combo,
                        "relative_model_mass": mass})
    if len({t["boat_combo"] for t in tickets}) != 120:
        raise ValueError("NOT_120_UNIQUE_BOAT_COMBOS")
    if not math.isclose(sum(t["relative_model_mass"] for t in tickets), 1.0,
                        rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError("MODEL_MASS_NOT_NORMALIZED")
    return {
        "entry_basis": entry_basis,
        "entry_is_provisional": entry_basis == "START_EXHIBITION_PROVISIONAL",
        "actual_entry_independently_authenticated": False,
        "head_mass_boat": {
            str(boat): sum(t["relative_model_mass"] for t in tickets
                           if t["boat_combo"].startswith(str(boat) + "-"))
            for boat in sorted(COURSES)
        },
        "ranked_120_boat": tickets,
        "top10_boat": [row["boat_combo"] for row in tickets[:10]],
        "source_exhibition_provenance_authenticated": False,
        "calibrated": False,
        "improvement_proven": False,
        "production_eligible": False,
        "scoring_authorized": False,
        "wagers_authorized": False,
    }
