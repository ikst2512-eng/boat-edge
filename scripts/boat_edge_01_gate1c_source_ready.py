#!/usr/bin/env python3
"""Gate 1C: first prospectively observed source-ready pre-result evidence only.

Called inside the EXISTING V216 pre-result commit, never from a new writer.
No results/formal prediction/payout paths are read. This is a sampled lower
bound, NOT the independently complete eligible-race denominator or 99% proof.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import re

from boat_edge_v220_site_ops import expected_deadline, load, source_status
from boat_edge_v01_collector_scratch import official  # reuse strict role/date/venue/race URI identity

JST=timezone(timedelta(hours=9))
KEY=re.compile(r'^20\d{6}-\d{2}-\d{2}$')
SHA=re.compile(r'^[0-9a-f]{64}$')
SCHEMA='BOAT_EDGE_GATE1C_PROSPECTIVE_SOURCE_READY_V1'
OUT='data/site_ops_v220/gate1c_source_ready'


def safe_source(path:Path):
    # No result lookup or symlink traversal even if the checked-out repository
    # contains a symlink masquerading as an official PRE_RESULT source.
    if path.is_symlink() or not path.is_file() or any(p.is_symlink() for p in path.parents):
        return None,None
    try:
        data=path.read_bytes()
        parsed=json.loads(data)
    except (OSError,UnicodeError,ValueError):
        return None,None
    return (parsed if isinstance(parsed,dict) else None), hashlib.sha256(data).hexdigest()


def valid(root,key,deadline,now):
    if not KEY.fullmatch(key) or not 120<=(deadline-now).total_seconds()<=600:
        return None
    # Check for untrusted symlinks BEFORE calling the existing V220 checker,
    # whose generic JSON helper does not itself reject symlinked source paths.
    snap=root/'data/site_prediction_snapshots'/f'{key}.json'
    if snap.is_symlink():return None
    files={
      'race':root/'data/races'/f'{key}.json',
      'scratch':root/'data/site_scratches_v182'/f'{key}.json',
      'odds':root/'data/site_odds'/f'{key}.json'
    }
    data={};digests={}
    for label,path in files.items():
        obj,hash_=safe_source(path)
        if obj is None or hash_ is None:return None
        data[label]=obj;digests[label]=hash_
    # source_status delegates freshness / exactly 120 odds / PRE_RESULT
    # checks to the already-reviewed V220 implementation. This helper adds
    # stricter positive official completeness checks below.
    blockers=source_status(root,key,now)
    if blockers not in ([],['frozen_prediction_missing_or_invalid']):
        return None
    race=data['race'];scratch=data['scratch'];odds=data['odds']
    meta=race.get('meta') or {}
    audit=race.get('source_audit') or {}
    card=audit.get('race_card') or {}
    before=audit.get('beforeinfo') or {}
    if (not isinstance(meta,dict) or race.get('race_key')!=key
        or meta.get('deadline')!=deadline.astimezone(JST).strftime('%H:%M')
        or meta.get('date')!=deadline.astimezone(JST).date().isoformat()
        or meta.get('venue_code')!=key.split('-')[1]
        or meta.get('race_no')!=int(key.split('-')[2])
        or meta.get('phase')!='PRE_RESULT' or len(race.get('racers') or [])!=6
        or not all(meta.get(g) is False for g in ('results_seen','unlock','scoring'))
        # V01 original official-source validator enforces HTTPS exact host,
        # intended path and unambiguous hd/jcd/rno for THIS race. A valid
        # official page for a different race is NOT source-ready evidence.
        or not official(card,'racelist',key)
        or not official(before,'beforeinfo',key)
        or (before.get('six_boat_coverage') or {}).get('six_boat_complete') is not True):
        return None
    if (scratch.get('official_beforeinfo_six_boat_complete') is not True
        or scratch.get('blocked') is not False
        or scratch.get('suspect_lanes') not in ([],)
        or scratch.get('official_raw_flags') not in ([],)):
        return None
    if (odds.get('results_seen') is not False or odds.get('scoring') is not False
        or odds.get('verified_official_dom_v167') is not True
        or odds.get('available_count')!=120):
        return None
    return {
        'schema':SCHEMA,'scope':'SITE_PRE_RESULT_SOURCE_OBSERVATION_NO_FORMAL_OR_RESULTS',
        'race_key':key,'deadline_jst':meta['deadline'],
        'deadline_at':deadline.isoformat(),'observed_at':now.isoformat(),
        'source_sha256':digests,
        'official_race_card_sha256':card['sha256'],
        'official_beforeinfo_sha256':before['sha256'],
        'official_race_card_fetched_at':card.get('fetched_at'),
        'official_beforeinfo_fetched_at':before.get('fetched_at'),
        'scratch_checked_at':scratch.get('checked_at'),
        'odds_fetched_at':odds.get('fetched_at'),
        'official_odds_combinations':120,
        'six_boat_exhibition_complete':True,
        'first_git_source_commit_independently_proven':False,
        'independently_eligible_denominator_established':False,
        'results_seen':False,'formal_fresh_unlock':False,'scoring':False,
        'snapshot_exists_at_source_observation':
            (root/'data/site_prediction_snapshots'/f'{key}.json').is_file(),
    }


def run(root,now):
    root=root.resolve();now=now.astimezone(timezone.utc)
    formal,_=safe_source(root/'data/formal_status.json')
    guards=(formal or {}).get('guards') or {}
    if (not all(guards.get(g) is False for g in ('results_seen','unlock','scoring'))
        or guards.get('RESULT_UNLOCK_TOKEN') is not None
        or not isinstance((formal or {}).get('formalFirst100'),dict)
        or (formal or {})['formalFirst100'].get('races')!=0):
        raise ValueError('GATE1C_FORMAL_FRESH_FAIL_CLOSED')
    today=now.astimezone(JST).strftime('%Y%m%d')
    plan,_=safe_source(root/'data/today.json')
    if not isinstance(plan,dict) or str(plan.get('date','')).replace('-','')!=today:
        return {'created':[],'ready_in_window':0,'window_races':0,'reason':'schedule_unverified'}
    races={}
    for venue in plan.get('venues') or []:
        for item in venue.get('races') or []:
            if not isinstance(item,dict):continue
            key=item.get('race_key')
            if not isinstance(key,str) or not KEY.fullmatch(key) or not key.startswith(today+'-'):
                continue
            due=expected_deadline(key,item.get('deadline'))
            if due is None:continue
            if key in races and races[key]!=due:
                raise ValueError('GATE1C_DUPLICATE_SCHEDULE_DEADLINE')
            races[key]=due
    made=[];ready=0;window=0
    for key,due in sorted(races.items()):
        if not 120<=(due-now).total_seconds()<=600:continue
        window+=1
        p=root/OUT/f'{key}.json'
        if p.is_symlink() or any(parent.is_symlink() for parent in p.parents):
            raise ValueError('GATE1C_PROOF_PATH_SYMLINK')
        if p.exists():
            # Even a malformed existing receipt must not be overwritten.
            continue
        proof=valid(root,key,due,now)
        if proof is None:continue
        ready+=1
        p.parent.mkdir(parents=True,exist_ok=True)
        if p.parent.is_symlink():
            raise ValueError('GATE1C_PROOF_DIR_SYMLINK')
        try:
            with p.open('x',encoding='utf8') as out:
                json.dump(proof,out,ensure_ascii=False,sort_keys=True,indent=2)
                out.write('\n')
        except FileExistsError:
            continue
        made.append(key)
    return {'created':made,'ready_in_window':ready,'window_races':window,
            'not_an_eligibility_denominator':True}


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--root',default='.')
    ap.add_argument('--now')
    args=ap.parse_args()
    at=datetime.fromisoformat(args.now.replace('Z','+00:00')) if args.now else datetime.now(timezone.utc)
    if at.tzinfo is None:raise ValueError('GATE1C_AWARE_NOW_REQUIRED')
    print('GATE1C_PROSPECTIVE_SOURCE_READY_OBSERVED_ONLY',json.dumps(
        run(Path(args.root),at),sort_keys=True,ensure_ascii=False))

if __name__=='__main__':main()
