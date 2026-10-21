#!/usr/bin/env python3
"""Fail-closed original-exhibition coverage assessment (no network or site writes).

For a single already-permitted, source-labelled structured snapshot. A valid
response is not evidence of permission, predeadline receipt, or authenticity.
"""
from __future__ import annotations

import re
import math
from datetime import datetime

FIELDS = ("lap", "turn", "straight")
MISSING = (None, "", "-", "－", "─", "—", "未計測")
NUMBER = re.compile(r"^(?:[0-9]+)(?:\.[0-9]+)?$")


def assess_original_exhibition(rows, *, fetched_at=None, deadline=None):
    """Return category and per-field absence without inventing zero values.

    rows: six dictionaries with boat (1..6), lap, turn and straight values.
    The three measurements are not interchangeable with exhibition time.
    """
    if fetched_at is not None or deadline is not None:
        if not isinstance(fetched_at, datetime) or not isinstance(deadline, datetime):
            return {"status": "INVALID_TIMESTAMPS", "retryable": False}
        if (fetched_at.tzinfo is None or deadline.tzinfo is None or
                fetched_at.utcoffset() is None or deadline.utcoffset() is None):
            return {"status": "INVALID_TIMESTAMPS", "retryable": False}
        if fetched_at >= deadline:
            return {"status": "STALE_AFTER_DEADLINE", "retryable": False}
    if rows is None:
        return {"status": "NOT_YET_PUBLISHED", "retryable": True}
    if rows is not None and not isinstance(rows, list):
        return {"status": "PARSE_FAILED", "retryable": False}
    if not rows:
        return {"status": "NOT_YET_PUBLISHED", "retryable": True}
    if len(rows) != 6 or any(not isinstance(r, dict) for r in rows):
        return {"status": "PARTIAL_SIX_BOATS", "retryable": True}
    boats = [r.get("boat") for r in rows]
    if any(type(b) not in (int, str) for b in boats) or sorted(map(str, boats)) != list("123456"):
        return {"status": "PARTIAL_SIX_BOATS", "retryable": True}
    absent = {}
    malformed = {}
    for row in rows:
        boat = str(row["boat"])
        missing = [f for f in FIELDS if row.get(f) is None or
                   (isinstance(row.get(f), str) and row[f].strip() in MISSING)]
        bad = [f for f in FIELDS if f not in missing and
               (type(row.get(f)) not in (str, int, float) or
                len(str(row[f]).strip()) > MAX_VALUE_CHARS or
                not NUMBER.fullmatch(str(row[f]).strip()) or
                not math.isfinite(float(row[f])) or float(row[f]) <= 0)]
        if missing:
            absent[boat] = missing
        if bad:
            malformed[boat] = bad
    if malformed:
        return {"status": "PARSE_FAILED", "retryable": True, "malformed": malformed}
    if absent:
        category = "NOT_MEASURED_OR_NOT_YET_PUBLISHED"
        return {"status": category, "retryable": True, "missing": absent,
                "note": "Source metadata required to distinguish official omission from delay"}
    return {"status": "COMPLETE_SIX_BOATS", "retryable": False,
            "boats": {str(r["boat"]): {f: float(r[f]) for f in FIELDS} for r in rows}}


def classify_fetch_failure(error):
    """Classify transport failures separately from the publication state."""
    code = getattr(error, "code", None)
    if code in (401, 403):
        return {"status": "ACCESS_RESTRICTED", "retryable": False}
    if code == 404:
        return {"status": "NOT_YET_PUBLISHED_OR_BAD_URL", "retryable": False}
    if code == 429:
        return {"status": "RATE_LIMITED", "retryable": False}
    if isinstance(code, int) and 500 <= code <= 599:
        return {"status": "HTTP_UNAVAILABLE", "retryable": True}
    return {"status": "HTTP_UNAVAILABLE", "retryable": True}


def retry_delay_seconds(attempt, status, *, remaining_seconds):
    """Bounded pure backoff decision; callers must recheck race deadline.

    Never retry access restrictions or late receipts. No network requests here.
    """
    retryable = {"NOT_YET_PUBLISHED", "PARTIAL_SIX_BOATS",
                 "HTTP_UNAVAILABLE", "PARSE_FAILED",
                 "NOT_MEASURED_OR_NOT_YET_PUBLISHED"}
    if type(attempt) is not int or attempt < 0:
        raise ValueError("INVALID_ATTEMPT")
    if type(remaining_seconds) not in (int, float) or not math.isfinite(remaining_seconds):
        raise ValueError("INVALID_REMAINING_SECONDS")
    if status not in retryable or remaining_seconds <= 0:
        return None
    delay = min(60, 2 ** min(attempt, 6) * 3)
    return delay if delay < remaining_seconds else None



def assess_official_beforeinfo(parsed):
    """Bridge V230 official beforeinfo to source-status without conflating exhibits.

    Standard exhibition-time and ST tables are NOT original exhibition
    (one-lap/turn/straight). This function never upgrades their evidence.
    """
    if not isinstance(parsed, dict):
        return {"official_beforeinfo_status": "PARSE_FAILED",
                "original_exhibition_status": "NOT_VERIFIED"}
    racers = parsed.get("racers")
    starts = parsed.get("start_exhibition")
    if not isinstance(racers, list) or not isinstance(starts, list):
        return {"official_beforeinfo_status": "PARSE_FAILED",
                "original_exhibition_status": "NOT_VERIFIED"}
    from boat_edge_v230_fast_lane import beforeinfo_coverage
    coverage = beforeinfo_coverage(parsed)
    return {"official_beforeinfo_status": (
                "COMPLETE" if coverage["six_boat_complete"] else "PARTIAL_SIX_BOATS"),
            "official_beforeinfo_coverage": coverage,
            "original_exhibition_status": "NOT_VERIFIED"}
