"""Read-only PRE_RESULT CSV coverage audit. Never reads results or payouts."""
import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROLES = ("stt", "tkz", "sui", "original_exhibition")
JST = timezone(timedelta(hours=9))

def summarize(race_dir: Path, now: datetime):
    day = now.strftime("%Y%m%d")
    cohorts = {"final15m": [], "future": [], "past_locked": []}
    files = sorted(race_dir.glob(f"{day}-??-??.json"))
    invalid_files = []
    for path in files:
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
            clock = (d.get("meta") or {}).get("deadline")
            hh, mm = map(int, clock.split(":"))
            deadline = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
        except (OSError, ValueError, TypeError, AttributeError):
            invalid_files.append(path.name)
            continue
        minutes = (deadline - now).total_seconds() / 60
        group = "final15m" if 0 <= minutes <= 15 else ("future" if minutes > 15 else "past_locked")
        audit = d.get("source_audit") or {}
        entry = {"race": path.stem, "minutes_to_deadline": round(minutes, 2)}
        # Do not promote old per-race observations to fresh evidence merely
        # because this read-only report was generated now.
        def source_reason(role):
            row = audit.get(role) or {}
            reason = row.get("availability_reason", "not_observed")
            clock = row.get("observed_at")
            if not clock:
                return "observation_time_missing" if reason != "not_observed" else reason
            try:
                observed = datetime.fromisoformat(clock)
                if observed.tzinfo is None:
                    return "observation_time_invalid"
                if observed > deadline:
                    return "post_deadline_observation"
                if observed > now or (now - observed).total_seconds() > 600:
                    return "stale_observation"
            except (TypeError, ValueError):
                return "observation_time_invalid"
            return reason
        entry["sources"] = {role: source_reason(role) for role in ROLES}
        cohorts[group].append(entry)
    input_race_count = sum(len(rows) for rows in cohorts.values())
    matched_file_count = len(files)
    invalid_file_count = len(invalid_files)
    assert matched_file_count == input_race_count + invalid_file_count
    input_state = ("NO_RACE_FILES_FOR_DATE" if not files else
                   "RACE_FILES_UNUSABLE" if not input_race_count else
                   "RACE_FILES_PARTIAL" if invalid_files else "RACE_FILES_PRESENT")
    result = {"observation_at": now.isoformat(timespec="seconds"), "phase": "PRE_RESULT",
              "read_only": True, "input_race_count": input_race_count,
              "input_state": input_state, "matched_file_count": matched_file_count,
              "invalid_file_count": invalid_file_count, "invalid_files": invalid_files,
              "cohorts": {}}
    for group, entries in cohorts.items():
        result["cohorts"][group] = {"count": len(entries), "reason_counts": {
            role: dict(sorted(Counter(e["sources"][role] for e in entries).items()))
            for role in ROLES}, "races": entries if group == "final15m" else []}
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--race-dir", default="data/races")
    ap.add_argument("--at", help="ISO8601 JST observation timestamp")
    args = ap.parse_args()
    now = datetime.fromisoformat(args.at) if args.at else datetime.now(JST)
    if now.tzinfo is None:
        ap.error("--at must contain a timezone offset")
    print(json.dumps(summarize(Path(args.race_dir), now.astimezone(JST)), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
