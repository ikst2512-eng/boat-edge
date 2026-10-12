#!/usr/bin/env python3
"""V220 read-only pre-result site operations; never opens formal targets, result, payout or combined API.
Only documents actual saved source evidence. Safe recovery *intent* is separate from purchase/model logic.
"""
from __future__ import annotations
import argparse
import hashlib
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
    elif (scratch.get('race_card_source_status')!='ok' or
          scratch.get('official_beforeinfo_source_status')!='ok' or
          age_minutes(scratch.get('checked_at'),now) is None or
          age_minutes(scratch.get('checked_at'),now)>15):
        issues.append('scratch_stale')
    if (odds.get('race_key')!=key or odds.get('phase')!='PRE_RESULT_PURCHASE_ONLY' or
        odds.get('results_seen') is not False or odds.get('scoring') is not False or
        age_minutes(odds.get('fetched_at'),now) is None):
        issues.append('odds_evidence_missing')
    elif age_minutes(odds.get('fetched_at'),now)>15:
        issues.append('odds_evidence_stale')
    else:
        rows=odds.get('trifecta_odds')
        valid=(isinstance(rows,dict) and len(rows)==120 and
               odds.get('available_count')==120 and
               all(f'{a}-{b}-{c}' in rows and
                   type(rows[f'{a}-{b}-{c}']) in (int,float) and
                   0<rows[f'{a}-{b}-{c}']<float('inf')
                   for a in range(1,7) for b in range(1,7) for c in range(1,7)
                   if len({a,b,c})==3))
        if not valid:issues.append('odds_120_incomplete')
        if odds.get('verified_official_dom_v167') is not True:
            issues.append('odds_official_dom_unverified')
    if snap.get('race_key')!=key or snap.get('snapshot_window')!='FINAL_15M' or not snap.get('odds_sha256'):
        issues.append('frozen_prediction_missing_or_invalid')
    return sorted(set(issues))

def freeze_coverage(root,day,now):
    """Site-only, observed-window coverage; never query a race result.

    An early 'snapshot_missing' observation is NOT a final missed freeze:
    later immutable evidence can appear in the saved prediction window.
    SHA consistency and V229 same-run provenance are kept separate.
    """
    summary={'day_jst':day,'scope':'OBSERVED_PREDEADLINE_WINDOWS_ONLY_NOT_ALL_RACES',
             'observed_races':0,'matured_observed_races':0,
             'snapshot_present':0,'sha_consistent_predeadline_snapshots':0,
             'v229_atomic_evidence_matched':0,'early_missing_later_snapshot_present':0,
             'not_found_after_deadline':0,'pending_before_deadline':0,
             'snapshot_or_audit_unverified':0,'observed_gaps_for_currently_missing':{},
             'status':'NO_PRE_RESULT_OBSERVATIONS'}
    path=root/'data/site_paper_sim/readiness_history_v215'/f'{day}.json'
    history=load(path) or {}
    if history.get('schema')!='BOAT_EDGE_V215_DIAGNOSTIC_HISTORY_V1' or history.get('day_jst')!=day:
        return summary
    observations=history.get('observations')
    if not isinstance(observations,dict):return summary
    for key,record in sorted(observations.items()):
        if not isinstance(record,dict) or not KEY.fullmatch(str(key)) or not key.startswith(day+'-'):
            continue
        deadline=expected_deadline(key,record.get('deadline'))
        if deadline is None:continue
        summary['observed_races']+=1
        matured=now>=deadline
        if matured:summary['matured_observed_races']+=1
        snap_file=root/'data/site_prediction_snapshots'/f'{key}.json'
        if not snap_file.is_file():
            field='not_found_after_deadline' if matured else 'pending_before_deadline'
            summary[field]+=1
            if matured:
                gaps=record.get('source_gaps_seen') or []
                for gap in set(x for x in gaps if isinstance(x,str) and len(x)<=80):
                    counts=summary['observed_gaps_for_currently_missing']
                    counts[gap]=counts.get(gap,0)+1
            continue
        summary['snapshot_present']+=1
        if 'snapshot_missing' in (record.get('reasons_seen') or []):
            summary['early_missing_later_snapshot_present']+=1
        snap=load(snap_file) or {}
        audit=load(root/'data/site_prediction_audit'/f'{key}.json') or {}
        if not isinstance(snap,dict) or not isinstance(audit,dict):
            summary['snapshot_or_audit_unverified']+=1;continue
        saved=moment(snap.get('saved_at'))
        lead=(deadline-saved).total_seconds() if saved else None
        guards=snap.get('guards') or {}
        try:
            snap_sha=hashlib.sha256(snap_file.read_bytes()).hexdigest()
            race_file=root/'data/races'/f'{key}.json'
            race_sha=hashlib.sha256(race_file.read_bytes()).hexdigest()
        except OSError:
            summary['snapshot_or_audit_unverified']+=1;continue
        consistent=(
            snap.get('race_key')==key and snap.get('snapshot_window')=='FINAL_15M'
            and all(guards.get(k) is False for k in ('results_seen','unlock','scoring'))
            and lead is not None and 120<=lead<=900
            and audit.get('race_key')==key and audit.get('pass') is True
            and audit.get('latest_snapshot_sha256')==snap_sha
            and snap.get('race_sha256')==race_sha)
        if not consistent:
            summary['snapshot_or_audit_unverified']+=1;continue
        summary['sha_consistent_predeadline_snapshots']+=1
        proof=load(root/'data/site_autopilot/v229_evidence'/f'{key}.json') or {}
        stamp=moment(proof.get('evidence_captured_at'))
        if (proof.get('schema')=='BOAT_EDGE_V229_ATOMIC_PRE_RESULT_SOURCE_EVIDENCE_V1'
            and proof.get('race_key')==key and proof.get('snapshot_sha256')==snap_sha
            and proof.get('race_sha256')==race_sha
            and proof.get('new_snapshot_created_this_run') is True
            and proof.get('results_seen') is False
            and proof.get('formal_fresh_unlock') is False
            and proof.get('scoring') is False
            and stamp is not None and saved<=stamp<=deadline):
            summary['v229_atomic_evidence_matched']+=1
    summary['status']='OBSERVED_WINDOW_COUNTS' if summary['observed_races'] else 'NO_PRE_RESULT_OBSERVATIONS'
    return summary


