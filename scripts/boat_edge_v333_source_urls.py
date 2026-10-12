#!/usr/bin/env python3
"""V333 explicit, inspectable race-page URL templates for public source capture.

These construct URL *candidates*, not proof of response identity, data access,
original exhibition values or permission for reuse. Network access is only
performed on a separate --capture opt-in in V332; all errors fail closed.
"""
from __future__ import annotations

from datetime import datetime

from boat_edge_v314_three_source_evidence import KEY
from boat_edge_v315_source_capture import check_target

VENUES = {
    "01": "kiryu", "02": "toda", "03": "edogawa",
    "04": "heiwajima", "05": "tamagawa", "06": "hamanako",
    "07": "gamagori", "08": "tokoname", "09": "tsu",
    "10": "mikuni", "11": "biwako", "12": "suminoe",
    "13": "amagasaki", "14": "naruto", "15": "marugame",
    "16": "kojima", "17": "miyajima", "18": "tokuyama",
    "19": "shimonoseki", "20": "wakamatsu", "21": "ashiya",
    "22": "fukuoka", "23": "karatsu", "24": "omura",
}


def suggested_source_urls(race_key):
    if not isinstance(race_key, str) or KEY.fullmatch(race_key) is None:
        raise ValueError("INVALID_RACE_KEY")
    if race_key.startswith("20261001-"):
        raise ValueError("FORMAL_FRESH_TARGET_EXCLUDED")
    date, code, race = race_key.split("-")
    try:
        day = datetime.strptime(date, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("INVALID_RACE_DATE") from exc
    if code not in VENUES:
        raise ValueError("UNKNOWN_VENUE")
    number = int(race)
    urls = {
        "official": (
            f"https://www.boatrace.jp/owpc/pc/race/beforeinfo"
            f"?hd={date}&jcd={code}&rno={number}"
        ),
        "boaters": (
            f"https://boaters-boatrace.com/race/{VENUES[code]}/"
            f"{day}/{number}R/last-minute?last-minute-content=original-tenji"
        ),
        "kyoteibiyori": (
            f"https://kyoteibiyori.com/race_shusso.php"
            f"?hiduke={date}&place_no={int(code)}&race_no={number}"
        ),
    }
    for provider, url in urls.items():
        check_target(provider, url, race_key)
    return urls
