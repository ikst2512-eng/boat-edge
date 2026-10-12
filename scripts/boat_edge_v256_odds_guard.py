#!/usr/bin/env python3
"""V256 pre-result official-odds fail-closed records and conflict-safe merge.

The odds validator may see a structurally correct 120-combination official
table with fewer than 80 numerical prices (for example, 60). This is NOT
proof that a racer was scratched. Never infer a scratch, fabricate prices,
or reuse a once-valid snapshot after a newer validation failure.

This module never loads outcomes, payout data, combined APIs or formal files.
"""
from __future__ import annotations

from datetime import datetime, timezone
import math
import re
from urllib.parse import parse_qs, urlsplit

RACE_KEY = re.compile(r"20\d{6}-\d{2}-\d{2}\Z")
COMBO = re.compile(r"[1-6]-[1-6]-[1-6]\Z")
SCHEMA = "boat-edge-site-odds-v71"
REJECTED = "REJECTED_NO_BET"
OFFICIAL_SOURCE = "https://www.boatrace.jp/owpc/pc/race/odds3t"
OFFICIAL_LABEL = "BOAT RACE オフィシャルウェブサイト 3連単オッズ"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def official_url_matches(key: str, source_url: str) -> bool:
    if not isinstance(key, str) or not RACE_KEY.fullmatch(key):
        return False
    try:
        u = urlsplit(str(source_url))
        q = parse_qs(u.query, keep_blank_values=True, strict_parsing=True)
        return (
            u.scheme == "https"
            and u.netloc == "www.boatrace.jp"
            and u.path == "/owpc/pc/race/odds3t"
            and not u.fragment
            and set(q) == {"hd", "jcd", "rno"}
            and all(len(q[k]) == 1 for k in q)
            and q["hd"][0] == key[:8]
            and q["jcd"][0].isdigit()
            and int(q["jcd"][0]) == int(key[9:11])
            and q["rno"][0].isdigit()
            and int(q["rno"][0]) == int(key[12:14])
        )
    except (ValueError, TypeError, KeyError):
        return False


def aware_instant(value: object) -> datetime | None:
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo is not None else None
    except (TypeError, ValueError, OverflowError):
        return None


def rejected_document(*, key: str, url: str, deadline: str,
                      checked_at: str, error: str) -> dict:
    """Return a per-race no-bet marker, NEVER an incomplete odds price map."""
    if not official_url_matches(key, url):
        raise ValueError("invalid race-bound official odds URL")
    if aware_instant(checked_at) is None:
        raise ValueError("invalid checked_at")
    observed = re.search(r"valid_odds_too_few=(\d+)", str(error))
    count = int(observed.group(1)) if observed else None
    if count is not None and not 0 <= count < 120:
        count = None
    return {
        "schema_version": SCHEMA,
        "race_key": key,
        "source_url": url,
        "phase": "PRE_RESULT_PURCHASE_ONLY",
        "results_seen": False,
        "scoring": False,
        "odds_validation": REJECTED,
        "no_bet": True,
        "checked_at": checked_at,
        "fetched_at": None,
        "deadline": deadline,
        "trifecta_odds": {},
        "available_count": 0,
        "observed_numeric_count": count,
        "reason": "公式オッズ取得または完全性検証が未確認。買い目にオッズを使用しない",
        "failure": str(error)[:200],
        "scratch_status": "UNVERIFIED",
    }


def is_safe_record(obj: object, key: str) -> bool:
    if not isinstance(obj, dict):
        return False
    if not official_url_matches(key, obj.get("source_url", "")):
        return False
    if (obj.get("race_key") != key or obj.get("schema_version") != SCHEMA
            or obj.get("results_seen") is not False or obj.get("scoring") is not False
            or obj.get("phase") != "PRE_RESULT_PURCHASE_ONLY"):
        return False
    odds = obj.get("trifecta_odds")
    if not isinstance(odds, dict):
        return False
    if obj.get("odds_validation") == REJECTED:
        return (obj.get("no_bet") is True and odds == {}
                and obj.get("available_count") == 0
                and obj.get("fetched_at") is None
                and aware_instant(obj.get("checked_at")) is not None)
    if obj.get("no_bet") is True:
        return False
    if (obj.get("odds_validation") != "VERIFIED"
            or obj.get("source") != OFFICIAL_LABEL
            or obj.get("verified_official_dom_v167") is not True
            or not HEX64.fullmatch(str(obj.get("raw_official_html_sha256", "")))):
        return False
    if not (len(odds) == 120 and obj.get("available_count") == 120
            and obj.get("unavailable_count") == 0
            and obj.get("unavailable_combinations") == []
            and aware_instant(obj.get("fetched_at")) is not None):
        return False
    for combo, price in odds.items():
        if not COMBO.fullmatch(str(combo)) or len(set(combo.split("-"))) != 3:
            return False
        # Official JSON prices are numeric; booleans and strings are not evidence.
        if type(price) not in (int, float):
            return False
        try:
            value = float(price)
        except (TypeError, ValueError, OverflowError):
            return False
        if not math.isfinite(value) or value <= 0:
            return False
    return True


def record_time(doc: dict) -> datetime | None:
    field = "checked_at" if doc.get("odds_validation") == REJECTED else "fetched_at"
    return aware_instant(doc.get(field))


def should_replace(previous: object, candidate: dict, key: str) -> bool:
    """A newer rejection invalidates older odds; older rejections cannot win."""
    if not is_safe_record(candidate, key):
        return False
    now = record_time(candidate)
    if now is None:
        return False
    if not is_safe_record(previous, key):
        return True
    old = record_time(previous)
    return old is None or now > old
