#!/usr/bin/env python3
"""Fail-closed original-exhibition coverage assessment (no network or site writes).

For a single already-permitted, source-labelled structured snapshot. A valid
response is not evidence of permission, predeadline receipt, or authenticity.
"""
from __future__ import annotations

import re
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
        if fetched_at.tzinfo is None or deadline.tzinfo is None:
            return {"status": "INVALID_TIMESTAMPS", "retryable": False}
        if fetched_at >= deadline:
            return {"status": "STALE_AFTER_DEADLINE", "retryable": False}
    if rows is None:
        return {"status": "NOT_YET_PUBLISHED", "retryable": True}
    if not isinstance(rows, list) or not rows:
        return {"status": "NOT_YET_PUBLISHED", "retryable": True}
    if len(rows) != 6 or any(not isinstance(r, dict) for r in rows):
        return {"status": "PARTIAL_SIX_BOATS", "retryable": True}
    boats = [r.get("boat") for r in rows]
    if sorted(boats, key=str) != [1, 2, 3, 4, 5, 6] and sorted(map(str, boats)) != list("123456"):
        return {"status": "PARTIAL_SIX_BOATS", "retryable": True}
    absent = {}
    malformed = {}
    for row in rows:
        boat = str(row["boat"])
        missing = [f for f in FIELDS if row.get(f) in MISSING]
        bad = [f for f in FIELDS if f not in missing and
               (not isinstance(row.get(f), (str, int, float)) or
                not NUMBER.fullmatch(str(row[f]).strip()) or
                float(row[f]) <= 0)]
        if missing:
            absent[boat] = missing
        if bad:
            malformed[boat] = bad
    if malformed:
        return {"status": "PARSE_FAILED", "retryable": True, "malformed": malformed}
    if absent:
        category = "OFFICIAL_NOT_MEASURED_OR_NOT_YET_PUBLISHED"
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
        return {"status": "NOT_YET_PUBLISHED_OR_BAD_URL", "retryable": True}
    if code == 429 or isinstance(code, int) and 500 <= code <= 599:
        return {"status": "HTTP_UNAVAILABLE", "retryable": True}
    return {"status": "HTTP_UNAVAILABLE", "retryable": True}
