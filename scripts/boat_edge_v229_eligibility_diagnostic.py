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


def inspect(root: Path, now: datetime) -> dict:
    if now.tzinfo is None:
        raise ValueError("AWARE_CLOCK_REQUIRED")
    root = root.resolve()
    day = now.astimezone(JST).strftime("%Y%m%d")
    active, other, upcoming = [], 0, []
    for path in sorted((root / "data/races").glob(f"{day}-??-??.json")):
        key = path.stem
        race = load(path)
        meta = race.get("meta") or {}
        if not isinstance(meta, dict):
            meta = {}
        deadline = deadline_for(day, str(meta.get("deadline") or ""))
        if deadline is None:
            # Surface a malformed deadline as an explicit diagnostics failure.
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
        reasons = []
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
                   "odds byte SHA, raw evidence, full model input, or provenance."),
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
