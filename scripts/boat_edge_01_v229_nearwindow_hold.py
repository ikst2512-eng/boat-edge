#!/usr/bin/env python3
"""Read-only V229 bounded prewindow sleep planner; NOT a freeze-eligibility oracle.

The existing V229 writer independently enforces 2-10m deadline, original
official 6-boat HTML, complete verified official 120 odds, scratch and first Git.
This code can only delay that writer by <=130s when all coarse live inputs
are already present immediately before the window. The strict freeze gate
always rechecks the source and 2-10m window AFTER the delay. No results/formal/payout reads.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import re
import sys

from boat_edge_v220_site_ops import JST, expected_deadline, load, source_status

MAX_HOLD_SECONDS = 130
PREWINDOW_END = 720  # from 12m00 to 10m, then stop at 9m50
EARLY_TARGET_SECONDS = 590
_KEY = re.compile(r'^20\d{6}-\d{2}-\d{2}$')


def _no_symlink(root: Path, relative: str) -> bool:
    path = root / relative
    # Do not follow an attacker-supplied link into results/formal files.
    if root.is_symlink() or path.is_symlink():
        return False
    parent = path.parent
    while parent != root and parent != parent.parent:
        if parent.is_symlink():
            return False
        parent = parent.parent
    return True


def plan(root: Path, now: datetime) -> dict:
    """No network, writes or arbitrary paths; false negatives are safe."""
    out = {'wait_seconds': 0, 'race_key': None, 'reason': 'NO_VERIFIED_NEAR_WINDOW'}
    now = now.astimezone(timezone.utc)
    day = now.astimezone(JST).strftime('%Y%m%d')
    if not _no_symlink(root, 'data/today.json'):
        out['reason'] = 'CATALOG_PATH_UNSAFE'
        return out
    catalog = load(root/'data/today.json')
    if not isinstance(catalog,dict) or str(catalog.get('date','')).replace('-','') != day or not isinstance(catalog.get('venues'),list):
        out['reason'] = 'CATALOG_INVALID_OR_NOT_TODAY'
        return out
    nearest = []
    open_unsaved = False
    seen = set()
    for venue in catalog['venues']:
        if not isinstance(venue,dict) or not isinstance(venue.get('races'),list):
            out['reason'] = 'CATALOG_STRUCTURE_UNVERIFIED'
            return out
        for race in venue['races']:
            if not isinstance(race,dict):
                out['reason'] = 'CATALOG_RACE_UNVERIFIED'
                return out
            key = race.get('race_key')
            if not isinstance(key,str) or _KEY.fullmatch(key) is None or not key.startswith(day+'-') or key in seen:
                out['reason'] = 'CATALOG_RACE_ID_OR_DUPLICATE'
                return out
            seen.add(key)
            due = expected_deadline(key,race.get('deadline'))
            if due is None:
                out['reason'] = 'CATALOG_DEADLINE_UNVERIFIED'
                return out
            left = (due-now).total_seconds()
            snap_rel=f'data/site_prediction_snapshots/{key}.json'
            if not _no_symlink(root,snap_rel):
                out['reason'] = 'SNAPSHOT_PATH_UNSAFE'
                return out
            if (root/snap_rel).exists():
                continue
            if 120 <= left <= 600:
                open_unsaved = True
                continue
            if not 600 < left <= PREWINDOW_END:
                continue
            for kind in ('races','site_odds','site_scratches_v182'):
                if not _no_symlink(root,f'data/{kind}/{key}.json'):
                    out['reason'] = 'SOURCE_PATH_UNSAFE'
                    return out
            # Coarse source check is a *wait-only* prerequisite, not V229
            # permission. V229's own immutable official-source checks remain.
            issues = source_status(root,key,now)
            if issues == ['frozen_prediction_missing_or_invalid']:
                nearest.append((left,key))
    if open_unsaved:
        out['reason'] = 'UNSAVED_RACE_ALREADY_IN_STRICT_WINDOW'
        return out
    if not nearest:
        return out
    seconds,key=min(nearest)
    hold = max(0,min(MAX_HOLD_SECONDS,math.ceil(seconds-EARLY_TARGET_SECONDS)))
    if hold:
        out.update(wait_seconds=hold,race_key=key,reason='COARSE_SOURCE_READY_PREWINDOW_WAIT_ONLY')
    return out


def main() -> int:
    # No user-supplied arbitrary file path, no caller-controlled time.
    status=plan(Path('.'),datetime.now(timezone.utc))
    print('V229_NEARWINDOW_WAIT_PLAN '+json.dumps(status,sort_keys=True))
    if status['wait_seconds']:
        import time
        time.sleep(status['wait_seconds'])
        print('V229_NEARWINDOW_HOLD_ELAPSED_RECHECK_BY_STRICT_V229')
    return 0


if __name__=='__main__':
    sys.exit(main())
