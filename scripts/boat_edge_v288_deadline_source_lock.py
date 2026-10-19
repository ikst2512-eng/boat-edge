#!/usr/bin/env python3
"""V288: source-only deadline gate for the rolling PRE_RESULT collector.

After the official race deadline, preserving the original source bytes is safer
than repeatedly recrawling historical racers or retrospectively enriching them.
The time gate is also fail-closed when the official deadline is unavailable.
No result, payout, odds, formal Fresh or frozen-snapshot content is ever read.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re
from scripts.boat_edge_v275_frozen_protection import protected_site_snapshot

JST=timezone(timedelta(hours=9))
CLOCK=re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def source_write_allowed(data_root, race_key, deadline, now):
    # V275 immutable prediction is sufficient to forbid mutations even before deadline.
    if protected_site_snapshot(data_root,race_key):
        return False
    if not isinstance(now,datetime) or now.tzinfo is None or now.utcoffset() is None:
        return False
    if not isinstance(deadline,str) or CLOCK.fullmatch(deadline) is None:
        return False
    try:
        scheduled=datetime.strptime(race_key[:8]+deadline,"%Y%m%d%H:%M").replace(tzinfo=JST)
    except ValueError:
        return False
    # No retrospective writes, including at the exact deadline second.
    return now.astimezone(JST)<scheduled


def source_write_allowed_with_prior_deadline(data_root, race_key, deadline, now):
    """Never reopen an existing PRE_RESULT source after its previous deadline.

    The current official schedule may be moved later. Both the newly observed
    deadline and the last saved per-race deadline must still be in the future
    before the collector can replace that race's bytes. An untrusted existing
    file fails closed, rather than treating it as a first-ever collection.
    This does not confer prediction eligibility or change frozen evidence.
    """
    import json

    if not source_write_allowed(data_root, race_key, deadline, now):
        return False
    if not isinstance(race_key, str) or re.fullmatch(
            r"20[0-9]{6}-(?:0[1-9]|1[0-9]|2[0-4])-(?:0[1-9]|1[0-2])",
            race_key) is None:
        return False
    data_root = Path(data_root)
    race_dir = data_root / "races"
    race_path = race_dir / (race_key + ".json")
    if data_root.is_symlink() or race_dir.is_symlink() or race_path.is_symlink():
        return False
    if not race_path.exists():
        return True
    try:
        if not race_path.is_file() or race_path.stat().st_size > 1_000_000:
            return False
        existing = json.loads(race_path.read_text(encoding="utf-8"))
        if not isinstance(existing, dict) or existing.get("race_key") != race_key:
            return False
        meta = existing.get("meta")
        if not isinstance(meta, dict) or meta.get("phase") != "PRE_RESULT":
            return False
        if any(meta.get(flag) is not False for flag in
               ("results_seen", "unlock", "scoring")):
            return False
        if (meta.get("date") != race_key[:4] + "-" + race_key[4:6] + "-" + race_key[6:8]
                or str(meta.get("venue_code")).zfill(2) != race_key[9:11]
                or type(meta.get("race_no")) is not int
                or meta["race_no"] != int(race_key[12:])):
            return False
        return source_write_allowed(data_root, race_key, meta.get("deadline"), now)
    except (OSError, ValueError, TypeError, UnicodeError, OverflowError):
        return False
