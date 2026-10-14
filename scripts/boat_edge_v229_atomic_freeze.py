#!/usr/bin/env python3
"""Site-reference ONLY: source-gated first freeze + same-run immutable audit.

No historical reconstruction, no settlement, no official result or payout reads,
no formal Fresh unlock. An evidence row is created only for a newly created
prospective snapshot in this process. Unverifiable input aborts the commit.
"""
from __future__ import annotations
import argparse
import ast
from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys

from boat_edge_v228_freeze_only import build_frozen_source, check_formal_closed

UTC=timezone.utc
JST=timezone(timedelta(hours=9))
KEY=re.compile(r'^20\d{6}-\d{2}-\d{2}$')
COMBOS={f'{a}-{b}-{c}' for a in range(1,7) for b in range(1,7)
        for c in range(1,7) if len({a,b,c})==3}
ANCHOR='    scratches=read_json(ROOT/"data/site_scratches_v182"/f"{key}.json") or {}\n'
WINDOW='    if not (0<mins<=10):\n        continue\n'
FRESH_CARD='''    # V229_FRESH_CARD_BEFORE_FREEZE: an old racelist cannot certify live participation.
    _v229_card=(race.get('source_audit') or {}).get('race_card') or {}
    try:
        _v229_card_at=datetime.fromisoformat(str(_v229_card.get('fetched_at')))
        if (_v229_card.get('status')!='ok' or _v229_card_at.tzinfo is None
                or not 0 <= (NOW-_v229_card_at).total_seconds() <= 16*60):
            continue
    except (ValueError,TypeError,OverflowError):
        continue
'''
WINDOW_REPLACEMENT='''    # V229_MINIMUM_DECISION_LEAD: no freezes <2 minutes before the deadline.
    if not (2<=mins<=10):
        continue
'''
FORBIDDEN={'site_results','results','result','payout','payouts',
           'formal_predictions','formal'}


def read_obj(path:Path):
    try:return json.loads(path.read_text(encoding='utf8'))
    except (OSError,UnicodeError,ValueError):return None


def instant(val):
    try:
        v=datetime.fromisoformat(str(val).replace('Z','+00:00'))
        return v.astimezone(UTC) if v.tzinfo else None
    except (TypeError,ValueError,OverflowError):return None


def age(newer,older,seconds):
    return newer is not None and older is not None and 0 <= (newer-older).total_seconds() <= seconds


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runner_source(source):
    """Keep V228's SHA-pinned result-free source; add only two pre-result guards."""
    if source.count(ANCHOR)!=1 or source.count(WINDOW)!=1:
        raise AssertionError('V229_V228_ANCHOR_DRIFT_FAIL_CLOSED')
    code=source.replace(ANCHOR,ANCHOR+FRESH_CARD).replace(WINDOW,WINDOW_REPLACEMENT)
    if any(x not in code for x in ('V228_NO_RESULT_READ','V228_SITE_REFERENCE_ONLY',
                                   'V226_IMMUTABLE_ORIGINAL_SNAPSHOT',
                                   'V229_FRESH_CARD_BEFORE_FREEZE','V229_MINIMUM_DECISION_LEAD')):
        raise AssertionError('V229_PROVENANCE_GUARDS_MISSING')
    ast.parse(code)
    return code


