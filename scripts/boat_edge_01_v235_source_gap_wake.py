#!/usr/bin/env python3
"""Read-only prospective V235 source-gap wake; never authorizes a prediction.

Only the already-existing V235 worker can fetch official PRE_RESULT inputs.
No results, payouts, formal predictions, odds fabrication or new writers.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

from scripts.boat_edge_v230_fast_lane import JST, due_for, load as load_race, targets
from scripts.boat_edge_v220_site_ops import source_status


def probe(root: Path, now: datetime) -> dict:
    report = {
        "schema": "GATE1C_V235_SOURCE_GAP_WAKE_V1",
        "scope": "UNFROZEN_PRE_RESULT_2_TO_10M_SOURCE_REFRESH_ONLY",
        "eligible_denominator_proven": False,
        "wake_needed": False,
        "race_keys": [],
        "gap_counts": {},
    }
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        return report
    root = Path(root).resolve()
    now = now.astimezone(JST)
    data = root / "data"
    formal_path = data / "formal_status.json"
    catalog_path = data / "today.json"
    if (data.is_symlink() or formal_path.is_symlink() or catalog_path.is_symlink()
            or not formal_path.is_file() or not catalog_path.is_file()):
        return report
    try:
        formal = json.loads(formal_path.read_text(encoding="utf8"))
        plan = json.loads(catalog_path.read_text(encoding="utf8"))
    except (OSError, UnicodeError, ValueError):
        return report
    if not isinstance(formal, dict) or not isinstance(plan, dict):
        return report
    guards = formal.get("guards")
    cohort = formal.get("formalFirst100")
    if (not isinstance(guards, dict) or not isinstance(cohort, dict)
            or any(guards.get(k) is not False for k in ("results_seen", "unlock", "scoring"))
            or guards.get("RESULT_UNLOCK_TOKEN") is not None
            or cohort.get("races") != 0):
        return report
    day = now.strftime("%Y%m%d")
    if (str(plan.get("date", "")).replace("-", "") != day
            or plan.get("phase") != "PRE_RESULT"
            or any(plan.get(k) is not False for k in ("results_seen", "unlock", "scoring"))):
        return report
    reasons = Counter()
    try:
        # Reuse V230's existing identity, current-day, six-racer, immutable
        # snapshot and BOTH catalog/race-clock safety gates.
        candidates = targets(root, now, max_target=12)
        for key in candidates:
            path = data / "races" / (key + ".json")
            snapshot = data / "site_prediction_snapshots" / (key + ".json")
            if path.is_symlink() or snapshot.is_symlink() or snapshot.exists():
                continue
            race = load_race(path)
            if not isinstance(race, dict) or race.get("race_key") != key:
                continue
            meta = race.get("meta")
            if not isinstance(meta, dict):
                continue
            due = due_for(key, meta.get("deadline"))
            if due is None or not 2 <= (due - now).total_seconds() / 60 <= 10:
                continue
            # Fully ready inputs belong to the already-established V229
            # nudge, never duplicate its dispatch with a V235 source refresh.
            gaps = set(source_status(root, key, now))
            if "frozen_prediction_missing_or_invalid" not in gaps:
                continue
            gaps.discard("frozen_prediction_missing_or_invalid")
            if not gaps:
                continue
            report["race_keys"].append(key)
            reasons.update(gaps)
    except (ValueError, OSError, TypeError, AttributeError, KeyError, OverflowError):
        report["race_keys"] = []
        return report
    report["race_keys"] = sorted(set(report["race_keys"]))
    report["gap_counts"] = dict(sorted(reasons.items()))
    report["wake_needed"] = bool(report["race_keys"])
    return report


def main() -> None:
    print(json.dumps(probe(Path("."), datetime.now(timezone.utc)), sort_keys=True))


if __name__ == "__main__":
    main()
