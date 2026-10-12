"""V307 fail-closed adapter for independently frozen pre-result course strengths.

No extraction from race results, odds, exhibition course as actual course,
or inferred entry. This module accepts an explicit six-boat provenance record.
"""
import datetime
import hashlib
import json

REQUIRED = {"race_key", "deadline_jst", "frozen_at_jst", "source_sha256",
            "actual_course_by_boat", "strength_by_boat", "source_verified"}
BOATS = set(range(1, 7))


def validated_course_strengths(record):
    if not isinstance(record, dict) or set(record) != REQUIRED:
        raise ValueError("INVALID_PROVENANCE_SCHEMA")
    if record["source_verified"] is not True:
        raise ValueError("SOURCE_NOT_VERIFIED")
    sha = record["source_sha256"]
    if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
        raise ValueError("INVALID_SOURCE_SHA256")
    if not isinstance(record["race_key"], str) or not record["race_key"]:
        raise ValueError("INVALID_RACE_KEY")
    def timestamp(s):
        if not isinstance(s, str) or not s.endswith("+09:00"):
            raise ValueError("JST_OFFSET_REQUIRED")
        return datetime.datetime.fromisoformat(s)
    if timestamp(record["frozen_at_jst"]) >= timestamp(record["deadline_jst"]):
        raise ValueError("NOT_FROZEN_BEFORE_DEADLINE")
    def keys(m):
        if not isinstance(m, dict) or set(m) != {str(i) for i in BOATS}:
            raise ValueError("SIX_BOATS_REQUIRED")
        return {int(k): v for k, v in m.items()}
    courses = keys(record["actual_course_by_boat"])
    strengths = keys(record["strength_by_boat"])
    if any(type(c) is not int for c in courses.values()) or set(courses.values()) != BOATS:
        raise ValueError("ACTUAL_COURSE_PERMUTATION_REQUIRED")
    import math
    if any(type(v) not in (int, float) or not math.isfinite(v) or v <= 0 for v in strengths.values()):
        raise ValueError("INVALID_STRENGTH")
    return {courses[boat]: strengths[boat] for boat in BOATS}


def provenance_digest(record):
    validated_course_strengths(record)
    return hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()
