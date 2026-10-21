#!/usr/bin/env python3
"""Offline, conservative decoder for *already acquired* Naruto original-exhibition HTML.

No network, permissions bypass, results access or production writes. The caller
must independently establish the exact race identity and predeadline receipt.
"""
from __future__ import annotations

import re
from bs4 import BeautifulSoup
from boat_edge_original_exhibition_coverage import assess_original_exhibition

HEADERS = ("一周", "まわり足", "直線")
ALIASES = {"一周": {"一周", "一周タイム", "1周", "1周タイム", "周回タイム"},
           "まわり足": {"まわり足", "まわり足タイム", "回り足", "回り足タイム"},
           "直線": {"直線", "直線タイム"}}


def _clean(value):
    return re.sub(r"\s+", "", value or "")


def parse_naruto_original_exhibition(html, *, identity_verified=False,
                                      fetched_at=None, deadline=None):
    """Fail closed unless an independently verified same-race HTML table exists.

    A generic page containing measurements is not enough: a caller must prove
    the URL/active race identity and provide an aware predeadline receipt.
    """
    if identity_verified is not True:
        return {"status": "RACE_IDENTITY_UNVERIFIED", "retryable": False}
    if fetched_at is None or deadline is None:
        return {"status": "INVALID_TIMESTAMPS", "retryable": False}
    from datetime import datetime
    if (not isinstance(fetched_at, datetime) or not isinstance(deadline, datetime)
            or fetched_at.tzinfo is None or deadline.tzinfo is None
            or fetched_at.utcoffset() is None or deadline.utcoffset() is None):
        return {"status": "INVALID_TIMESTAMPS", "retryable": False}
    if fetched_at >= deadline:
        return {"status": "STALE_AFTER_DEADLINE", "retryable": False}
    if not isinstance(html, (str, bytes)) or len(html) > 2_000_000:
        return {"status": "PARSE_FAILED", "retryable": False}
    try:
        soup = BeautifulSoup(html, "lxml")
    except (UnicodeError, TypeError, ValueError):
        return {"status": "PARSE_FAILED", "retryable": False}
    candidates = []
    for table in soup.find_all("table"):
        # Reject nested table rows: they belong to a different source block.
        trs = [tr for tr in table.find_all("tr") if tr.find_parent("table") is table]
        for index, header in enumerate(trs):
            names = [_clean(x.get_text(" ", strip=True))
                     for x in header.find_all(["th", "td"], recursive=False)]
            if len(names) < 4 or names[0] not in ("艇", "艇番", "艇番号", "号艇"):
                continue
            indices = {}
            for label in HEADERS:
                matching = [i for i, name in enumerate(names)
                            if name in ALIASES[label]]
                if len(matching) != 1:
                    break
                indices[label] = matching[0]
            if len(indices) != 3 or len(set(indices.values())) != 3:
                continue
            parsed = []
            malformed_rows = False
            for tr in trs[index + 1:]:
                cells = tr.find_all(["th", "td"], recursive=False)
                values = [_clean(c.get_text(" ", strip=True)) for c in cells]
                boat = values[0].replace("号艇", "") if values else ""
                if not re.fullmatch("[1-6]", boat):
                    # Another header after the data block is not another boat.
                    if parsed:
                        break
                    continue
                if len(values) <= max(indices.values()):
                    malformed_rows = True
                    continue
                parsed.append({"boat": int(boat), "lap": values[indices["一周"]],
                               "turn": values[indices["まわり足"]],
                               "straight": values[indices["直線"]]})
            if parsed or malformed_rows:
                # A truncated row must never be silently skipped and then
                # accepted as six complete boats.
                candidates.append(parsed if not malformed_rows else [])
    # Alternative layout: measurement labels down the first column and
    # boats 1..6 across the header. Never infer boat order without labels.
    for table in soup.find_all("table"):
        trs = [tr for tr in table.find_all("tr") if tr.find_parent("table") is table]
        for hi, tr in enumerate(trs):
            cells = tr.find_all(["th", "td"], recursive=False)
            labels = [_clean(c.get_text(" ", strip=True)) for c in cells]
            if len(labels) != 7:
                continue
            boats = [v.replace("号艇", "") for v in labels[1:]]
            if boats != list("123456"):
                continue
            measurement = {}
            for row in trs[hi + 1:]:
                vals = [_clean(c.get_text(" ", strip=True))
                        for c in row.find_all(["th", "td"], recursive=False)]
                if not vals:
                    continue
                name = next((k for k, allowed in ALIASES.items()
                             if vals[0] in allowed), None)
                if name is None:
                    if measurement:
                        break
                    continue
                if name in measurement or len(vals) != 7:
                    measurement = {}
                    break
                measurement[name] = vals[1:]
            if len(measurement) == 3:
                candidates.append([{"boat": i + 1,
                                    "lap": measurement["一周"][i],
                                    "turn": measurement["まわり足"][i],
                                    "straight": measurement["直線"][i]}
                                   for i in range(6)])
    if len(candidates) != 1:
        return {"status": "TABLE_NOT_FOUND_OR_AMBIGUOUS", "retryable": False,
                "tables_detected": len(candidates)}
    if not candidates[0]:
        return {"status": "PARSE_FAILED", "retryable": False,
                "reason": "TRUNCATED_BOAT_ROW"}
    result = assess_original_exhibition(candidates[0], fetched_at=fetched_at,
                                         deadline=deadline)
    result["source_kind"] = "naruto_official_html_unverified_origin"
    result["identity_verified_by_caller"] = True
    result["origin_authenticated_by_parser"] = False
    return result
