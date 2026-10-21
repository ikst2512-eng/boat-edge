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
DASH = {"", "-", "－", "─", "—", "未計測"}


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
    if not isinstance(html, (str, bytes)) or len(html) > 2_000_000:
        return {"status": "PARSE_FAILED", "retryable": False}
    soup = BeautifulSoup(html, "lxml")
    candidates = []
    for table in soup.find_all("table"):
        trs = table.find_all("tr")
        for index, header in enumerate(trs):
            names = [_clean(x.get_text(" ", strip=True))
                     for x in header.find_all(["th", "td"], recursive=False)]
            if len(names) < 4:
                continue
            indices = {}
            for label in HEADERS:
                matching = [i for i, name in enumerate(names)
                            if name == label or name == label + "タイム"]
                if len(matching) != 1:
                    break
                indices[label] = matching[0]
            if len(indices) != 3 or len(set(indices.values())) != 3:
                continue
            parsed = []
            for tr in trs[index + 1:]:
                cells = tr.find_all(["th", "td"], recursive=False)
                values = [_clean(c.get_text(" ", strip=True)) for c in cells]
                if len(values) <= max(indices.values()):
                    continue
                boat = values[0].replace("号艇", "")
                if not re.fullmatch("[1-6]", boat):
                    continue
                parsed.append({"boat": int(boat), "lap": values[indices["一周"]],
                               "turn": values[indices["まわり足"]],
                               "straight": values[indices["直線"]]})
            if parsed:
                candidates.append(parsed)
    if len(candidates) != 1:
        return {"status": "TABLE_NOT_FOUND_OR_AMBIGUOUS", "retryable": False,
                "tables_detected": len(candidates)}
    result = assess_original_exhibition(candidates[0], fetched_at=fetched_at,
                                         deadline=deadline)
    result["source_kind"] = "naruto_official_html_unverified_origin"
    result["identity_verified_by_caller"] = True
    return result
