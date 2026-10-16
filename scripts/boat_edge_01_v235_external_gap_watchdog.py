#!/usr/bin/env python3
"""Opt-in EXTERNAL timer backup for existing V235. No runner is provisioned here.

Call from an independently hosted scheduler every ~2 min. The only live write
is GitHub's workflow_dispatch for the existing V235 workflow on main.
Dry-run is the default. Neither official race data nor formal results are read.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timedelta, timezone
import json
import os
import re
import sys
from urllib import request

REPOSITORY = 'ikst2512-eng/boat-edge'
WORKFLOW = 'V235.yml'
API = f'https://api.github.com/repos/{REPOSITORY}'
JST = timezone(timedelta(hours=9))
ACTIVE = {'queued', 'in_progress', 'waiting', 'pending', 'requested'}
DAY_KEY = re.compile(r'^20\d{6}-\d{2}-\d{2}$')


def api_json(method: str, route: str, token: str, body=None):
    # Routes are internal constants, never arbitrary input URLs or redirects.
    headers = {
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'BOAT-EDGE-01-external-gap-watchdog',
    }
    if token:
        headers['Authorization'] = f'Bearer {token}'
    content = None if body is None else json.dumps(body).encode('utf-8')
    if content is not None:
        headers['Content-Type'] = 'application/json'
    req = request.Request(API + route, data=content, method=method, headers=headers)
    with request.urlopen(req, timeout=15) as response:
        raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('oversized GitHub API response')
        return json.loads(raw) if raw else {}


def official_schedule(envelope):
    if not isinstance(envelope, dict) or envelope.get('encoding') != 'base64':
        raise ValueError('GitHub contents response must be base64')
    raw = base64.b64decode(envelope['content'], validate=False)
    if len(raw) > 2_000_000:
        raise ValueError('oversized race catalog')
    value = json.loads(raw)
    if not isinstance(value, dict) or not isinstance(value.get('venues'), list):
        raise ValueError('invalid race catalog')
    return value


def imminent(schedule: dict, now: datetime) -> list[str]:
    """Find real same-day races in the prewarm interval; NEVER decide freeze eligibility."""
    local = now.astimezone(JST)
    date = local.strftime('%Y-%m-%d')
    day = local.strftime('%Y%m%d')
    if schedule.get('date') != date:
        return []
    keys = set()
    for venue in schedule.get('venues', []):
        for race in venue.get('races', []):
            if not isinstance(race, dict):
                continue
            key, clock = race.get('race_key'), race.get('deadline')
            if not isinstance(key, str) or not DAY_KEY.fullmatch(key) or not key.startswith(day + '-'):
                continue
            if not isinstance(clock, str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', clock):
                continue
            deadline = datetime.strptime(day + ' ' + clock, '%Y%m%d %H:%M').replace(tzinfo=JST)
            remaining = (deadline - local).total_seconds() / 60
            if 4 <= remaining <= 19:
                keys.add(key)
    return sorted(keys)


def decision(schedule: dict, workflow: dict, runs: dict, now: datetime) -> dict:
    """Fail closed if run coverage, identity, or current status is ambiguous."""
    if workflow.get('path') != f'.github/workflows/{WORKFLOW}' or workflow.get('state') != 'active':
        return {'dispatch': False, 'reason': 'WORKFLOW_NOT_ACTIVE_OR_IDENTITY_UNVERIFIED'}
    targets = imminent(schedule, now)
    if not targets:
        return {'dispatch': False, 'reason': 'NO_SAME_DAY_PREWARM_RACE'}
    entries = runs.get('workflow_runs')
    if not isinstance(entries, list) or not entries:
        return {'dispatch': False, 'reason': 'RUN_HISTORY_NOT_VERIFIED', 'targets': targets}
    newest_executed = None
    main_runs_verified = 0
    for run in entries:
        if run.get('head_branch') != 'main':
            continue
        main_runs_verified += 1
        status = run.get('status')
        if status in ACTIVE:
            return {'dispatch': False, 'reason': 'V235_ALREADY_ACTIVE', 'targets': targets}
        if status != 'completed':
            return {'dispatch': False, 'reason': 'V235_UNKNOWN_RUN_STATE', 'targets': targets}
        if run.get('conclusion') == 'skipped':
            continue  # skipped jobs never fetched sources or froze predictions
        if not isinstance(run.get('conclusion'), str):
            return {'dispatch': False, 'reason': 'V235_UNVERIFIED_CONCLUSION', 'targets': targets}
        try:
            created = datetime.fromisoformat(run['created_at'].replace('Z', '+00:00'))
            elapsed = (now - created).total_seconds()
        except (KeyError, TypeError, ValueError, AttributeError):
            return {'dispatch': False, 'reason': 'V235_UNVERIFIED_RUN_TIME', 'targets': targets}
        if elapsed < -90:
            return {'dispatch': False, 'reason': 'CLOCK_AHEAD_OF_GITHUB', 'targets': targets}
        if newest_executed is None or elapsed < newest_executed:
            newest_executed = elapsed
    # Other branches' runs cannot prove the main workflow is idle. The exact
    # V235 history query must include at least one verifiable main run.
    if main_runs_verified == 0:
        return {'dispatch': False, 'reason': 'NO_MAIN_V235_RUN_HISTORY', 'targets': targets}
    if newest_executed is not None and newest_executed < 420:
        return {'dispatch': False, 'reason': 'V235_RECENT_ACTUAL_RUN',
                'seconds_since_run': max(0, int(newest_executed)), 'targets': targets}
    return {'dispatch': True, 'reason': 'MISSED_V235_RUNTIME_WITH_IMMINENT_RACE',
            'targets': targets}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='dispatch existing V235 (default: dry-run)')
    args = parser.parse_args(argv)
    token = os.environ.get('BOAT_EDGE_GITHUB_ACTIONS_TOKEN', '')
    if args.live and not token:
        print(json.dumps({'dispatch': False, 'reason': 'MISSING_ACTIONS_WRITE_TOKEN'}))
        return 2
    # A linked paid cron is not permission to dispatch. The owner must
    # explicitly opt into live operation AFTER dry-run, billing and secret review.
    if args.live and os.environ.get('BOAT_EDGE_EXTERNAL_V235_ENABLED') != 'true':
        print(json.dumps({'dispatch': False, 'reason': 'EXTERNAL_V235_NOT_ENABLED'}))
        return 0
    try:
        schedule = official_schedule(api_json('GET', '/contents/data/today.json?ref=main', token))
        workflow = api_json('GET', f'/actions/workflows/{WORKFLOW}', token)
        runs = api_json('GET', f'/actions/workflows/{WORKFLOW}/runs?branch=main&per_page=100', token)
        status = decision(schedule, workflow, runs, utc_now())
        if not status['dispatch']:
            print(json.dumps(status, sort_keys=True))
            return 0
        if not args.live:
            status.update(dispatch=False, reason='DRY_RUN_WOULD_DISPATCH_V235')
            print(json.dumps(status, sort_keys=True))
            return 0
        # Only existing V235 and main can be dispatched. GitHub's strict V230/V229
        # official source and pre-result first-Git freeze gates are unchanged.
        api_json('POST', f'/actions/workflows/{WORKFLOW}/dispatches', token, {'ref': 'main'})
        status.update(dispatch=True, reason='EXISTING_V235_DISPATCH_SUBMITTED')
        print(json.dumps(status, sort_keys=True))
        return 0
    except Exception as exc:
        # Never echo request headers/tokens or accidentally dispatch on API failure.
        print(json.dumps({'dispatch': False, 'reason': 'GITHUB_API_OR_CATALOG_UNVERIFIED',
                          'error_class': type(exc).__name__}, sort_keys=True))
        return 1


if __name__ == '__main__':
    sys.exit(main())
