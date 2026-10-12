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