def compute(root,now):
    now=now.astimezone(timezone.utc)
    day=now.astimezone(JST).strftime('%Y%m%d')
    today=load(root/'data/today.json') or {}
    odds=load(root/'data/site_odds/index.json') or {}
    readiness=load(root/'data/site_paper_sim/readiness_v215_current.json') or {}
    evaluation=load(root/'data/site_autovalidation/current.json') or {}
    paper=load(root/'data/site_paper_sim/current.json') or {}
    formal=load(root/'data/formal_status.json') or {}
    collector_health=load(root/'data/health.json') or {}
    previous_day=(now.astimezone(JST).date()-timedelta(days=1)).strftime('%Y%m%d')
    freeze_funnel={'today':freeze_coverage(root,day,now),
                   'previous_day':freeze_coverage(root,previous_day,now)}
    urgent_names=('beforeinfo_urgent_15m_targets','beforeinfo_urgent_15m_ok',
                  'beforeinfo_urgent_15m_published_wait','beforeinfo_urgent_15m_error')
    urgent_counts=[collector_health.get(name) for name in urgent_names]
    urgent_fresh=age_minutes(collector_health.get('updated_at'),now)
    urgent_telemetry_ok=(urgent_fresh is not None and urgent_fresh<=30 and
        all(type(v) is int and v>=0 for v in urgent_counts) and
        urgent_counts[0]==sum(urgent_counts[1:]) and
        collector_health.get('results_seen') is False and
        collector_health.get('unlock') is False and
        collector_health.get('scoring') is False)
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
    if any(r['minutes_left']<=12 and any(i.startswith('odds_evidence_') or i in ('odds_120_incomplete','odds_official_dom_unverified') for i in r['missing_evidence']) for r in urgent):
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
      'official_beforeinfo_urgent_15m':{
        'status':'OBSERVED' if urgent_telemetry_ok else 'UNVERIFIED_OR_STALE',
        'targets':urgent_counts[0] if urgent_telemetry_ok else None,
        'ok':urgent_counts[1] if urgent_telemetry_ok else None,
        'published_wait':urgent_counts[2] if urgent_telemetry_ok else None,
        'error':urgent_counts[3] if urgent_telemetry_ok else None,
        'health_updated_at':collector_health.get('updated_at') if urgent_telemetry_ok else None},
      'site_prediction_freeze_observation':freeze_funnel,
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
