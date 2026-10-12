#!/usr/bin/env python3
"""V312 candidate feature-ablation shadow, research only.

Uses only independently time-qualified source metadata and six documented
PRE_RESULT racer rows. Entry order is START EXHIBITION, not actual race order.
Neither source authenticity nor first-Git-commit timing is established here.
No results, payouts, odds, formal outcomes, network or production changes.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

from boat_edge_v307_pl120_research import rank_120
from boat_edge_v311_existing_source_audit import audit_race
from boat_edge_v317_ticket_mapper import map_course_mass_to_boat_tickets

MODEL = "BOAT_EDGE_V312_UNCALIBRATED_EXHIBITION_ENTRY_ABLATION"


def num(value, minimum, maximum):
    if type(value) not in (int, float) or not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError("INVALID_OR_MISSING_NUMERIC_FEATURE")
    return float(value)


def build_shadow(race):
    audit = audit_race(race)
    sources = audit["source_metadata"]
    if not (sources["race_card"]["pre_deadline_metadata_qualified"]
            and sources["beforeinfo"]["pre_deadline_metadata_qualified"]
            and audit["start_exhibition_course_permutation_recorded"]):
        raise ValueError("PREDEADLINE_SOURCE_AND_EXHIBITION_GATE_NOT_MET")
    racers = race.get("racers")
    if not isinstance(racers, list) or len(racers) != 6:
        raise ValueError("SIX_RACERS_REQUIRED")
    by_boat = {}
    for row in racers:
        if not isinstance(row, dict) or type(row.get("lane")) is not int or row["lane"] not in range(1, 7):
            raise ValueError("INVALID_RACER_LANE")
        if re.search(r"欠場|出走取消|出走取り消し|不出走|scratched|withdrawn",
                     str(row.get("raw_text", "")), re.IGNORECASE):
            raise ValueError("WITHDRAWAL_TEXT_RESEARCH_EXCLUDED")
        if row.get("withdrawn") is True or row.get("cancelled") is True:
            raise ValueError("WITHDRAWAL_FLAG_RESEARCH_EXCLUDED")
        boat = row["lane"]
        if boat in by_boat:
            raise ValueError("DUPLICATE_RACER_LANE")
        national = row.get("national")
        motor = row.get("motor")
        if not isinstance(national, dict) or not isinstance(motor, dict):
            raise ValueError("NATIONAL_AND_MOTOR_REQUIRED")
        # Positive national strength and bounded motor rate; 0 motor rate is
        # accepted only as a recorded numeric measurement, not missingness.
        national_rate = num(national.get("win_rate"), 0.01, 10.0)
        motor_rate = num(motor.get("quinella_rate"), 0.0, 100.0)
        avg_st = num(row.get("avg_st"), 0.01, 1.0)
        by_boat[boat] = (national_rate, motor_rate, avg_st)
    if set(by_boat) != set(range(1, 7)):
        raise ValueError("SIX_DISTINCT_RACERS_REQUIRED")
    entries = race["beforeinfo"]["start_exhibition"]
    courses = {row["lane"]: row["course"] for row in entries}
    if set(courses) != set(range(1, 7)):
        raise ValueError("ENTRY_PERMUTATION_REQUIRED")
    # Explicit, unoptimized ablation hypotheses (not learned or calibrated).
    # Each is positive and preserves input order independence.
    modes = {}
    for name in ("national_only", "national_motor", "national_motor_st"):
        weights = {}
        for boat, (national_rate, motor_rate, avg_st) in by_boat.items():
            weight = national_rate
            if name != "national_only":
                weight *= 0.5 + motor_rate / 100
            if name == "national_motor_st":
                weight *= 1.0 / (0.1 + avg_st)
            weights[courses[boat]] = weight
        ranked = rank_120(weights)
        boat_mapping = map_course_mass_to_boat_tickets(
            ranked, courses, "START_EXHIBITION_PROVISIONAL")
        modes[name] = {
            "top10": [combo for combo, _ in ranked[:10]],
            "top10_label_basis": "COURSE_NOT_BOAT_TICKET",
            "top10_boat_research_only": boat_mapping["top10_boat"],
            "head_mass_boat_research_only": boat_mapping["head_mass_boat"],
            "boat_ticket_label_basis": "EXHIBITION_COURSE_PROVISIONAL",
            "ranked_120_count": len(ranked),
            "head_mass": {
                str(course): sum(p for combo, p in ranked if combo.startswith(str(course) + "-"))
                for course in range(1, 7)
            },
        }
    return {
        "model_id": MODEL,
        "race_key": audit["race_key"],
        "deadline_jst": audit["deadline_jst"],
        "entry_basis": "START_EXHIBITION_PROVISIONAL_NOT_ACTUAL",
        "course_by_boat_exhibition": {str(k): v for k, v in courses.items()},
        "ticket_numbers_are_boat_numbers_only_in_research_field": True,
        "source_metadata_before_deadline": True,
        "source_bytes_independently_authenticated": False,
        "first_git_commit_before_deadline_attested": False,
        "scratch_and_cancellation_independently_verified": False,
        "full_latest_prediction": False,
        "boaters_original_exhibition_verified": False,
        "kyoteibiyori_original_exhibition_verified": False,
        "race_results_accessed": False,
        "formal_fresh_accessed": False,
        "calibrated": False,
        "improvement_proven": False,
        "production_eligible": False,
        "scoring_authorized": False,
        "modes": modes,
    }


def main():
    parser = argparse.ArgumentParser(description="V312 offline race-card feature ablation proposal only")
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args()
    record = json.loads(args.input.read_text(encoding="utf-8"))
    print(json.dumps(build_shadow(record), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
