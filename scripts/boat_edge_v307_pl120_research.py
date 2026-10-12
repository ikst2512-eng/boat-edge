#!/usr/bin/env python3
"""V307 research-only 120-way Plackett-Luce ranker; never a production pick.

Input: six pre-result, source-verified positive relative strengths indexed by
actual entry COURSE, not frame. Optional positional second/third log adjustments
are explicit hypotheses, NOT calibrated probabilities or proven accuracy.
"""
from __future__ import annotations
import argparse
import itertools
import json
import math
from pathlib import Path

MODEL = "BOAT_EDGE_V307_PL120_RESEARCH_UNCALIBRATED"
COURSES = tuple(range(1, 7))


def rank_120(strengths, second_log=None, third_log=None):
    if not isinstance(strengths, dict) or set(strengths) != set(COURSES):
        raise ValueError("SIX_ACTUAL_COURSES_REQUIRED")
    if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0
           for v in strengths.values()):
        raise ValueError("INVALID_POSITIVE_STRENGTH")
    for adjustment in (second_log, third_log):
        if adjustment is not None and (
            not isinstance(adjustment, dict) or set(adjustment) != set(COURSES)
            or any(type(v) not in (int, float) or not math.isfinite(v)
                   for v in adjustment.values())
        ):
            raise ValueError("INVALID_POSITION_ADJUSTMENT")
    # Relative scaling only: this is a baseline ordering model, not calibrated.
    scale = max(strengths.values())
    weights = {c: strengths[c] / scale for c in COURSES}
    raw = []
    # Iterate all ordered podiums; each course is an actual entry position.
    for a, b, c in itertools.permutations(COURSES, 3):
        rest = sum(weights.values()) - weights[a]
        rest2 = rest - weights[b]
        p = (weights[a] / sum(weights.values())) * (weights[b] / rest) * (weights[c] / rest2)
        if second_log:
            p *= math.exp(second_log[b] - max(second_log.values()))
        if third_log:
            p *= math.exp(third_log[c] - max(third_log.values()))
        raw.append((a, b, c, p))
    total = sum(p for _, _, _, p in raw)
    if not math.isfinite(total) or total <= 0:
        raise ValueError("NUMERICAL_FAILURE")
    ranked = sorted(((f"{a}-{b}-{c}", p / total) for a, b, c, p in raw),
                    key=lambda item: (-item[1], item[0]))
    if len(ranked) != 120 or len({x for x, _ in ranked}) != 120:
        raise AssertionError("NOT_120_UNIQUE_TRIFECTAS")
    return ranked


def research_report(strengths, second_log=None, third_log=None):
    ranked = rank_120(strengths, second_log, third_log)
    return {
        "model_id": MODEL, "research_only": True,
        "calibrated": False, "improvement_proven": False,
        "promotion_authorized": False, "wagers_authorized": False,
        "ranked_120": [{"course_combo": x, "relative_model_mass": p} for x, p in ranked],
        "top10": [x for x, _ in ranked[:10]],
        "head_mass": {str(c): sum(p for x, p in ranked if x.startswith(str(c) + "-"))
                      for c in COURSES},
    }


def main():
    parser = argparse.ArgumentParser(description="Research-only offline six-course 120-way ranking")
    parser.add_argument("--input", required=True, type=Path,
                        help="Pre-result strengths JSON only; no result or formal data")
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) - {"strengths", "second_log", "third_log"} or "strengths" not in data:
        raise ValueError("UNRECOGNIZED_INPUT_KEYS")
    # JSON course keys are strings, internally enforce integer actual-course keys.
    def convert(x):
        if x is None:
            return None
        if not isinstance(x, dict):
            raise ValueError("INVALID_COURSE_MAP")
        if set(x) != {str(i) for i in COURSES}:\n            raise ValueError("SIX_ACTUAL_COURSES_REQUIRED")\n        return {int(k): v for k, v in x.items()}
    print(json.dumps(research_report(convert(data["strengths"]),
                                     convert(data.get("second_log")),
                                     convert(data.get("third_log"))),
                     ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