def validate(root:Path,key:str,now:datetime):
    """Validate evidence from the current checkout, not later results or inferred files."""
    if not KEY.fullmatch(key):raise AssertionError('V229_RACE_KEY_INVALID')
    sp=root/'data/site_prediction_snapshots'/f'{key}.json'
    doc=read_obj(sp)
    if not isinstance(doc,dict) or doc.get('race_key')!=key:
        raise AssertionError('V229_SNAPSHOT_INVALID')
    if doc.get('schema_version')!='boat-edge-server-site-final-v123' or doc.get('snapshot_window')!='FINAL_15M':
        raise AssertionError('V229_SNAPSHOT_SCHEMA_INVALID')
    if doc.get('prediction_kind')!='SITE_REFERENCE_V122':
        raise AssertionError('V229_NOT_SITE_REFERENCE')
    if any((doc.get('guards') or {}).get(k) is not False for k in ('results_seen','unlock','scoring')):
        raise AssertionError('V229_RESULT_GUARD_INVALID')
    saved=instant(doc.get('saved_at'))
    first=instant(doc.get('first_saved_at'))
    clock=doc.get('deadline')
    try:
        if not re.fullmatch(r'\d{2}:\d{2}',str(clock)):raise ValueError('bad clock')
        due=datetime.strptime(key[:8]+clock,'%Y%m%d%H:%M').replace(tzinfo=JST).astimezone(UTC)
    except (TypeError,ValueError):raise AssertionError('V229_DEADLINE_INVALID')
    if not age(now,saved,120) or not age(saved,first,10) or not (120 <= (due-saved).total_seconds() <= 600):
        raise AssertionError('V229_SOURCE_WINDOW_INVALID')
    race_path=root/'data/races'/f'{key}.json'
    race=read_obj(race_path) or {}
    m=race.get('meta') or {}
    if m.get('phase')!='PRE_RESULT' or any(m.get(k) is not False for k in ('results_seen','unlock','scoring')):
        raise AssertionError('V229_RACE_PHASE_INVALID')
    if len(race.get('racers') or [])!=6:
        raise AssertionError('V229_SIX_BOATS_UNVERIFIED')
    if digest(race_path)!=doc.get('race_sha256'):
        raise AssertionError('V229_SNAPSHOT_RACE_SHA_MISMATCH')
    au=race.get('source_audit') or {}
    for field,secs in [('race_card',960),('beforeinfo',900)]:
        row=au.get(field) or {}
        if row.get('status')!='ok' or not age(saved,instant(row.get('fetched_at')),secs):
            raise AssertionError('V229_'+field.upper()+'_NOT_VERIFIED_AT_SAVE')
    scratch_path=root/'data/site_scratches_v182'/f'{key}.json'
    scratch=read_obj(scratch_path) or {}
    if (scratch.get('race_key')!=key or scratch.get('blocked') is not False
            or scratch.get('race_card_source_status')!='ok'
            or scratch.get('official_beforeinfo_source_status')!='ok'
            or not age(saved,instant(scratch.get('checked_at')),900)):
        raise AssertionError('V229_SCRATCH_NOT_VERIFIED_AT_SAVE')
    if doc.get('stake_plan_version')!='V141-10000-PROSPECTIVE':
        raise AssertionError('V229_STAKE_PLAN_UNVERIFIED')
    modes=doc.get('modes') or {}
    for name in ('hit','balance','hole','narrow'):
        tickets=(modes.get(name) or {}).get('tickets') or []
        if not tickets or len({x.get('combo') for x in tickets})!=len(tickets):
            raise AssertionError('V229_MISSING_UNIQUE_TICKETS_'+name)
        if any(x.get('combo') not in COMBOS or not isinstance(x.get('stake_yen'),int)
               or x['stake_yen']<0 or x['stake_yen']%100 for x in tickets):
            raise AssertionError('V229_INVALID_TICKET_'+name)
        if sum(x['stake_yen'] for x in tickets)!=10000:
            raise AssertionError('V229_STAKE_NOT_10000_'+name)
    odds_sha=doc.get('odds_sha256')
    if not re.fullmatch(r'[0-9a-f]{64}',str(odds_sha)):
        raise AssertionError('V229_ODDS_SHA_MISSING')
    archived=root/'data/site_prediction_snapshots/odds_v214'/f'{key}-{odds_sha}.json'
    if not archived.is_file() or digest(archived)!=odds_sha:
        raise AssertionError('V229_ODDS_SIDECAR_NOT_IMMUTABLE')
    odds=read_obj(archived) or {}
    rows=odds.get('trifecta_odds') or {}
    if (odds.get('race_key')!=key or odds.get('phase')!='PRE_RESULT_PURCHASE_ONLY'
            or not age(saved,instant(odds.get('fetched_at')),900)
            or set(rows)!=COMBOS or any(not isinstance(v,(int,float)) or isinstance(v,bool)
                                        or not math.isfinite(v) or v<=0 for v in rows.values())):
        raise AssertionError('V229_ODDS_120_NOT_VALID_AT_SAVE')
    # 02/01 prospective user-selected best observed Top10. A new SITE mode
    # is only source-audited when its entire ten-ticket permutation matches
    # the predeclared V254 construction from the exact frozen hit/hole modes.
    # Earlier four-mode snapshots retain their untouched original contract.
    selected=doc.get('default_display_mode')
    tail_present='tail' in modes
    if selected not in (None,'tail') or tail_present!=(selected=='tail'):
        raise AssertionError('V229_PROVISIONAL_TAIL_MARKER_INVALID')
    if tail_present:
        if (set(modes)!={'hit','balance','hole','narrow','tail'} or
            doc.get('mode_policy')!='PROVISIONAL_V254_THIRD_TAIL10_FIXED_TOP7' or
            doc.get('adopted_ticket_policy')!='PROVISIONAL_V254_THIRD_TAIL10_FROM_PREDECLARED_FROZEN_MODES' or
            doc.get('statistical_significance_claim') is not False or
            doc.get('formal_current_model_changed') is not False):
            raise AssertionError('V229_PROVISIONAL_TAIL_POLICY_UNVERIFIED')
        from boat_edge_v254_third_tail import third_tail_candidate
        source_hit=[x.get('combo') for x in modes['hit']['tickets']]
        source_hole=[x.get('combo') for x in modes['hole']['tickets']]
        expected=third_tail_candidate(source_hit,source_hole)
        tail=(modes.get('tail') or {}).get('tickets')
        if (expected is None or not isinstance(tail,list) or
            len(tail)!=10 or [x.get('combo') for x in tail]!=expected):
            raise AssertionError('V229_PROVISIONAL_TAIL_RANK_MISMATCH')
        total=0
        for t in tail:
            combo=t.get('combo');stake=t.get('stake_yen');p=t.get('p');price=t.get('odds')
            if (combo not in COMBOS or type(stake) is not int or stake<100 or
                stake%100 or type(p) not in (float,int) or
                isinstance(p,bool) or not math.isfinite(p) or not 0<p<100 or
                type(price) not in (float,int) or isinstance(price,bool) or
                not math.isfinite(price) or abs(price-rows[combo])>.05):
                raise AssertionError('V229_PROVISIONAL_TAIL_TICKET_UNVERIFIED')
            total+=stake
        if total!=10000:
            raise AssertionError('V229_PROVISIONAL_TAIL_STAKE_NOT_10000')
    return {'schema':'BOAT_EDGE_V229_ATOMIC_PRE_RESULT_SOURCE_EVIDENCE_V1',
            'scope':'SITE_REFERENCE_ONLY_NO_FORMAL_OR_RESULT_ACCESS',
            'race_key':key,'snapshot_sha256':digest(sp),'snapshot_saved_at':saved.isoformat(),
            'evidence_captured_at':now.isoformat(),
            'race_sha256':digest(race_path),
            'scratch_sha256':digest(scratch_path),
            'official_race_card_fetched_at':instant(au['race_card']['fetched_at']).isoformat(),
            'official_beforeinfo_fetched_at':instant(au['beforeinfo']['fetched_at']).isoformat(),
            'scratch_checked_at':instant(scratch['checked_at']).isoformat(),
            'odds_sha256':odds_sha,'odds_fetched_at':instant(odds['fetched_at']).isoformat(),
            'odds_combinations':120,'stake_yen_per_mode':10000,
            'new_snapshot_created_this_run':True,
            'results_seen':False,'formal_fresh_unlock':False,'scoring':False,
            'model_accuracy_proven':False}


