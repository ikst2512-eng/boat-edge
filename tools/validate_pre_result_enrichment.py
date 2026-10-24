#!/usr/bin/env python3
"""Validate pre-deadline race enrichments without introducing result-derived data.

Usage:
 python tools/validate_pre_result_enrichment.py data/races/YYYYMMDD-JJ-RR.json enrichment.json
 Input enrichment can contain actual_entry (six boat numbers in actual course order)
 and/or course_stats (list of registration_no, course, first/second/third_rate).
 Output: JSON validation report. Never changes the race snapshot or unlocks scoring.
"""
import argparse
import datetime as dt
import json
import math
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

JST = dt.timezone(dt.timedelta(hours=9))
CLEAN_KEYS = {"actual_entry", "course_stats", "source_audit"}
FORBIDDEN_WORDS = ("result", "raceresult", "payout", "finish_order", "scoring", "unlock")


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamp missing")
    d = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if d.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return d.astimezone(JST)


def validate(race, addition, now=None):
    reasons = []
    key = race.get("race_key", "")
    meta = race.get("meta") or {}
    if not re.fullmatch(r"\d{8}-\d{2}-\d{2}", key):
        reasons.append("invalid_race_key")
    else:
        expected_date = key[:4] + "-" + key[4:6] + "-" + key[6:8]
        if meta.get("date") != expected_date or str(meta.get("venue_code", key.split("-")[1])) != key.split("-")[1] or str(meta.get("race_no", int(key.split("-")[2]))) != str(int(key.split("-")[2])):
            reasons.append("race_metadata_mismatch")
    if meta.get("phase") != "PRE_RESULT" or any(meta.get(k) is not False for k in ("results_seen", "unlock", "scoring")):
        reasons.append("race_not_locked_pre_result")
    if not isinstance(addition, dict) or not addition:
        return {"ok": False, "reasons": reasons + ["no_enrichment"], "race_key": key}
    if set(addition) - CLEAN_KEYS:
        reasons.append("unexpected_payload_fields")
    audit = addition.get("source_audit") or {}
    if not isinstance(audit, dict):
        audit = {}
        reasons.append("invalid_audit")
    if not re.fullmatch(r"\d{2}:\d{2}", str(meta.get("deadline", ""))):
        reasons.append("invalid_deadline")
        cutoff = None
    else:
        try:
            cutoff = timestamp(meta["date"] + "T" + meta["deadline"] + ":00+09:00")
        except (ValueError, KeyError):
            cutoff = None
            reasons.append("invalid_deadline")
    now = now or dt.datetime.now(JST)
    def verify_source(kind):
        evidence = audit.get(kind)
        if not isinstance(evidence, dict) or evidence.get("status") != "ok":
            reasons.append(kind + "_source_not_ok")
            return
        url = evidence.get("source", "")
        try:
            p = urlparse(url)
            qs = parse_qs(p.query)
            allowed_path = "/owpc/pc/race/beforeinfo" if kind == "actual_entry" else "/owpc/pc/race/racelist"
            # Course stats may come from separate source, but only explicit
            # HTTPS pages are accepted; do not claim an official source.
            if p.scheme != "https" or p.hostname != "www.boatrace.jp" or p.username or p.password or p.port is not None or p.fragment:
                raise ValueError("source must be exact trusted official host")
            if any(term in (p.path + p.query).lower() for term in FORBIDDEN_WORDS):
                raise ValueError("result-derived source forbidden")
            if p.path != allowed_path:
                raise ValueError("unsupported pre-result source path")
            if set(qs) != {"hd", "jcd", "rno"}:
                raise ValueError("unexpected source query parameters")
            if qs.get("hd") != [key[:8]] or qs.get("jcd") != [key.split("-")[1]] or qs.get("rno") != [str(int(key.split("-")[2]))]:
                raise ValueError("official URL does not match race")
        except (ValueError, TypeError, IndexError):
            reasons.append(kind + "_source_invalid")
        try:
            recorded = timestamp(evidence.get("fetched_at"))
            if cutoff is None or recorded >= cutoff or recorded > now + dt.timedelta(minutes=5):
                reasons.append(kind + "_not_predeadline")
        except ValueError:
            reasons.append(kind + "_timestamp_invalid")
        if not re.fullmatch(r"[a-f0-9]{64}", str(evidence.get("sha256", ""))):
            reasons.append(kind + "_sha_invalid")

    if "actual_entry" in addition:
        values = addition["actual_entry"]
        if not isinstance(values, list) or len(values) != 6 or set(map(str, values)) != set("123456") or any(type(x) is not int for x in values):
            reasons.append("actual_entry_not_permutation")
        verify_source("actual_entry")
    if "course_stats" in addition:
        rows = addition["course_stats"]
        racer_list = race.get("racers", [])
        ids = {str(r.get("registration_no")) for r in racer_list if isinstance(r, dict)}
        if len(racer_list) != 6 or len(ids) != 6 or "None" in ids:
            reasons.append("race_roster_not_six_unique")
        if not isinstance(rows, list) or len(rows) != 6:
            reasons.append("course_stats_incomplete")
        else:
            seen_ids = set()
            seen_courses = set()
            for row in rows:
                if not isinstance(row, dict):
                    reasons.append("course_stats_invalid_row")
                    continue
                reg = str(row.get("registration_no"))
                course = row.get("course")
                seen_ids.add(reg)
                if type(course) is int and 1 <= course <= 6:
                    seen_courses.add(course)
                nums = [row.get(k) for k in ("first_rate", "second_rate", "third_rate")]
                valid_numbers = all(type(x) in (int, float) and math.isfinite(x) and 0 <= x <= 100 for x in nums)
                if type(course) is not int or not 1 <= course <= 6 or not valid_numbers or (valid_numbers and sum(nums) > 100.01):
                    reasons.append("course_stats_invalid_values")
            if len(seen_ids) != 6 or seen_ids != ids or len(seen_courses) != 6:
                reasons.append("course_stats_racer_or_course_mismatch")
        verify_source("course_stats")
    if not any(k in addition for k in ("actual_entry", "course_stats")):
        reasons.append("no_enrichment")
    return {"ok": not reasons, "reasons": sorted(set(reasons)), "race_key": key, "checked": [k for k in ("actual_entry", "course_stats") if k in addition]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("race_json", type=Path)
    parser.add_argument("enrichment_json", type=Path)
    a = parser.parse_args()
    try:
        result = validate(json.loads(a.race_json.read_text()), json.loads(a.enrichment_json.read_text()))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result = {"ok": False, "reasons": ["invalid_input", str(exc)]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
