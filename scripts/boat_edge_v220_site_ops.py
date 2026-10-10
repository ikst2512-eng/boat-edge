#!/usr/bin/env python3
"""V220 read-only pre-result site operations; never opens formal targets, result, payout or combined API.
Only documents actual saved source evidence. Safe recovery *intent* is separate from purchase/model logic.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import re

JST=timezone(timedelta(hours=9))
SCHEMA='BOAT_EDGE_V220_SITE_AUTONOMOUS_OPERATIONS_V1'
KEY=re.compile(r'^20\d{6}-\d{2}-\d{2}$')
RECOVER_ALLOW={'auto-update.yml','site-odds.yml'}

def load(p):
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except (OSError,ValueError,UnicodeError):
        return None

def moment(s):
    try:
        x=datetime.fromisoformat(str(s).replace('Z','+00:00'))
        return x.astimezone(timezone.utc) if x.tzinfo else None
    except (ValueError,TypeError,OverflowError):
        return None

def age_minutes(s,now):
    x=moment(s)
    if not x:return None
    age=(now-x).total_seconds()/60
    return round(age,1) if 0<=age<14400 else None

def expected_deadline(k,clock):
    if not KEY.fullmatch(str(k)) or not re.fullmatch(r'\d\d:\d\d',str(clock)):return None
    try:
        return datetime.strptime(k[:8]+clock,'%Y%m%d%H:%M').replace(tzinfo=JST).astimezone(timezone.utc)
    except ValueError:return None

def source_status(root,key,now):
    race=load(root/'data/races'/f'{key}.json') or {}
    meta=race.get('meta') or {};audit=race.get('source_audit') or {}
    card=audit.get('race_card') or {};before=audit.get('beforeinfo') or {}
    scratch=load(root/'data/site_scratches_v182'/f'{key}.json') or {}
    odds=load(root/'data/site_odds'/f'{key}.json') or {}
    snap=load(root/'data/site_prediction_snapshots'/f'{key}.json') or {}
    issues=[]
    if meta.get('phase')!='PRE_RESULT' or any(meta.get(g) is not False for g in ('results_seen','unlock','scoring')):
        issues.append('race_pre_result_not_verified')
    if len(race.get('racers') or [])!=6:issues.append('racers_not_six')
    if card.get('status')!='ok' or age_minutes(card.get('fetched_at'),now) is None:issues.append('race_card_missing_or_future')
    elif age_minutes(card.get('fetched_at'),now)>20:issues.append('race_card_stale')
    if before.get('status')!='ok' or age_minutes(before.get('fetched_at'),now) is None:issues.append('beforeinfo_unavailable')
    elif age_minutes(before.get('fetched_at'),now)>15:issues.append('beforeinfo_stale')
    if scratch.get('race_key')!=key or scratch.get('blocked') is not False:
        issues.append('scratch_unverified_or_blocked')
    elif scratch.get('race_card_source_status')!='ok' or age_minutes(scratch.get('checked_at'),now) is None or age_minutes(scratch.get('checked_at'),now)>15:
        issues.append('scratch_stale')
    if odds.get('race_key')!=key or odds.get('phase')!='PRE_RESULT_PURCHASE_ONLY' or age_minutes(odds.get('fetched_at'),now) is None:
        issues.append('odds_evidence_missing')
    elif age_minutes(odds.get('fetched_at'),now)>15:issues.append('odds_evidence_stale')
    if snap.get('race_key')!=key or snap.get('snapshot_window')!='FINAL_15M' or not snap.get('odds_sha256'):
        issues.append('frozen_prediction_missing_or_invalid')
    return sorted(set(issues))

def compute(root,now):
    now=now.astimezone(timezone.utc)
    day=now.astimezone(JST).strftime('%Y%m%d')
    today=load(root/'data/today.json') or {}
    odds=load(root/'data/site_odds/index.json') or {}
    readiness=load(root/'data/site_paper_sim/readiness_v215_current.json') or {}
    evaluation=load(root/'data/site_autovalidation/current.json') or {}
    paper=load(root/'data/site_paper_sim/current.json') or {}
    formal=load(root/'data/formal_status.json') or {}
    schedule_ok=str(today.get('date','')).replace('-','')==day
    race_cards=[]
    if schedule_ok:
        for venue in today.get('venues') or []:
            for race in venue.get('races') or []:
                key=race.get('race_key')
                d=expected_deadline(key,race.get('deadline'))
                if d and str(key).startswith(day+'-'):
                    race_cards.append((d,key,str(venue.get('venue') or '-')))
    race_cards.sort()
    soon=[];urgent=[]
    for due,key,venue in race_cards:
        minutes=(due-now).total_seconds()/60
        if 0<=minutes<=90 and len(soon)<8:
            soon.append({'key':key,'venue':venue,'deadline_jst':due.astimezone(JST).strftime('%H:%M'),
                         'minutes_left':round(minutes,1)})
        if 2<=minutes<=15 and len(urgent)<12:
            urgent.append({'key':key,'venue':venue,'deadline_jst':due.astimezone(JST).strftime('%H:%M'),
                           'minutes_left':round(minutes,1),'missing_evidence':source_status(root,key,now)})
    active=bool(soon)
    source_age=age_minutes(today.get('updated_at'),now)
    odds_age=age_minutes(odds.get('updated_at'),now)
    reasons=[]
    if not schedule_ok:reasons.append('today_schedule_not_confirmed')
    if active and (source_age is None or source_age>30):reasons.append('collector_index_stale')
    # Odds source index is only required during its actual collection window (-45min onward).
    if any(r['minutes_left']<=40 for r in soon) and (odds_age is None or odds_age>30):
        reasons.append('odds_index_stale')
    if urgent and any(x['missing_evidence'] for x in urgent):reasons.append('predeadline_incomplete')
    if evaluation.get('schema')!='BOAT_EDGE_SITE_AUTOVALIDATION_V1':
        reasons.append('site_validation_report_unavailable')
    if str(readiness.get('day_jst'))!=day:reasons.append('predeadline_diagnostics_not_today')
    if paper.get('money',{}).get('daily_budget_yen')!=50000 or paper.get('mode')!='PAPER_ONLY':
        reasons.append('paper_budget_policy_mismatch')
    formal_guard=(formal.get('guards') or {})
    if any(formal_guard.get(g) is not False for g in ('results_seen','unlock','scoring')) or formal_guard.get('RESULT_UNLOCK_TOKEN') is not None:
        reasons.append('formal_status_requires_manual_safety_review')
    recover=[]
    # A scheduled job may already be running: the workflow will suppress dispatch when
    # that exact action has run recently; no results endpoints, betting or formal actions.
    if active and 'collector_index_stale' in reasons:recover.append('auto-update.yml')
    if any(r['minutes_left']<=12 and any(i in ('race_pre_result_not_verified','racers_not_six','race_card_missing_or_future','race_card_stale','beforeinfo_unavailable','beforeinfo_stale') for i in r['missing_evidence']) for r in urgent):
        recover.append('auto-update.yml')
    if any(r['minutes_left']<=25 for r in soon) and 'odds_index_stale' in reasons:
        recover.append('site-odds.yml')
    if any(r['minutes_left']<=12 and any(i.startswith('odds_evidence_') for i in r['missing_evidence']) for r in urgent):
        recover.append('site-odds.yml')
    recover=sorted(set(recover)&RECOVER_ALLOW)
    if reasons:status='NEEDS_ATTENTION'
    elif not urgent:status='WAITING_FOR_PREDEADLINE'
    else:status='MONITORING_PREDEADLINE'
    nxt=next(({'race_key':k,'venue':v,'deadline_jst':d.astimezone(JST).strftime('%H:%M'),
               'watch_from_jst':(d-timedelta(minutes=15)).astimezone(JST).strftime('%H:%M')} for d,k,v in race_cards if d>now),None)
    return {'schema':SCHEMA,'scope':'SITE_ONLY_PRE_RESULT_OPERATIONS_NOT_FORMAL_FRESH',
      'day_jst':day,'status':status,'issues':sorted(set(reasons)),
      'scheduled_races':len(race_cards),'active_window_races':len(soon),'decision_window_races':len(urgent),
      'next_race':nxt,'current_windows':[{k:v for k,v in row.items() if k!='minutes_left'} for row in urgent],
      'data_sources':{'collector_freshness':'CURRENT' if source_age is not None and source_age<=30 else 'STALE_OR_UNVERIFIED',
                      'odds_index_freshness':'CURRENT' if odds_age is not None and odds_age<=30 else 'STALE_OR_UNVERIFIED',
                      'site_autovalidation':evaluation.get('status','NOT_AVAILABLE'),
                      'predeadline_observations':readiness.get('day_observed_races',0)},
      'research_model_production_promotion':False,'paper_wager_authorized_by_this_runner':False,
      'formal_unlock_or_scoring_authorized':False,'formal_results_read_by_this_runner':False,
      'recovery_dispatch_candidates':recover}

def write_if_changed(path,doc):
    encoded=json.dumps(doc,sort_keys=True,ensure_ascii=False,indent=2)+'\n'
    if path.exists() and path.read_text(encoding='utf-8')==encoded:return False
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(encoded,encoding='utf-8')
    return True

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',default='.');parser.add_argument('--at');parser.add_argument('--recovery-plan',action='store_true')
    a=parser.parse_args();now=moment(a.at) if a.at else datetime.now(timezone.utc)
    if not now:raise SystemExit('INVALID_CLOCK')
    doc=compute(Path(a.root),now)
    if a.recovery_plan:
        print(json.dumps({'workflows':doc['recovery_dispatch_candidates']},sort_keys=True))
    else:
        output=Path(a.root)/'data/site_ops_v220/current.json'
        changed=write_if_changed(output,doc)
        print('V220_SITE_OPERATIONS '+json.dumps({'status':doc['status'],'issues':doc['issues'],'window':doc['decision_window_races'],
                  'next':doc['next_race'],'saved':changed,'recovery':doc['recovery_dispatch_candidates']},ensure_ascii=False))
if __name__=='__main__':main()
