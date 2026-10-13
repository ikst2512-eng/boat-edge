#!/usr/bin/env python3
"""V362: explain start-exhibition COURSE from one labelled official HTML table.

Course is the *row position* beneath the explicit official コース/並び/ST header,
not the boat number or final actual entry. Requires six ordered official rows
and exact same ST values already present on the pre-result race card. This is
an offline parser only, not source authentication or prediction authorization.
"""
from __future__ import annotations

import hashlib
import math
import re
from bs4 import BeautifulSoup

from boat_edge_v314_three_source_evidence import KEY

MODEL = "BOAT_EDGE_V362_OFFICIAL_LABELLED_START_COURSE_PROOF"
SIX = set(range(1, 7))
BOAT_IMAGE = re.compile(r"^/static_extra/pc/images/img_boat2_([1-6])\.png$")


def _st(value):
    if not isinstance(value, str):
        raise ValueError("START_SOURCE_ST_ABSENT")
    value = value.strip()
    if re.fullmatch(r"F\.?\d{1,2}", value, re.IGNORECASE):
        return -int(value.split(".")[-1]) / 100
    if not re.fullmatch(r"[+-]?0?\.\d{1,2}", value):
        raise ValueError("START_SOURCE_ST_INVALID")
    number = float(value)
    if not math.isfinite(number) or abs(number) >= 1:
        raise ValueError("START_SOURCE_ST_INVALID")
    return number


def parse_proven_course_rows(source_raw, race):
    if type(source_raw) is not bytes or not 64 <= len(source_raw) <= 1_000_000:
        raise ValueError("START_SOURCE_HTML_BYTES_REQUIRED")
    if not isinstance(race, dict) or not KEY.fullmatch(str(race.get("race_key"))):
        raise ValueError("START_SOURCE_RACE_KEY_REQUIRED")
    try:
        soup = BeautifulSoup(source_raw, "lxml")
    except Exception as exc:
        raise ValueError("START_SOURCE_HTML_INVALID") from exc
    # Only one table with both the official start-exhibition and course headers
    # is admissible: never infer entries from other tables or row labels alone.
    tables = []
    for table in soup.select("table"):
        ths = [x.get_text(" ", strip=True).replace(" ", "") for x in table.select("thead th")]
        if "スタート展示" in ths:
            tables.append((table, ths))
    if len(tables) != 1:
        raise ValueError("START_SOURCE_LABELLED_TABLE_NOT_UNIQUE")
    table, headers = tables[0]
    if headers != ["スタート展示", "コース", "並び", "ST"]:
        raise ValueError("START_SOURCE_COURSE_HEADERS_INVALID")
    tbody = table.find("tbody", recursive=False)
    rows = tbody.find_all("tr", recursive=False) if tbody is not None else []
    if len(rows) != 6:
        raise ValueError("START_SOURCE_SIX_EXPLICIT_COURSE_ROWS_REQUIRED")
    by_boat = {}
    source_st = {}
    for course, row in enumerate(rows, 1):
        cells = row.find_all("td", recursive=False)
        if len(cells) != 1 or cells[0].get("colspan") != "3":
            raise ValueError("START_SOURCE_COURSE_ROW_SHAPE_INVALID")
        blocks = cells[0].select("div.table1_boatImage1")
        if len(blocks) != 1:
            raise ValueError("START_SOURCE_COURSE_BOAT_BLOCK_INVALID")
        block = blocks[0]
        number = block.select(".table1_boatImage1Number")
        image = block.select("img")
        time = block.select(".table1_boatImage1Time")
        if len(number) != 1 or len(image) != 1 or len(time) != 1:
            raise ValueError("START_SOURCE_ROW_FIELDS_INCOMPLETE")
        raw_boat = number[0].get_text(strip=True)
        m = BOAT_IMAGE.fullmatch(image[0].get("src", ""))
        if raw_boat not in "123456" or len(raw_boat) != 1 or m is None or int(m.group(1)) != int(raw_boat):
            raise ValueError("START_SOURCE_BOAT_ICON_MISMATCH")
        boat = int(raw_boat)
        if boat in by_boat:
            raise ValueError("START_SOURCE_DUPLICATE_BOAT")
        by_boat[boat] = course
        source_st[boat] = _st(time[0].get_text(strip=True))
    if set(by_boat) != SIX:
        raise ValueError("START_SOURCE_SIX_DISTINCT_BOATS_REQUIRED")
    start = (race.get("beforeinfo") or {}).get("start_exhibition")
    if not isinstance(start, list) or len(start) != 6:
        raise ValueError("START_SOURCE_RACE_START_ROWS_REQUIRED")
    existing = {}
    for row in start:
        if not isinstance(row, dict) or type(row.get("lane")) is not int or row["lane"] not in SIX:
            raise ValueError("START_SOURCE_RACE_START_LANE_INVALID")
        boat = row["lane"]
        if boat in existing:
            raise ValueError("START_SOURCE_RACE_DUPLICATE_LANE")
        if not math.isclose(_st(row.get("st")), source_st[boat], rel_tol=0, abs_tol=1e-8):
            raise ValueError("START_SOURCE_ST_VS_RACE_MISMATCH")
        explicit = row.get("course")
        if explicit is not None and (type(explicit) is not int or explicit != by_boat[boat]):
            raise ValueError("START_SOURCE_DECLARED_COURSE_CONFLICT")
        existing[boat] = explicit
    if set(existing) != SIX:
        raise ValueError("START_SOURCE_RACE_LANES_INCOMPLETE")
    return {
        "model_id": MODEL,
        "race_key": race["race_key"],
        "official_table_header": "スタート展示 / コース / 並び / ST",
        "course_by_boat": {str(boat): by_boat[boat] for boat in sorted(SIX)},
        "matched_six_race_card_st_values": True,
        "official_html_sha256": hashlib.sha256(source_raw).hexdigest(),
        "row_order_is_official_labelled_start_exhibition_course": True,
        "source_authenticity_independently_verified": False,
        "actual_entry_independently_verified": False,
        "results_read": False,
        "formal_fresh_read": False,
    }
