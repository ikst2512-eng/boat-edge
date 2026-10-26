#!/usr/bin/env python3
"""Read-only selection of near-deadline PRE_RESULT race states; no result access."""
import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

JST = timezone(timedelta(hours=9))

def select(root, now, minutes=45, limit=6):
    out = []
    for path in sorted(Path(root).glob(now.strftime("%Y%m%d") + "-??-??.json")):
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
            meta = state["meta"]
            if meta.get("phase") != "PRE_RESULT" or meta.get("results_seen") is not False:
                continue
            deadline = datetime.strptime(now.strftime("%Y%m%d") + " " + meta["deadline"], "%Y%m%d %H:%M").replace(tzinfo=JST)
            if not now < deadline <= now + timedelta(minutes=minutes):
                continue
            audit = state.get("source_audit") or {}
            preview = ("stt", "tkz", "sui", "original_exhibition")
            stale = []
            for role in preview:
                item = audit.get(role) or {}
                observed = item.get("observed_at")
                if observed:
                    age = (now - datetime.fromisoformat(observed)).total_seconds() / 60
                    if age > 15:
                        stale.append({"role": role, "age_minutes": round(age, 1)})
            out.append({"race_key": path.stem, "deadline_jst": deadline.isoformat(),
                        "preview_missing_roles": [r for r in preview if (audit.get(r) or {}).get("status") != "ok"],
                        "preview_observations_older_than_15m": stale})
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            continue
    return sorted(out, key=lambda x: (x["deadline_jst"], x["race_key"]))[:limit]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--minutes", type=int, default=45)
    p.add_argument("--limit", type=int, default=6)
    p.add_argument("--output", default="fresh_upcoming_state_targets.json")
    args = p.parse_args()
    if not 0 < args.minutes <= 180 or not 0 < args.limit <= 50:
        p.error("invalid window")
    now = datetime.now(JST)
    out = {"schema": "BOAT_EDGE_UPCOMING_STATE_TARGETS_V1", "observed_at_jst": now.isoformat(),
           "results_accessed": False, "formal_unlock_authorized": False,
           "targets": select("data/races", now, args.minutes, args.limit)}
    Path(args.output).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main()
