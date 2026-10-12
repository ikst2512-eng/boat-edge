#!/usr/bin/env python3
"""V330 batch SITE-only research readiness: actionable blockers in one pass.

Dry-run: never calls V328 freeze, never fetches network, never reads outcomes,
formal Fresh, odds or payouts. It inspects race-card timing, V312 feature
eligibility and V316 local receipt consistency for currently open races.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
from pathlib import Path

from boat_edge_v312_pre_result_ablation import build_shadow
from boat_edge_v316_receipt_assemble import assemble
from boat_edge_v318_shadow_freeze import JST, KEY, parse_time


def inspect(root, key, now):
    row = {"race_key": key, "ready_for_live_freeze": False, "blockers": []}
    try:
        race_path = root / "data" / "races" / (key + ".json")
        if race_path.is_symlink():
            raise ValueError("RACE_SYMLINK_FORBIDDEN")
        race = json.loads(race_path.read_text(encoding="utf-8"))
        meta = race.get("meta")
        if race.get("race_key") != key or not isinstance(meta, dict):
            raise ValueError("INVALID_RACE_ID_OR_META")
        if meta.get("phase") != "PRE_RESULT" or any(meta.get(k) is not False for k in ("results_seen", "unlock", "scoring")):
            raise ValueError("RESULT_OR_LOCK_FLAG")
        if meta.get("date", "").replace("-", "") != key[:8]:
            raise ValueError("DATE_MISMATCH")
        deadline = parse_time(meta["date"] + "T" + meta["deadline"] + ":00+09:00")
        if now >= deadline:
            raise ValueError("CLOSED_RACE_NO_BACKFILL")
        updated = datetime.fromisoformat(meta["updated_at"])
        if updated.tzinfo is None or updated >= deadline or updated > now:
            raise ValueError("RACE_UPDATED_AFTER_DEADLINE_OR_FUTURE")
        audit = race.get("source_audit")
        if not isinstance(audit, dict):
            raise ValueError("SOURCE_AUDIT_MISSING")
        for name in ("race_card", "beforeinfo"):
            source = audit.get(name)
            if not isinstance(source, dict) or source.get("status") != "ok":
                raise ValueError("SOURCE_MISSING_" + name)
            fetched = datetime.fromisoformat(source["fetched_at"])
            if fetched.tzinfo is None or fetched >= deadline or fetched > now:
                raise ValueError("SOURCE_LATE_OR_FUTURE_" + name)
        build_shadow(race)
        report = assemble(root, key, deadline.isoformat())
        if not report["ready_for_research_review"]:
            missing = report.get("missing_or_invalid_receipts", {})
            raise ValueError("THREE_SOURCE_RECEIPTS_NOT_READY:" + ",".join(sorted(missing)))
        row["ready_for_live_freeze"] = True
    except (ValueError, TypeError, KeyError, OSError) as exc:
        row["blockers"].append(str(exc))
    return row


def scan(root, date, now=None):
    root = root.resolve()
    now = now if now is not None else datetime.now(JST)
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("AWARE_CLOCK_REQUIRED")
    now = now.astimezone(JST)
    if not isinstance(date, str) or len(date) != 8 or not date.isdigit():
        raise ValueError("YYYYMMDD_REQUIRED")
    folder = root / "data/races"
    rows = []
    if folder.is_dir():
        for path in sorted(folder.glob(date + "-??-??.json")):
            if KEY.fullmatch(path.stem):
                rows.append(inspect(root, path.stem, now))
    counts = Counter(block for row in rows for block in row["blockers"])
    return {"model_id": "BOAT_EDGE_V330_SITE_RESEARCH_READINESS_DRY_RUN",
            "date": date, "races_inspected": len(rows),
            "ready_for_live_freeze": sum(r["ready_for_live_freeze"] for r in rows),
            "blocker_counts": dict(sorted(counts.items())),
            "rows": rows, "network_fetch": False, "results_read": False,
            "formal_fresh_read": False, "writes_performed": False,
            "accuracy_improvement_proven": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    print(json.dumps(scan(args.root, args.date), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
