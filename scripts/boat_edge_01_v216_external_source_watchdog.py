#!/usr/bin/env python3
"""Explicitly opt-in V216 source-ready observer backup, not another collector.

Reuse the already-provisionable V235 external Cron without creating a new paid
service, prediction writer, model, or GitHub schedule. Live dispatches ONLY the
existing V216 workflow on main. Its own pre-result/source/first-Git safeguards
remain unchanged. Disabled by default, including when V235 is enabled.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
from datetime import datetime

from boat_edge_01_v235_external_gap_watchdog import (
    ACTIVE, api_json, official_schedule, imminent, utc_now,
)

WORKFLOW = 'BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml'


def decision(schedule: dict, workflow: dict, runs: dict, now: datetime) -> dict:
    if (not isinstance(workflow, dict)
        or workflow.get('path') != f'.github/workflows/{WORKFLOW}'
        or workflow.get('state') != 'active'):
        return {'dispatch': False, 'reason': 'V216_WORKFLOW_NOT_ACTIVE_OR_UNVERIFIED'}
    targets=imminent(schedule,now)
    if not targets:
        return {'dispatch': False, 'reason': 'NO_SAME_DAY_PREWARM_RACE'}
    entries=runs.get('workflow_runs') if isinstance(runs,dict) else None
    if not isinstance(entries,list) or not entries:
        return {'dispatch': False, 'reason': 'V216_RUN_HISTORY_UNVERIFIED', 'targets':targets}
    main_seen=0
    recent=None
    for run in entries:
        if not isinstance(run,dict):
            return {'dispatch': False, 'reason': 'V216_RUN_METADATA_UNVERIFIED','targets':targets}
        if run.get('head_branch')!='main':
            continue
        main_seen+=1
        state=run.get('status')
        if state in ACTIVE:
            return {'dispatch':False,'reason':'V216_ALREADY_ACTIVE','targets':targets}
        if state!='completed':
            return {'dispatch':False,'reason':'V216_UNKNOWN_RUN_STATE','targets':targets}
        conclusion=run.get('conclusion')
        if conclusion=='skipped':
            continue
        if not isinstance(conclusion,str):
            return {'dispatch':False,'reason':'V216_UNVERIFIED_CONCLUSION','targets':targets}
        try:
            created=datetime.fromisoformat(run['created_at'].replace('Z','+00:00'))
            if created.tzinfo is None:
                raise ValueError('timezone missing')
            age=(now-created).total_seconds()
        except (KeyError,TypeError,ValueError,AttributeError):
            return {'dispatch':False,'reason':'V216_RUN_TIMESTAMP_UNVERIFIED','targets':targets}
        if age < -90:
            return {'dispatch':False,'reason':'V216_GITHUB_CLOCK_AHEAD','targets':targets}
        recent=age if recent is None else min(recent,age)
    if not main_seen:
        return {'dispatch':False,'reason':'V216_NO_MAIN_RUN_HISTORY','targets':targets}
    if recent is not None and recent < 420:
        return {'dispatch':False,'reason':'V216_RECENT_ACTUAL_RUN',
                'seconds_since_run':max(0,int(recent)),'targets':targets}
    return {'dispatch':True,'reason':'MISSED_V216_SOURCE_OBSERVATION',
            'targets':targets}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',action='store_true')
    args=parser.parse_args(argv)
    # V235 consent NEVER authorizes V216 source/paper workflow dispatch.
    if args.live and os.environ.get('BOAT_EDGE_EXTERNAL_V216_ENABLED')!='true':
        print(json.dumps({'dispatch':False,'reason':'EXTERNAL_V216_NOT_ENABLED'}))
        return 0
    token=os.environ.get('BOAT_EDGE_GITHUB_ACTIONS_TOKEN','')
    if args.live and not token:
        print(json.dumps({'dispatch':False,'reason':'V216_MISSING_ACTIONS_WRITE_TOKEN'}))
        return 2
    try:
        schedule=official_schedule(api_json('GET','/contents/data/today.json?ref=main',token))
        workflow=api_json('GET',f'/actions/workflows/{WORKFLOW}',token)
        runs=api_json('GET',f'/actions/workflows/{WORKFLOW}/runs?branch=main&per_page=100',token)
        result=decision(schedule,workflow,runs,utc_now())
        if not result['dispatch']:
            print(json.dumps(result,sort_keys=True))
            return 0
        if not args.live:
            result.update(dispatch=False,reason='DRY_RUN_WOULD_DISPATCH_V216')
        else:
            api_json('POST',f'/actions/workflows/{WORKFLOW}/dispatches',token,{'ref':'main'})
            result.update(dispatch=True,reason='EXISTING_V216_DISPATCH_SUBMITTED')
        print(json.dumps(result,sort_keys=True))
        return 0
    except Exception as exc:
        # Never print bearer tokens or request payloads on a failed request.
        print(json.dumps({'dispatch':False,'reason':'V216_GITHUB_API_UNVERIFIED',
                          'error_class':type(exc).__name__},sort_keys=True))
        return 1


if __name__=='__main__':
    sys.exit(main())
