#!/usr/bin/env python3
"""Read-only, window-scoped site V229 diagnostics; never reads outcomes or formal data.

This is observability, NOT a source-authentication or freeze-eligibility certificate.
It cannot create predictions, modify production state, or authorize scoring.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re

JST = timezone(timedelta(hours=9))


def load(path: Path) -> dict:
    """Never follow symlinks into a different source (especially result files)."""
    if path.is_symlink() or any(parent.is_symlink() for parent in path.parents):
        return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except (OSError, ValueError, UnicodeError):
        return {}


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed if parsed.tzinfo is not None else None
    except (TypeError, ValueError, OverflowError):
        return None


def current(source, now: datetime, minutes: int) -> bool:
    if not isinstance(source, dict) or source.get("status") != "ok":
        return False
    fetched = timestamp(source.get("fetched_at"))
    return fetched is not None and 0 <= (now - fetched).total_seconds() <= minutes * 60


def deadline_for(day: str, text: str):
    try:
        # Fail closed on malformed time fields; no inferred deadlines.
        if len(text) != 5 or text[2] != ":":
            return None
        h, m = int(text[:2]), int(text[3:])
        if h > 23 or m > 59 or h < 0 or m < 0:
            return None
        return datetime(int(day[:4]), int(day[4:6]), int(day[6:]),
                        h, m, tzinfo=JST)
    except (TypeError, ValueError, OverflowError):
        return None



def scheduled_catalog(root: Path, day: str):
    """Return validated current-day schedule, or None when untrusted.

    This is a read-only coverage reference, never proof of official source
    readiness and never permission to create a prediction.
    """
    catalog = load(root / "data/today.json")
    if (str(catalog.get("date", "")).replace("-", "") != day
            or not isinstance(catalog.get("venues"), list)):
        return None
    scheduled = {}
    for venue in catalog["venues"]:
        if not isinstance(venue, dict) or not isinstance(venue.get("races"), list):
            return None
        for row in venue["races"]:
            if not isinstance(row, dict):
                return None
            key = row.get("race_key")
            if (not isinstance(key, str) or
                    re.fullmatch(r"20\d{6}-\d{2}-\d{2}", key) is None or
                    not key.startswith(day + "-") or key in scheduled):
                return None
            due = deadline_for(day, row.get("deadline"))
            if due is None:
                return None
            scheduled[key] = due
    return scheduled

def inspect(root: Path, now: datetime) -> dict:
    if now.tzinfo is None:
        raise ValueError("AWARE_CLOCK_REQUIRED")
    root = root.resolve()
    day = now.astimezone(JST).strftime("%Y%m%d")
    active, other, upcoming = [], 0, []
    schedule = scheduled_catalog(root, day)
    race_paths = {path.stem: path for path in
                  sorted((root / "data/races").glob(f"{day}-??-??.json"))}
    scheduled_missing = 0
    unlisted_race_files = 0
    catalog_deadline_mismatches = 0
    if schedule is not None:
        for key, due in sorted(schedule.items()):
            if key in race_paths:
                continue
            scheduled_missing += 1
            mins = (due - now).total_seconds() / 60
            if 2 <= mins <= 10:
                active.append({"race_key": key, "minutes_to_deadline": round(mins, 2),
                               "reasons": ["race_file_missing"],
                               "preliminary_eligible": False})
            else:
                other += 1
                if mins > 10:
                    upcoming.append((mins, key, due))
    for path in race_paths.values():
        key = path.stem
        # Never use an unscheduled race file to infer a legitimate 2–10m
        # decision window when the independently fetched day catalog exists.
        # It could be stale, misidentified or have a different deadline.
        if schedule is not None and key not in schedule:
            unlisted_race_files += 1
            other += 1
            continue
        race = load(path)
        meta = race.get("meta") or {}
        if not isinstance(meta, dict):
            meta = {}
        file_deadline = deadline_for(day, str(meta.get("deadline") or ""))
        deadline = schedule[key] if schedule is not None else file_deadline
        deadline_mismatch = (schedule is not None and
                             file_deadline != deadline)
        if deadline_mismatch:
            catalog_deadline_mismatches += 1
        if deadline is None:
            # Catalog missing: malformed file deadline is an unverified
            # diagnostic, NEVER an eligibility certificate.
            active.append({"race_key": key, "minutes_to_deadline": None,
                           "reasons": ["deadline_unknown"],
                           "preliminary_eligible": False})
            continue
        mins = (deadline - now).total_seconds() / 60
        if not 2 <= mins <= 10:
            other += 1
            if mins > 10:
                upcoming.append((mins, key, deadline))
            continue
        reasons = ["race_deadline_catalog_mismatch"] if deadline_mismatch else []
        audit = race.get("source_audit") or {}
        if not isinstance(audit, dict):
            audit = {}
        if not current(audit.get("race_card"), now, 16):
            reasons.append("race_card_missing_or_stale")
        if not current(audit.get("beforeinfo"), now, 15):
            reasons.append("beforeinfo_missing_or_stale")
        scratch = load(root / "data/site_scratches_v182" / f"{key}.json")
        checked = timestamp(scratch.get("checked_at"))
        if (scratch.get("race_key") != key or scratch.get("blocked") is not False
                or scratch.get("race_card_source_status") != "ok"
                or scratch.get("official_beforeinfo_source_status") != "ok"
                or checked is None or not 0 <= (now - checked).total_seconds() <= 900):
            reasons.append("scratch_unverified_or_stale")
        odds = load(root / "data/site_odds" / f"{key}.json")
        rows = odds.get("trifecta_odds")
        if (odds.get("race_key") != key
                or odds.get("phase") != "PRE_RESULT_PURCHASE_ONLY"
                or not isinstance(rows, dict) or len(rows) != 120):
            reasons.append("odds_120_missing_or_invalid")
        else:
            # V229 rejects 120 unverified or unbound prices even if the
            # number of JSON combinations happens to match. This is only a
            # read-only early diagnostic, not full source authentication.
            if (odds.get("verified_official_dom_v167") is not True
                    or odds.get("available_count") != 120):
                reasons.append("official_odds_dom_proof_missing")
            fetched = timestamp(odds.get("fetched_at"))
            if fetched is None or not 0 <= (now - fetched).total_seconds() <= 900:
                reasons.append("odds_stale")
        snap = root / "data/site_prediction_snapshots" / f"{key}.json"
        if snap.is_symlink() or snap.exists():
            reasons.append("snapshot_already_exists")
        active.append({"race_key": key, "minutes_to_deadline": round(mins, 2),
                       "reasons": reasons, "preliminary_eligible": not reasons})
    counts = dict(sorted(Counter(reason for row in active
                                 for reason in row["reasons"]).items()))
    next_up = min(upcoming) if upcoming else None
    return {
        "schema": "V229_READ_ONLY_WINDOW_DIAGNOSTIC_V2",
        "as_of": now.isoformat(), "day_jst": day,
        "scope": "SITE_ONLY_PRE_RESULT_NOT_FORMAL_FRESH",
        "caveat": ("Preliminary, race-card-current-view checks only; does not prove "
                   "a V229 job actually reached the decision window or validate "
                   "odds byte SHA, raw evidence, full model input, or provenance. "
                   "Catalog coverage is not proof of eligible official sources."),
        "catalog_coverage_verified": schedule is not None,
        "scheduled_races_in_catalog": len(schedule) if schedule is not None else None,
        "scheduled_missing_race_files": scheduled_missing if schedule is not None else None,
        "race_files_not_in_verified_catalog": unlisted_race_files if schedule is not None else None,
        "race_file_deadlines_mismatching_catalog": catalog_deadline_mismatches if schedule is not None else None,
        "races_scanned": len(active) + other,
        "decision_window_races": len(active),
        "preliminary_ready_races": sum(row["preliminary_eligible"] for row in active),
        "outside_window_races": other,
        "reason_counts_in_window": counts,
        "next_race": ({"race_key": next_up[1],
                       "deadline_jst": next_up[2].isoformat()}
                      if next_up else None),
        "window_races": active,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--at", help="Aware ISO timestamp; default current UTC")
    parser.add_argument("--summary-only", action="store_true",
                        help="Keep workflow output compact; include window reasons")
    args = parser.parse_args()
    now = datetime.fromisoformat(args.at) if args.at else datetime.now(timezone.utc)
    if now.tzinfo is None:
        parser.error("--at must include a timezone")
    report = inspect(args.root, now)
    if args.summary_only:
        report = {key: value for key, value in report.items()
                  if key != "window_races"}
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
