#!/usr/bin/env python3
"""Attach independently checked scratch evidence to the SAME official collector push.

SITE PRE_RESULT only. Do not access results, payouts, formal predictions or any
post-deadline source. A missing/unverified HTML byte is never proof of six boats.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit, parse_qs

_REPO = str(Path(__file__).resolve().parents[1])
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)
from scripts.boat_edge_v288_deadline_source_lock import source_write_allowed

JST = timezone(timedelta(hours=9))
KEY = re.compile(r"20\d{6}-(\d{2})-(\d{2})\Z")
FLAGS = re.compile(r"欠場|出走取消|出走取り消し|不出走|欠航|scratched|withdrawn", re.I)
ROW_FLAGS = re.compile(r"欠場|出走取消|取消|不出走|scratched|withdrawn", re.I)
ST = re.compile(r"(?:F|[+-])?0?\.\d{1,2}\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")


def stamp(value):
    try:
        out = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return out.astimezone(timezone.utc) if out.tzinfo else None
    except (TypeError, ValueError, OverflowError):
        return None


def load(path):
    if path.is_symlink():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None


def official(raw, role, key):
    m = KEY.fullmatch(key)
    if not m or raw.get("status") != "ok" or not HEX.fullmatch(str(raw.get("sha256"))):
        return False
    address = urlsplit(str(raw.get("source") or ""))
    if (address.scheme != "https" or address.netloc != "www.boatrace.jp"
            or address.path != "/owpc/pc/race/" + role or address.fragment):
        return False
    try:
        query = parse_qs(address.query, strict_parsing=True)
        return (set(query) == {"hd", "jcd", "rno"}
                and all(len(v) == 1 for v in query.values())
                and query["hd"][0] == key[:8]
                and query["jcd"][0] == m.group(1)
                and int(query["rno"][0]) == int(m.group(2)))
    except (ValueError, KeyError, IndexError):
        return False


def complete_beforeinfo(race):
    before = race.get("beforeinfo") or {}
    expect = set(range(1, 7))
    ex = before.get("racers") or []
    starts = before.get("start_exhibition") or []
    if not isinstance(ex, list) or not isinstance(starts, list) or len(ex) != 6 or len(starts) != 6:
        return False
    exhibit = {r.get("lane") for r in ex if isinstance(r, dict)
               and type(r.get("lane")) is int and r["lane"] in expect
               and type(r.get("exhibition_time")) in (int, float)
               and 6 <= r["exhibition_time"] <= 8.5}
    st = {r.get("lane") for r in starts if isinstance(r, dict)
          and type(r.get("lane")) is int and r["lane"] in expect
          and isinstance(r.get("st"), str) and ST.fullmatch(r["st"])}
    return exhibit == expect and st == expect


def prove(root: Path, key: str, now: datetime):
    """Return (proof, reason); no output for absent or obsolete evidence."""
    if now.tzinfo is None:
        raise ValueError("Aware clock required")
    match = KEY.fullmatch(key)
    if not match or key[:8] != now.astimezone(JST).strftime("%Y%m%d"):
        return None, "not_today"
    path = root / "data/races" / (key + ".json")
    race = load(path)
    if not isinstance(race, dict) or race.get("race_key") != key:
        return None, "race_missing"
    meta = race.get("meta") or {}
    try:
        due = datetime.strptime(key[:8] + str(meta["deadline"]), "%Y%m%d%H:%M").replace(tzinfo=JST)
    except (KeyError, TypeError, ValueError):
        return None, "deadline_missing"
    minutes = (due - now.astimezone(JST)).total_seconds() / 60
    if not (2 <= minutes <= 19):
        return None, "outside_2_19_window"
    if (meta.get("phase") != "PRE_RESULT"
            or any(meta.get(x) is not False for x in ("results_seen", "unlock", "scoring"))
            or str(meta.get("venue_code")).zfill(2) != match.group(1)
            or int(meta.get("race_no") or 0) != int(match.group(2))):
        return None, "unverified_race_identity"
    if not source_write_allowed(root / "data", key, meta["deadline"], now.astimezone(JST)):
        return None, "immutable_or_deadline_locked"
    racers = race.get("racers") or []
    if (len(racers) != 6 or
            {r.get("lane") for r in racers if isinstance(r, dict) and type(r.get("lane")) is int} != set(range(1, 7)) or
            len({str(r.get("registration_no")) for r in racers if isinstance(r, dict)}) != 6):
        return None, "six_racers_unverified"
    audit = race.get("source_audit") or {}
    raw = root / "data/raw" / key[:8]
    evidence = {}
    for role, suffix, age in (("racelist", "race_card", 960), ("beforeinfo", "beforeinfo", 900)):
        row = audit.get(suffix) or {}
        when = stamp(row.get("fetched_at"))
        if (not official(row, role, key) or when is None or
                not 0 <= (now - when).total_seconds() <= age):
            return None, role + "_source_stale"
        f = raw / (match.group(1) + "_" + match.group(2) + "_" + role + ".html")
        if not f.is_file() or f.is_symlink():
            return None, role + "_raw_missing"
        data = f.read_bytes()
        if hashlib.sha256(data).hexdigest() != row["sha256"]:
            return None, role + "_raw_sha_mismatch"
        # Official race pages may be UTF-8 or Japanese Windows-31J. Check
        # both readings so a correctly encoded withdrawal marker is not lost.
        evidence[role] = (data.decode("utf-8", errors="replace") + "\\n"
                          + data.decode("cp932", errors="replace"))
    # Require six real labelled exhibition observations, not an incomplete CSV.
    if not complete_beforeinfo(race):
        return None, "six_boat_exhibition_unverified"
    lanes = []
    for row in racers:
        fields = [row.get(x) for x in ("status", "race_status", "entry_status", "scratch_status", "raw_text")]
        if (any(row.get(x) is True for x in ("scratched", "withdrawn", "absent", "cancelled", "canceled"))
                or any(ROW_FLAGS.search(v) for v in fields if isinstance(v, str))):
            lanes.append(row["lane"])
    flagged = [role for role, data in evidence.items() if FLAGS.search(data)]
    blocked = bool(flagged or lanes)
    return {
        "schema_version": "boat-edge-v182-scratch-evidence-v1",
        "race_key": key,
        "source_date": key[:8],
        "checked_at": now.astimezone(JST).isoformat(),
        "blocked": blocked,
        "reason": " / ".join(x for x in (
            "選手行に欠場・取消の明示情報あり" if lanes else "",
            "取得済み公式HTMLに欠場・取消の表記あり" if flagged else "",
        ) if x) or None,
        "suspect_lanes": lanes,
        "official_raw_flags": flagged,
        "race_card_source_status": "ok",
        "official_beforeinfo_source_status": "ok",
        "official_beforeinfo_six_boat_complete": True,
        "race_card_sha256": audit["race_card"]["sha256"],
        "beforeinfo_sha256": audit["beforeinfo"]["sha256"],
        "limitations": "Source-timestamp-bound presence screening, not a race participation guarantee.",
    }, "blocked" if blocked else "verified"


def run(root: Path, now: datetime):
    root = root.resolve()
    formal = load(root / "data/formal_status.json")
    guard = (formal or {}).get("guards") or {}
    if (any(guard.get(k) is not False for k in ("results_seen", "unlock", "scoring"))
            or guard.get("RESULT_UNLOCK_TOKEN") is not None
            or ((formal or {}).get("formalFirst100") or {}).get("races") != 0):
        raise ValueError("FORMAL_FRESH_LOCK_NOT_CLOSED")
    day = now.astimezone(JST).strftime("%Y%m%d")
    counts = {"in_window_proven": 0, "blocked": 0, "missing_source": 0, "unchanged": 0}
    for race in sorted((root / "data/races").glob(day + "-??-??.json")):
        key = race.stem
        proof, reason = prove(root, key, now)
        if proof is None:
            if reason not in ("outside_2_19_window", "immutable_or_deadline_locked"):
                counts["missing_source"] += 1
            continue
        target = root / "data/site_scratches_v182" / (key + ".json")
        if target.is_symlink():
            raise ValueError("Scratch destination symlink refused")
        prior = load(target)
        prior_time = stamp((prior or {}).get("checked_at"))
        if prior_time and prior_time > now:
            continue
        new = json.dumps(proof, ensure_ascii=False, indent=2) + "\n"
        if target.is_file() and target.read_text(encoding="utf-8") == new:
            counts["unchanged"] += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(new, encoding="utf-8")
        counts["in_window_proven"] += 1
        counts["blocked"] += bool(proof["blocked"])
    return counts


if __name__ == "__main__":
    print("COLLECTOR_SAME_RUN_SCRATCH", json.dumps(
        run(Path("."), datetime.now(JST)), sort_keys=True))
