#!/usr/bin/env python3
"""V370: official racelist SIX BOAT-LANE to racer registration proof.

Never infer identity from the unordered set of racer numbers. Require
one labelled official table and, for each boat 1..6, an explicit matching
is-boatColorN first cell plus a linked registered racer profile/photo.
This parses original HTML bytes but does not assert source authenticity.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit, parse_qs

from bs4 import BeautifulSoup

MODEL = "BOAT_EDGE_V370_OFFICIAL_RACELIST_SIX_LANE_REGISTRATION_PROOF"
LANES = set(range(1, 7))
PROFILE = re.compile(r"^/owpc/pc/data/racersearch/profile$")
PHOTO = re.compile(r"^/racerphoto/(\d{4})\.jpg$")


def proof_six_lane_registrations(racelist_raw, racers):
    if type(racelist_raw) is not bytes or not 64 <= len(racelist_raw) <= 2_097_152:
        raise ValueError("V370_OFFICIAL_RACELIST_BYTES_REQUIRED")
    if not isinstance(racers, list) or len(racers) != 6:
        raise ValueError("V370_SIX_RACE_CARD_LANES_REQUIRED")
    expected = {}
    for row in racers:
        if not isinstance(row, dict):
            raise ValueError("V370_INVALID_RACE_CARD_ROW")
        lane, reg = row.get("lane"), row.get("registration_no")
        if (type(lane) is not int or lane not in LANES or
                not isinstance(reg, str) or not re.fullmatch(r"\d{4}", reg)
                or lane in expected):
            raise ValueError("V370_BAD_OR_DUPLICATE_RACE_CARD_LANE")
        expected[lane] = reg
    if set(expected) != LANES or len(set(expected.values())) != 6:
        raise ValueError("V370_SIX_DISTINCT_EXPECTED_RACERS_REQUIRED")
    soup = BeautifulSoup(racelist_raw, "lxml")
    # Actual official race list has one table containing both labels:
    # ボートレーサー and 登録番号/級別. Other per-day history tables are
    # not registration evidence and must never be admitted.
    tables = [
        table for table in soup.select("table")
        if any("ボートレーサー" in th.get_text(" ", strip=True)
               for th in table.select("thead th"))
        and any("登録番号/級別" in th.get_text(" ", strip=True)
                for th in table.select("thead th"))
    ]
    if len(tables) != 1:
        raise ValueError("V370_OFFICIAL_RACER_TABLE_NOT_UNIQUE")
    observed = {}
    for tbody in tables[0].find_all("tbody", recursive=False):
        first = tbody.find("tr", recursive=False)
        if first is None:
            continue
        cells = first.find_all("td", recursive=False)
        if not cells:
            continue
        boat_css = [c for c in cells[0].get("class", [])
                    if re.fullmatch(r"is-boatColor[1-6]", c)]
        if not boat_css:
            continue
        if len(boat_css) != 1:
            raise ValueError("V370_AMBIGUOUS_BOAT_COLOR")
        lane = int(boat_css[0][-1])
        boat_text = cells[0].get_text(" ", strip=True)
        if boat_text not in (str(lane), "１２３４５６"[lane - 1]):
            raise ValueError("V370_BOAT_COLOR_LABEL_MISMATCH")
        if lane in observed:
            raise ValueError("V370_DUPLICATE_BOAT_COLOR_LANE")
        profile_links = []
        for link in first.select("a[href]"):
            url = urlsplit(link.get("href", ""))
            if url.path == PROFILE.pattern.strip("^$"):
                # The DOM uses a fixed /owpc/pc/data/racersearch/profile path.
                params = parse_qs(url.query, keep_blank_values=True)
                if (url.scheme or url.netloc or url.fragment
                        or set(params) != {"toban"} or len(params["toban"]) != 1
                        or not re.fullmatch(r"\d{4}", params["toban"][0])):
                    raise ValueError("V370_BAD_RACER_PROFILE_LINK")
                profile_links.append(params["toban"][0])
        if not profile_links or len(set(profile_links)) != 1:
            raise ValueError("V370_PROFILE_LINKS_NOT_CONSISTENT")
        reg = profile_links[0]
        photos = []
        for img in first.select("img[src]"):
            m = PHOTO.fullmatch(img.get("src", ""))
            if m:
                photos.append(m.group(1))
        if photos != [reg]:
            raise ValueError("V370_RACER_PHOTO_PROFILE_ID_MISMATCH")
        if len(cells) < 3:
            raise ValueError("V370_RACER_REGISTERED_NUMBER_CELL_MISSING")
        # Registration is printed in the third direct cell, not a later
        # old-race-history cell or an arbitrary 4-digit number elsewhere.
        third = cells[2].get_text(" ", strip=True)
        if re.search(r"(?<!\d)" + reg + r"\s*/", third) is None:
            raise ValueError("V370_PRINTED_REGISTERED_NUMBER_MISMATCH")
        observed[lane] = reg
    if set(observed) != LANES or len(set(observed.values())) != 6:
        raise ValueError("V370_SIX_EXPLICIT_RACER_LANE_ROWS_REQUIRED")
    if observed != expected:
        raise ValueError("V370_OFFICIAL_BOAT_LANE_REGISTRATION_MISMATCH")
    return {
        "model_id": MODEL,
        "lane_to_registration": {str(k): observed[k] for k in sorted(LANES)},
        "six_lane_racer_photo_printed_registration_matched": True,
        "local_official_html_structure_verified": True,
        "source_authenticity_independently_verified": False,
        "results_read": False,
        "formal_fresh_read": False,
    }
