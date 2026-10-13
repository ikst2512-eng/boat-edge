#!/usr/bin/env python3
"""V334 bounded, current-day SITE research capture and freeze batch.

Select races in the final N minutes from existing current-day pre-result SITE
race cards. With explicit --capture, call V332 (which derives the 3 public
provider URLs, validates raw hashes and freezes research-only 120-way picks).
A dry-run is read-only. Never touches result pages, payouts, odds, formal Fresh,
production predictions, purchases or shared GitHub workflows.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path

from boat_edge_v314_three_source_evidence import KEY
from boat_edge_v315_source_capture import real_fetch
from boat_edge_v318_shadow_freeze import JST, parse_time
from boat_edge_v332_live_local_freeze import live_local_freeze
from boat_edge_v361_source_readiness import scan_preflight
from boat_edge_v363_fast_lane_gap_diagnostic import classify as upstream_gap_diagnostic


def _now(clock):
    now = clock() if clock is not None else datetime.now(JST)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("AWARE_JST_CLOCK_REQUIRED")
    return now.astimezone(JST)


def live_window(root, now, window_minutes=15, max_races=12):
    if type(window_minutes) is not int or not 1 <= window_minutes <= 30:
        raise ValueError("INVALID_WINDOW_MINUTES")
    if type(max_races) is not int or not 1 <= max_races <= 12:
        raise ValueError("INVALID_MAX_RACES")
    root = Path(root).resolve()
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("AWARE_JST_CLOCK_REQUIRED")
    now = now.astimezone(JST)
    date = now.strftime("%Y%m%d")
    races = root / "data/races"
    eligible, skipped = [], []
    observed = {
        "current_day_race_card_files": 0,
        "closed_before_scan": 0,
        "outside_final_window": 0,
        "less_than_two_minutes": 0,
        "already_frozen_in_this_checkout": 0,
    }
    if races.is_dir():
        for path in sorted(races.glob(date + "-??-??.json")):
            if not KEY.fullmatch(path.stem):
                continue
            key = path.stem
            observed["current_day_race_card_files"] += 1
            if path.is_symlink():
                skipped.append({"race_key": key, "reason": "RACE_SYMLINK_FORBIDDEN"})
                continue
            try:
                scan_raw = path.read_bytes()
                obj = json.loads(scan_raw)
                # Treat malformed race documents as per-race skips; a single
                # broken card must not interrupt the rest of today's batch.
                if not isinstance(obj, dict):
                    raise ValueError("RACE_DOCUMENT_NOT_OBJECT")
                meta = obj.get("meta")
                race_date = meta.get("date") if isinstance(meta, dict) else None
                if (not isinstance(meta, dict) or obj.get("race_key") != key or
                        not isinstance(race_date, str) or
                        race_date.replace("-", "") != date):
                    raise ValueError("RACE_METADATA_MISMATCH")
                if meta.get("phase") != "PRE_RESULT" or any(
                    meta.get(x) is not False for x in ("results_seen", "unlock", "scoring")
                ):
                    raise ValueError("PRE_RESULT_GUARD_NOT_READY")
                deadline = parse_time(meta["date"] + "T" + meta["deadline"] + ":00+09:00")
                minutes_left = (deadline - now).total_seconds() / 60
                if minutes_left <= 0:
                    observed["closed_before_scan"] += 1
                    continue  # Never process or backfill closed races.
                if minutes_left > window_minutes:
                    observed["outside_final_window"] += 1
                    continue  # Only deadline-near races, not future card crawling.
                if minutes_left < 2:
                    observed["less_than_two_minutes"] += 1
                    skipped.append({"race_key": key, "reason": "LESS_THAN_TWO_MINUTES"})
                    continue
                target = root / "data/research_local_v332" / date / (key + ".json")
                if target.is_file() or target.is_symlink():
                    observed["already_frozen_in_this_checkout"] += 1
                    skipped.append({"race_key": key, "reason": "RESEARCH_FREEZE_EXISTS"})
                    continue
                selection_scan = scan_preflight(obj, scan_raw, now)
                selection_scan["upstream_fast_lane_gap_diagnostic"] = (
                    upstream_gap_diagnostic(root, selection_scan)
                )
                eligible.append((deadline, key, round(minutes_left, 2), selection_scan))
            except (OSError, UnicodeError, ValueError, TypeError, KeyError) as exc:
                skipped.append({"race_key": key, "reason": "RACE_WINDOW_INVALID:" + str(exc)})
    eligible.sort(key=lambda t: (t[0], t[1]))
    selected = eligible[:max_races]
    return {
        "date": date,
        "window_minutes": window_minutes,
        "max_races": max_races,
        "candidates": [{"race_key": key, "minutes_left": minutes,
                        "selection_scan": scan}
                       for _, key, minutes, scan in selected],
        "deferred_due_to_cap": [key for _, key, _, _ in eligible[max_races:]],
        "skipped": skipped,
        "coverage": {
            **observed,
            "invalid_or_guarded_race_cards": sum(
                s["reason"] != "LESS_THAN_TWO_MINUTES"
                and s["reason"] != "RESEARCH_FREEZE_EXISTS" for s in skipped
            ),
            "eligible_before_cap": len(eligible),
            "selected": len(selected),
            "deferred_due_to_cap": max(0, len(eligible) - len(selected)),
        },
    }


def run(root, capture=False, window_minutes=15, max_races=12,
        clock=None, fetcher=real_fetch):
    root = Path(root).resolve()
    selected = live_window(root, _now(clock), window_minutes, max_races)
    completed, failures = [], []
    if capture:
        for race in selected["candidates"]:
            key = race["race_key"]
            try:
                # Recheck real/fake clock and all input timestamps for each race.
                frozen = live_local_freeze(root, key, capture=True,
                                           clock=clock, fetcher=fetcher)
                completed.append({
                    "race_key": key, "path": frozen["path"],
                    "sha256": frozen["sha256"],
                    "modes": sorted(frozen["record"]["candidate"]["modes"]),
                })
            except (OSError, ValueError, KeyError, TypeError) as exc:
                failures.append({"race_key": key, "reason": str(exc),
                                 "selection_scan": race["selection_scan"]})
    coverage = selected["coverage"]
    if coverage["current_day_race_card_files"] == 0:
        readiness = "NO_CURRENT_DAY_RACE_CARDS"
    elif not selected["candidates"]:
        readiness = "NO_ELIGIBLE_RACES_IN_CURRENT_FINAL_WINDOW"
    elif not capture:
        readiness = "ELIGIBLE_RACES_DRY_RUN_ONLY"
    elif not completed:
        readiness = "ELIGIBLE_BUT_NO_FREEZE_COMPLETED"
    elif failures:
        readiness = "PARTIAL_RESEARCH_CAPTURE"
    else:
        readiness = "SELECTED_RACES_FROZEN_LOCALLY"
    return {
        "model_id": "BOAT_EDGE_V334_SITE_RESEARCH_BATCH_ONLY",
        "run_diagnostic": readiness,
        "diagnostic_is_not_an_accuracy_or_formal_readiness_claim": True,
        "immutable_across_independent_actions_runs_verified": False,
        "window": selected,
        "capture_requested": capture is True,
        "completed": completed, "failures": failures,
        "completed_count": len(completed),
        "independent_source_authentication_proven": False,
        "original_exhibition_verified": False,
        "actual_course_independently_verified": False,
        "accuracy_improvement_proven": False,
        "results_read": False, "formal_fresh_read": False,
        "production_model_changed": False, "wagers_authorized": False,
    }


def main():
    parser = argparse.ArgumentParser(description="Select current-day final-15m races; --capture writes research only")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--capture", action="store_true",
                        help="Opt-in to bounded public HTML capture and one-time research freeze")
    parser.add_argument("--window-minutes", type=int, default=15)
    parser.add_argument("--max-races", type=int, default=12)
    args = parser.parse_args()
    print(json.dumps(run(args.root, capture=args.capture,
                         window_minutes=args.window_minutes, max_races=args.max_races),
                     ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
