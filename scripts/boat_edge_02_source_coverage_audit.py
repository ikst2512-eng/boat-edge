#!/usr/bin/env python3
"""Read-only race-source audit. No network, workflow triggers, or prediction writes."""
import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import json
import math
from pathlib import Path
import re

FIELDS = ("race_card", "beforeinfo", "original_exhibition", "odds")
KEY = re.compile(r"^(20\d{6})-(0[1-9]|1\d|2[0-4])-(0[1-9]|1[0-2])$")
JST = timezone(timedelta(hours=9))


def load_expected(path, day):
    """An independently supplied schedule, never inferred from saved cards."""
    if path is None:
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    keys = document.get("race_keys")
    if document.get("date_jst") != day or not isinstance(keys, list):
        raise ValueError("schedule date or race_keys invalid")
    if any(not isinstance(key, str) or not KEY.fullmatch(key) or key[:8] != day for key in keys):
        raise ValueError("schedule includes invalid or wrong-day race keys")
    if not keys:
        raise ValueError("empty independent schedule not accepted")
    if len(set(keys)) != len(keys):
        raise ValueError("duplicate scheduled race")
    return set(keys)


def load_catalog(path, day):
    """Load same-day race identities from an existing independent site catalog."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or doc.get("date") != f"{day[:4]}-{day[4:6]}-{day[6:]}":
        raise ValueError("catalog date mismatch")
    venues = doc.get("venues")
    if not isinstance(venues, list) or not venues:
        raise ValueError("missing catalog venues")
    keys = []
    deadlines = {}
    venue_codes = set()
    for venue in venues:
        if not isinstance(venue, dict) or not isinstance(venue.get("races"), list):
            raise ValueError("invalid catalog venue")
        code = str(venue.get("jcd", "")).zfill(2)
        if code not in {f"{i:02d}" for i in range(1, 25)} or code in venue_codes:
            raise ValueError("invalid or duplicate catalog venue")
        venue_codes.add(code)
        for race in venue["races"]:
            if not isinstance(race, dict):
                raise ValueError("invalid catalog race")
            key, deadline = race.get("race_key"), race.get("deadline")
            if not isinstance(key, str) or not KEY.fullmatch(key) or not key.startswith(day + "-"):
                raise ValueError("catalog race key invalid")
            if key[9:11] != str(venue.get("jcd", "")).zfill(2):
                raise ValueError("catalog venue mismatch")
            if not isinstance(deadline, str) or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", deadline):
                raise ValueError("catalog deadline invalid")
            keys.append(key)
            deadlines[key] = deadline
    if not keys or len(keys) != len(set(keys)):
        raise ValueError("empty or duplicate catalog race")
    return set(keys), deadlines


def retry_candidates(rows, day, now=None):
    """Diagnostics only: never execute fetches or bypass deadline locks."""
    now = datetime.now(JST) if now is None else now
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("aware JST clock required")
    now = now.astimezone(JST)
    candidates = []
    for row in rows:
        key = row["race_key"]
        deadline = row.get("deadline")
        if row.get("error") or not isinstance(deadline, str) or not re.fullmatch(r"\d{2}:\d{2}", deadline):
            continue
        try:
            due = datetime.strptime(day + deadline, "%Y%m%d%H:%M").replace(tzinfo=JST)
        except ValueError:
            continue
        if due <= now:
            continue
        statuses = row.get("statuses", {})
        for field in ("race_card", "beforeinfo"):
            # Not yet in the official beforeinfo window is not a retryable failure.
            # Unknown statuses also fail closed until classified by the owner.
            if statuses.get(field) in ("missing", "error", "fetch_error", "timeout", "incomplete_exhibition", "unverified_ok"):
                candidates.append({"race_key": key, "source": field,
                                   "reason": statuses.get(field, "not_recorded"),
                                   "deadline_jst": due.isoformat(),
                                   "automatic_fetch_authorized": False})
    return candidates


def _valid_timestamp(value):
    try:
        stamp = datetime.fromisoformat(value)
        return stamp.tzinfo is not None and stamp.utcoffset() is not None
    except ValueError:
        return False


def audit(root, day, expected=None, now=None, deadlines=None):
    counts = {field: Counter() for field in FIELDS}
    rows = []
    for path in sorted((root / "data" / "races").glob(day + "-*.json")):
        if not KEY.fullmatch(path.stem):
            continue
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(obj, dict):
                raise ValueError("invalid race object")
            if obj.get("race_key") != path.stem:
                raise ValueError("race_key mismatch")
            src = obj.get("source_audit") or {}
            meta = obj.get("meta") or {}
            if not isinstance(src, dict) or not isinstance(meta, dict):
                raise ValueError("invalid audit/meta structure")
            if (meta.get("date") not in (None, day[:4] + "-" + day[4:6] + "-" + day[6:])
                    or str(meta.get("venue_code", path.stem[9:11])).zfill(2) != path.stem[9:11]
                    or meta.get("phase") not in (None, "PRE_RESULT")):
                raise ValueError("race meta identity or phase mismatch")
            statuses = {}
            source_fetched_at = {}
            for field in FIELDS:
                entry = src.get(field)
                status = entry.get("status", "not_recorded") if isinstance(entry, dict) else "not_recorded"
                if not isinstance(status, str):
                    status = "invalid_source_status"
                if status == "ok" and not (
                        isinstance(entry, dict)
                        and isinstance(entry.get("sha256"), str)
                        and re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])
                        and isinstance(entry.get("fetched_at"), str)
                        and _valid_timestamp(entry["fetched_at"])):
                    status = "unverified_ok"
                if status == "ok" and field == "beforeinfo":
                    cov = entry.get("six_boat_coverage") or {}
                    if not isinstance(cov, dict) or cov.get("six_boat_complete") is not True:
                        status = "incomplete_exhibition"
                if status == "ok" and field == "original_exhibition":
                    original = obj.get("original_exhibition")
                    labels = original.get("labels") if isinstance(original, dict) else None
                    boats = original.get("boats") if isinstance(original, dict) else None
                    if not (
                        isinstance(labels, list) and 1 <= len(labels) <= 3
                        and all(isinstance(x, str) and x.strip() for x in labels)
                        and isinstance(boats, list) and len(boats) == 6
                        and {b.get("lane") for b in boats if isinstance(b, dict)} == set(range(1, 7))
                        and all(isinstance(b, dict)
                                and isinstance(b.get("values"), list)
                                and len(b["values"]) == len(labels)
                                and all(type(v) in (int, float) and math.isfinite(v)
                                        for v in b["values"])
                                for b in boats)
                    ):
                        status = "incomplete_original_exhibition"
                statuses[field] = status
                source_fetched_at[field] = entry.get("fetched_at") if isinstance(entry, dict) else None
                counts[field][status] += 1
            rows.append({"race_key": path.stem, "venue": meta.get("venue"),
                         "record_updated_at": meta.get("updated_at"),
                         "source_fetched_at": source_fetched_at,
                         "deadline": meta.get("deadline"), "statuses": statuses})
        except (OSError, UnicodeError, ValueError, TypeError) as error:
            rows.append({"race_key": path.stem, "error": type(error).__name__})
            for field in FIELDS:
                counts[field]["invalid_record"] += 1
    saved_keys = {row["race_key"] for row in rows if "error" not in row}
    valid_rows = [row for row in rows if "error" not in row]
    missing = sorted(expected - saved_keys) if expected is not None else None
    missing_deadlines = {key: deadlines[key] for key in missing if deadlines and key in deadlines} if missing is not None else None
    # Missing entire cards have no local metadata; a trusted catalog deadline
    # permits a diagnostic only, never automatic fetching or retroactive writing.
    missing_rows = [
        {"race_key": key, "deadline": missing_deadlines[key],
         "statuses": {"race_card": "missing", "beforeinfo": "not_recorded"}}
        for key in (missing or []) if missing_deadlines and key in missing_deadlines
    ]
    unexpected = sorted(saved_keys - expected) if expected is not None else None
    # A saved race does not by itself establish data-source completeness.
    n = len(rows)
    summary = {}
    for field in FIELDS:
        success = counts[field]["ok"]
        summary[field] = {"saved_races": n, "recorded_ok_with_metadata": success,
                          "saved_card_success_percent": round(100 * success / n, 2) if n else None,
                          "by_status": dict(sorted(counts[field].items())),
                          "scheduled_recorded_ok_percent": (
                              round(100 * sum(
                                  1 for row in rows
                                  if row["race_key"] in expected
                                  and row.get("statuses", {}).get(field) == "ok"
                              ) / len(expected), 2)
                              if expected else None)}
    clock = datetime.now(JST) if now is None else now
    if clock.tzinfo is None or clock.utcoffset() is None:
        raise ValueError("aware clock required")
    clock = clock.astimezone(JST)
    stale_wait = []
    for row in valid_rows:
        if row.get("statuses", {}).get("beforeinfo") != "published_wait":
            continue
        deadline = row.get("deadline")
        if not isinstance(deadline, str) or not re.fullmatch(r"(?:[01]\\d|2[0-3]):[0-5]\\d", deadline):
            continue
        due = datetime.strptime(day + deadline, "%Y%m%d%H:%M").replace(tzinfo=JST)
        if due <= clock:
            stale_wait.append({
                "race_key": row["race_key"],
                "deadline_jst": due.isoformat(),
                "last_beforeinfo_fetch_jst": row.get("source_fetched_at", {}).get("beforeinfo"),
                "interpretation": "PERSISTED_WAIT_AFTER_DEADLINE_NOT_PROOF_OF_RETRY_FAILURE",
            })
    return {
        "schema": "BOAT_EDGE_02_READONLY_SOURCE_COVERAGE_V1",
        "date_jst": day, "generated_at_jst": datetime.now(JST).isoformat(),
        "venues_total": 24, "saved_venues": len({r["race_key"][9:11] for r in valid_rows}),
        "saved_races": n,
        "valid_saved_races": len(valid_rows),
        "invalid_saved_races": n - len(valid_rows),
        "past_deadline_persisted_beforeinfo_wait": stale_wait,
        "published_wait_beforeinfo_count": sum(r.get("statuses", {}).get("beforeinfo") == "published_wait" for r in valid_rows),
        "missing_original_exhibition_count": sum(r.get("statuses", {}).get("original_exhibition") == "missing" for r in valid_rows),
        "beforeinfo_published_wait_with_fetch_timestamp": sum(
            r.get("statuses", {}).get("beforeinfo") == "published_wait"
            and bool(r.get("source_fetched_at", {}).get("beforeinfo")) for r in valid_rows),
        "expected_scheduled_races": len(expected) if expected is not None else None,
        "missing_scheduled_race_keys": missing,
        "missing_scheduled_deadlines": missing_deadlines,
        "unexpected_saved_race_keys": unexpected,
        "scheduled_card_presence_percent": (
            round(100 * len(saved_keys & expected) / len(expected), 2)
            if expected else None),
        "all_scheduled_race_success_percent": None,
        "collection_state": "PROVISIONAL_NO_LIVE_SOURCE_ATTESTATION",
        "source_statuses_do_not_establish_final_deadline_capture": True,
        "note": "Saved-card rate only; missing scheduled races, live source verification and original exhibition values are not proven.",
        "summary": summary, "retry_candidates_diagnostics_only": retry_candidates(rows + missing_rows, day, now), "rows": rows,
    }


def inspect_health(path):
    """Read-only consistency check; never equate a fetch count with saved coverage."""
    h = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(h, dict):
        raise ValueError("invalid health report")
    checks = [
        ("urgent_original_exhibition",
         "beforeinfo_urgent_15m_targets",
         ("original_exhibition_urgent_15m_complete",
          "original_exhibition_urgent_15m_missing")),
        ("urgent_beforeinfo",
         "beforeinfo_urgent_15m_targets",
         ("beforeinfo_urgent_15m_ok",
          "beforeinfo_urgent_15m_published_wait",
          "beforeinfo_urgent_15m_error")),
    ]
    diagnostics = []
    for label, denominator, parts in checks:
        total = h.get(denominator)
        numbers = [h.get(part) for part in parts]
        if any(type(v) is not int or v < 0 for v in [total, *numbers]):
            diagnostics.append({"check": label, "status": "unknown_invalid_counts"})
        elif sum(numbers) != total:
            diagnostics.append({"check": label, "status": "inconsistent",
                                "target": total, "classified": sum(numbers)})
        else:
            diagnostics.append({"check": label, "status": "arithmetically_consistent",
                                "target": total})
    return {"updated_at": h.get("updated_at"), "checks": diagnostics,
            "note": "Health counts are not proof of persisted predeadline sources."}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--day", required=True, help="JST date in YYYYMMDD")
    parser.add_argument("--output", type=Path, help="Optional explicit report destination")
    parser.add_argument("--health", type=Path, help="Optional read-only data/health.json check")
    parser.add_argument("--catalog", type=Path, help="Existing same-day data/today.json (read only)")
    parser.add_argument("--schedule", type=Path,
                        help="Trusted independent JSON schedule: date_jst and race_keys")
    args = parser.parse_args()
    if not re.fullmatch(r"20\d{6}", args.day):
        parser.error("--day must be YYYYMMDD")
    try:
        if args.schedule and args.catalog:
            parser.error("use only one of --schedule and --catalog")
        expected, deadlines = load_catalog(args.catalog, args.day) if args.catalog else (load_expected(args.schedule, args.day), None)
    except (OSError, ValueError, TypeError) as exc:
        parser.error("invalid schedule: " + str(exc))
    report = audit(args.root, args.day, expected, deadlines=deadlines)
    if args.health:
        try:
            report["health_consistency"] = inspect_health(args.health)
        except (OSError, UnicodeError, ValueError, TypeError) as exc:
            parser.error("invalid health: " + str(exc))
    serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