def write_once(path:Path,object_:dict):
    if path.exists():raise AssertionError('V229_EVIDENCE_FILE_ALREADY_EXISTS_DO_NOT_OVERWRITE')
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(object_,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf8')


def run(root:Path):
    root=root.resolve()
    check_formal_closed(root)
    source=(root/'scripts/site_final_history_v133.py').read_text(encoding='utf8')
    code=runner_source(build_frozen_source(source))
    today=datetime.now(JST).strftime('%Y%m%d')
    snaps=root/'data/site_prediction_snapshots'
    before={p.stem for p in snaps.glob(f'{today}-??-??.json')}
    cwd=Path.cwd()
    orig_text,orig_bytes,orig_open=Path.read_text,Path.read_bytes,Path.open
    def guard(p):
        if set(p.parts)&FORBIDDEN:raise RuntimeError('V229_FORBIDDEN_FILE_ACCESS_'+str(p))
    def read_text(p,*a,**kw):guard(p);return orig_text(p,*a,**kw)
    def read_bytes(p,*a,**kw):guard(p);return orig_bytes(p,*a,**kw)
    def open_safe(p,*a,**kw):guard(p);return orig_open(p,*a,**kw)
    try:
        os.chdir(root)
        Path.read_text,Path.read_bytes,Path.open=read_text,read_bytes,open_safe
        exec(compile(code,'V229_PINNED_SITE_ONLY_FREEZE','exec'),{'__name__':'__main__'})
    finally:
        Path.read_text,Path.read_bytes,Path.open=orig_text,orig_bytes,orig_open
        os.chdir(cwd)
    after={p.stem for p in snaps.glob(f'{today}-??-??.json')}
    new=sorted(after-before)
    if not new:
        print('V229_NO_NEW_ELIGIBLE_SNAPSHOT_NO_FABRICATED_PASS')
        return 0
    now=datetime.now(UTC)
    # Stage NOTHING if even one race fails post-freeze provenance review.
    evidence={key:validate(root,key,now) for key in new}
    for key,rec in evidence.items():
        write_once(root/'data/site_autopilot/v229_evidence'/f'{key}.json',rec)
        # V214 / V215 require this exact latest digest. V125 can extend it later.
        write_once(root/'data/site_prediction_audit'/f'{key}.json',{
            'schema_version':'boat-edge-final15m-audit-v125',
            'race_key':key,'first_audited_at':now.isoformat(),
            'last_audited_at':now.isoformat(),
            'latest_snapshot_sha256':rec['snapshot_sha256'],
            'latest_snapshot_saved_at':rec['snapshot_saved_at'],
            'revision_count':1,'revisions':[{
                'snapshot_sha256':rec['snapshot_sha256'],
                'saved_at':rec['snapshot_saved_at'],
                'odds_sha256_snapshot':rec['odds_sha256'],
                'race_sha256_snapshot':rec['race_sha256'],
                'atomic_pre_result_proof_sha256':digest(root/'data/site_autopilot/v229_evidence'/f'{key}.json')
            }],
            'pass':True,'atomic_pre_result_audit':True,
            'scope':'SITE_ONLY_NOT_FORMAL_FRESH',
            'source_evidence_file':f'data/site_autopilot/v229_evidence/{key}.json'
        })
    print('V229_NEW_SNAPSHOT_AND_ATOMIC_SHA_AUDIT_PASS '+json.dumps({'new_races':new,'count':len(new)},sort_keys=True))
    return len(new)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default='.')
    args=p.parse_args()
    run(Path(args.root))
