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
import subprocess
import sys

JST=timezone(timedelta(hours=9))
SCHEMA='BOAT_EDGE_V220_SITE_AUTONOMOUS_OPERATIONS_V1'
KEY=re.compile(r'^20\d{6}-\d{2}-\d{2}$')
RECOVER_ALLOW={'auto-update.yml','site-odds.yml','BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml'}

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
    # Recovery decisions use the exact same age boundary as the independent
    # freeze validator. Rounding first could accept a source one second late.
    return age if 0<=age<14400 else None

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
    # V229 independently enforces 960 seconds. A looser monitor limit would
    # dispatch a doomed freeze instead of requesting fresh official sources.
    elif age_minutes(card.get('fetched_at'),now)>16:issues.append('race_card_stale')
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

def verified_v229_recovery_source(root,key,now):
    """Do not waste the V229 recovery window on a source that V229 will reject.

    Reuse the existing 1C PRE_RESULT original official HTML / V182 scratch /
    official 120-odds verifier; V220 status labels alone are not readiness.
    Read only. No result, payout, formal prediction, or source modification.
    """
    scripts=str(Path(__file__).resolve().parent)
    if scripts not in sys.path:sys.path.insert(0,scripts)
    from boat_edge_01_gate1c_source_ready import valid
    race=load(root/'data/races'/f'{key}.json') or {}
    due=expected_deadline(key,(race.get('meta') or {}).get('deadline'))
    return due is not None and valid(root,key,due,now) is not None


def freeze_coverage(root,day,now):
    """Site-only, observed-window coverage; never query a race result.

    An early 'snapshot_missing' observation is NOT a final missed freeze:
    later immutable evidence can appear in the saved prediction window.
    SHA consistency and V229 same-run provenance are kept separate.
    """
    summary={'day_jst':day,'scope':'OBSERVED_PREDEADLINE_WINDOWS_ONLY_NOT_ALL_RACES',
             'observed_races':0,'matured_observed_races':0,
             'snapshot_present':0,'sha_consistent_predeadline_snapshots':0,
             'predeadline_snapshot_with_matching_audit':0,
             'source_changed_after_freeze':0,'source_missing_after_freeze':0,
             'v229_attestation_record_matched':0,
             'v229_atomic_evidence_matched':0,'early_missing_later_snapshot_present':0,
             'not_found_after_deadline':0,'pending_before_deadline':0,
             'not_found_with_observed_gaps':0,'not_found_without_observed_gaps':0,
             'not_found_last_seen_inside_2_to_10m_window':0,
             'not_found_last_seen_outside_2_to_10m_window':0,
             'not_found_last_seen_unverified':0,
             'not_found_without_gaps_inside_2_to_10m_window':0,
             'snapshot_or_audit_unverified':0,'observed_gaps_for_currently_missing':{},
             'integrity_note':'A missing snapshot without observed source gaps is not proof of eligibility. Last V215 observation in the V229 2-10m window is not proof the V229 freeze job actually ran. Historical at-freeze record does not imply current-source SHA parity.',
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
                # V290: a missing snapshot with NO observed source gap
                # does not prove source readiness. Track the separate
                # scheduler/freeze decision window, without any backfill.
                gaps=record.get('source_gaps_seen')
                has_gaps=not isinstance(gaps,list) or bool(gaps)
                summary['not_found_with_observed_gaps' if has_gaps else
                        'not_found_without_observed_gaps']+=1
                if isinstance(gaps,list):
                    for gap in set(x for x in gaps if isinstance(x,str) and len(x)<=80):
                        counts=summary['observed_gaps_for_currently_missing']
                        counts[gap]=counts.get(gap,0)+1
                last_seen=moment(record.get('last_seen_at'))
                lead=(deadline-last_seen).total_seconds()/60 if last_seen else None
                if lead is None:
                    summary['not_found_last_seen_unverified']+=1
                elif 2<=lead<=10:
                    summary['not_found_last_seen_inside_2_to_10m_window']+=1
                    if not has_gaps:
                        summary['not_found_without_gaps_inside_2_to_10m_window']+=1
                else:
                    summary['not_found_last_seen_outside_2_to_10m_window']+=1
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
        except OSError:
            summary['snapshot_or_audit_unverified']+=1;continue
        # V285: first establish the exact saved predeadline snapshot/audit.
        # A later race-file mutation must not erase its existence or claim
        # that the original SHA-bound pre-result source is still intact.
        metadata_ok=(
            snap.get('race_key')==key and snap.get('snapshot_window')=='FINAL_15M'
            and isinstance(guards,dict)
            and all(guards.get(k) is False for k in ('results_seen','unlock','scoring'))
            and lead is not None and 120<=lead<=900
            and re.fullmatch(r'[0-9a-f]{64}',str(snap.get('race_sha256'))) is not None
            and audit.get('race_key')==key and audit.get('pass') is True
            and audit.get('latest_snapshot_sha256')==snap_sha)
        if not metadata_ok:
            summary['snapshot_or_audit_unverified']+=1;continue
        summary['predeadline_snapshot_with_matching_audit']+=1
        # The independent same-run V229 *record* is inspected separately
        # from today's mutable race JSON; do not call it a present-source PASS.
        proof=load(root/'data/site_autopilot/v229_evidence'/f'{key}.json') or {}
        stamp=moment(proof.get('evidence_captured_at'))
        same_run_record=(
            proof.get('schema')=='BOAT_EDGE_V229_ATOMIC_PRE_RESULT_SOURCE_EVIDENCE_V1'
            and proof.get('race_key')==key and proof.get('snapshot_sha256')==snap_sha
            and proof.get('race_sha256')==snap.get('race_sha256')
            and proof.get('new_snapshot_created_this_run') is True
            and proof.get('results_seen') is False
            and proof.get('formal_fresh_unlock') is False
            and proof.get('scoring') is False
            and stamp is not None and saved<=stamp<=deadline)
        if same_run_record:summary['v229_attestation_record_matched']+=1
        race_file=root/'data/races'/f'{key}.json'
        try:
            race_sha=hashlib.sha256(race_file.read_bytes()).hexdigest()
        except OSError:
            summary['source_missing_after_freeze']+=1;continue
        if snap.get('race_sha256')!=race_sha:
            summary['source_changed_after_freeze']+=1;continue
        summary['sha_consistent_predeadline_snapshots']+=1
        if same_run_record:summary['v229_atomic_evidence_matched']+=1
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
    # V289: partial is a SUBSET of published_wait, not a disjoint outcome.
    # Old health data without the field may remain observable but never
    # claims the partial count is zero. Contradictory values fail closed.
    urgent_partial=collector_health.get('beforeinfo_urgent_15m_partial')
    partial_valid=(urgent_partial is None or
                   (type(urgent_partial) is int and urgent_partial>=0 and
                    type(urgent_counts[2]) is int and urgent_partial<=urgent_counts[2]))
    urgent_fresh=age_minutes(collector_health.get('updated_at'),now)
    urgent_telemetry_ok=(urgent_fresh is not None and urgent_fresh<=30 and
        partial_valid and all(type(v) is int and v>=0 for v in urgent_counts) and
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
    # V410: GitHub's best-effort cron missed the V229/V235 2-10m
    # decision window for three observed 2026-10-14 races. Reuse the
    # EXISTING guarded V229 workflow only with complete currently saved
    # source evidence. Readiness observations alone never authorize a freeze.
    # No retrospective runs or writes into already-present/invalid snapshots.
    # A UI all-clear is not enough: require source-bound PRE_RESULT proof.
    formal_locked=(
        all(formal_guard.get(k) is False for k in ('results_seen','unlock','scoring'))
        and formal_guard.get('RESULT_UNLOCK_TOKEN') is None
        and (formal.get('formalFirst100') or {}).get('races',0)==0)
    if formal_locked and any(
        2<=r['minutes_left']<=10
        and r['missing_evidence']==['frozen_prediction_missing_or_invalid']
        and not (root/'data/site_prediction_snapshots'/f"{r['key']}.json").exists()
        and verified_v229_recovery_source(root,r['key'],now)
        for r in urgent
    ):
        recover.append('BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml')
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
        'partial_six_boat_source':urgent_partial if urgent_telemetry_ok else None,
        'error':urgent_counts[3] if urgent_telemetry_ok else None,
        'health_updated_at':collector_health.get('updated_at') if urgent_telemetry_ok else None},
      'site_prediction_freeze_observation':freeze_funnel,
      'research_model_production_promotion':False,'paper_wager_authorized_by_this_runner':False,
      'formal_unlock_or_scoring_authorized':False,'formal_results_read_by_this_runner':False,
      'recovery_dispatch_candidates':recover}

def gate1c_first_git_summary(root, day, now, verify=None):
    """Read-only 1C numerator proof, NOT a source-eligible-race denominator.

    Reuse the existing historical V125/Git-first-add validator. A current
    snapshot and matching mutable audit are not enough to claim an immutable
    original. No results, payouts, or Formal Fresh files are ever opened.
    """
    if verify is None:
        from site_v136_historical_proof import check_historical_proof
        verify = check_historical_proof
    out={'day_jst':day, 'scope':'OBSERVED_MATURED_RACES_ONLY',
         'observed_races':0, 'matured_races':0, 'missing_after_deadline':0,
         'snapshots_present':0, 'first_git_original_sha_proven':0,
         'original_not_verified':0, 'unverified_reasons':{},
         # Source release times and all race-specific eligibility guards
         # cannot be reconstructed from a sampled V215 observation history.
         'independently_source_eligible_denominator':None,
         'eligible_save_rate_percent':None,
         'acceptance_99_percent_proven':False}
    hist=load(root/'data/site_paper_sim/readiness_history_v215'/f'{day}.json') or {}
    if hist.get('schema')!='BOAT_EDGE_V215_DIAGNOSTIC_HISTORY_V1' or hist.get('day_jst')!=day:
        return out
    obs=hist.get('observations')
    if not isinstance(obs,dict):return out
    for key,record in sorted(obs.items()):
        if not isinstance(record,dict) or not KEY.fullmatch(str(key)) or not key.startswith(day+'-'):
            continue
        due=expected_deadline(key,record.get('deadline'))
        if due is None:continue
        out['observed_races']+=1
        if now<due:continue
        out['matured_races']+=1
        p=root/'data/site_prediction_snapshots'/f'{key}.json'
        if p.is_symlink() or not p.is_file():
            out['missing_after_deadline']+=1
            continue
        out['snapshots_present']+=1
        audit_path=root/'data/site_prediction_audit'/f'{key}.json'
        # The reused historical checker reads the audit file directly.
        # Reject symlink redirection rather than possibly opening a protected
        # result/formal file through an untrusted checkout.
        if audit_path.is_symlink():
            out['original_not_verified']+=1
            out['unverified_reasons']['audit_symlink_blocked']=(
                out['unverified_reasons'].get('audit_symlink_blocked',0)+1)
            continue
        snap=load(p)
        reason='snapshot_invalid'
        if isinstance(snap,dict) and snap.get('race_key')==key and snap.get('deadline')==record.get('deadline'):
            saved=moment(snap.get('saved_at'))
            # Match V229's strict 2–10 minute decision window. A 15-minute
            # SITE-only record is not silently promoted to a V229 success.
            if saved is not None and 120 <= (due-saved).total_seconds() <= 600:
                try:
                    reason, commit=verify(root,key,snap)
                except (OSError,ValueError,TypeError,RuntimeError):
                    reason='first_git_verifier_failed_closed'
                if reason=='PASS' and commit is not None:
                    out['first_git_original_sha_proven']+=1
                    continue
                if reason=='PASS':reason='first_git_commit_missing'
            else:
                reason='outside_v229_decision_window'
        out['original_not_verified']+=1
        out['unverified_reasons'][reason]=out['unverified_reasons'].get(reason,0)+1
    return out


def gate1c_source_receipt_first_git_proof(root,key,receipt):
    """Verify first-added receipt AND source blobs in THAT SAME Git tree.

    Source blobs at current HEAD may change later. Reconstructing eligibility
    from today's mutable source files is forbidden. A forged/backfilled receipt
    or a delayed Git addition beyond the decision window cannot be a PASS.
    """
    relative=f'data/site_ops_v220/gate1c_source_ready/{key}.json'
    p=root/relative
    if (not KEY.fullmatch(str(key)) or p.is_symlink() or not p.is_file()
            or any(parent.is_symlink() for parent in p.parents)):
        return 'receipt_path_unverified',None
    if not isinstance(receipt,dict) or receipt.get('schema')!='BOAT_EDGE_GATE1C_PROSPECTIVE_SOURCE_READY_V1':
        return 'receipt_schema_unverified',None
    due=expected_deadline(key,receipt.get('deadline_jst'))
    observed=moment(receipt.get('observed_at'))
    if (due is None or observed is None or receipt.get('race_key')!=key
            or receipt.get('deadline_at')!=due.isoformat()
            or not 120 <= (due-observed).total_seconds() <= 600
            or receipt.get('official_odds_combinations')!=120
            or receipt.get('six_boat_exhibition_complete') is not True
            or not all(receipt.get(x) is False for x in
                       ('results_seen','formal_fresh_unlock','scoring'))
            or receipt.get('first_git_source_commit_independently_proven') is not False
            or receipt.get('independently_eligible_denominator_established') is not False):
        return 'receipt_metadata_or_window_unverified',None
    digests=receipt.get('source_sha256')
    if (not isinstance(digests,dict) or set(digests)!={'race','scratch','odds'}
            or any(re.fullmatch(r'[0-9a-f]{64}',str(v)) is None for v in digests.values())):
        return 'receipt_source_sha_invalid',None
    try:
        hist=subprocess.run(['git','log','--diff-filter=A','--format=%H%x09%cI',
                             '--',relative],cwd=root,capture_output=True,text=True,
                            timeout=12,check=True).stdout.strip().splitlines()
        # Any delete/readd creates ambiguous proof even if current HEAD agrees.
        if len(hist)!=1:
            return 'receipt_first_git_add_missing_or_ambiguous',None
        fields=hist[0].split('\t')
        if len(fields)!=2 or re.fullmatch(r'[0-9a-f]{40}',fields[0]) is None:
            return 'receipt_first_git_commit_invalid',None
        commit,committed=fields
        at=moment(committed)
        # Git timestamps are seconds; observed_at may have microseconds.
        if (at is None or at+timedelta(seconds=1)<observed
                or at>due-timedelta(seconds=120)):
            return 'receipt_first_git_add_outside_window',None
        original=subprocess.run(['git','show',f'{commit}:{relative}'],cwd=root,
                                capture_output=True,timeout=12,check=True).stdout
        if hashlib.sha256(original).digest()!=hashlib.sha256(p.read_bytes()).digest():
            return 'receipt_changed_after_first_git_add',None
        if json.loads(original)!=receipt:
            return 'receipt_original_metadata_changed',None
        for label,subdir in (('race','data/races'),('scratch','data/site_scratches_v182'),
                             ('odds','data/site_odds')):
            blob=subprocess.run(['git','show',f'{commit}:{subdir}/{key}.json'],
                                cwd=root,capture_output=True,timeout=12,
                                check=True).stdout
            if hashlib.sha256(blob).hexdigest()!=digests[label]:
                return f'{label}_source_not_in_first_receipt_git_tree',None
        # Source JSON alone could cite an unbacked official-HTML SHA.
        # Require exact raw HTML bytes in the SAME first Git tree, not
        # whatever files happen to exist in today's mutable checkout.
        for role,field in (('racelist','official_race_card_sha256'),
                           ('beforeinfo','official_beforeinfo_sha256')):
            expected=receipt.get(field)
            if not isinstance(expected,str) or re.fullmatch(r'[0-9a-f]{64}',expected) is None:
                return f'{role}_original_html_sha_unverified',None
            rel=f'data/raw/{key[:8]}/{key[9:11]}_{key[12:14]}_{role}.html'
            raw=subprocess.run(['git','show',f'{commit}:{rel}'],cwd=root,
                               capture_output=True,timeout=12,check=True).stdout
            if hashlib.sha256(raw).hexdigest()!=expected:
                return f'{role}_original_html_not_in_first_receipt_git_tree',None
    except (OSError,ValueError,UnicodeError,subprocess.SubprocessError):
        return 'receipt_original_git_proof_unavailable',None
    return 'PASS',commit


def gate1c_source_receipt_summary(root,day,now,prediction_verify=None):
    """Conservative lower-bound cohort; NEVER infer completeness/99%."""
    if prediction_verify is None:
        from site_v136_historical_proof import check_historical_proof
        prediction_verify=check_historical_proof
    out={'day_jst':day, 'scope':'SAMPLED_FIRST_GIT_SOURCE_READY_ONLY',
         'receipts_seen':0, 'receipts_matured':0,
         'source_ready_first_git_proven':0,
         'source_ready_original_unverified':0,
         'source_ready_unverified_reasons':{},
         'source_ready_with_proven_prediction':0,
         # The V136 original snapshot is independently genuine but may refer
         # to DIFFERENT race/odds inputs from the first-ready observation.
         # Never silently equate two independent Git-proof successes.
         'source_ready_with_exact_race_odds_sha':0,
         'source_ready_prediction_input_parity_unverified':0,
         'source_ready_prediction_input_parity_reasons':{},
         'source_ready_without_proven_prediction':0,
         'source_ready_missing_prediction_keys':[],
         'source_ready_prediction_unverified_reasons':{},
         'independently_source_eligible_denominator':None,
         'eligible_save_rate_percent':None, 'acceptance_99_percent_proven':False,
         'sampling_complete_for_all_scheduled_races':False}
    base=root/'data/site_ops_v220/gate1c_source_ready'
    if base.is_symlink() or not base.is_dir():return out
    for p in sorted(base.glob(f'{day}-??-??.json')):
        key=p.stem
        if not KEY.fullmatch(key) or p.is_symlink():continue
        out['receipts_seen']+=1
        rec=load(p)
        deadline=expected_deadline(key,rec.get('deadline_jst')) if isinstance(rec,dict) else None
        if deadline is None:
            out['source_ready_original_unverified']+=1
            code='receipt_deadline_unverified'
            out['source_ready_unverified_reasons'][code]=out['source_ready_unverified_reasons'].get(code,0)+1
            continue
        if now<deadline:continue
        out['receipts_matured']+=1
        try:
            code,original=gate1c_source_receipt_first_git_proof(root,key,rec)
        except (OSError,ValueError,RuntimeError):
            code,original='receipt_proof_error_fail_closed',None
        if code!='PASS' or original is None:
            out['source_ready_original_unverified']+=1
            out['source_ready_unverified_reasons'][code]=out['source_ready_unverified_reasons'].get(code,0)+1
            continue
        out['source_ready_first_git_proven']+=1
        snap_path=root/'data/site_prediction_snapshots'/f'{key}.json'
        audit_path=root/'data/site_prediction_audit'/f'{key}.json'
        proof_code='snapshot_or_audit_missing'
        if (not snap_path.is_symlink() and not audit_path.is_symlink()
                and snap_path.is_file() and audit_path.is_file()):
            snap=load(snap_path)
            if isinstance(snap,dict) and snap.get('deadline')==rec.get('deadline_jst'):
                saved=moment(snap.get('saved_at'))
                if saved is not None and 120 <= (deadline-saved).total_seconds() <= 600:
                    try:
                        proof_code,pred_commit=prediction_verify(root,key,snap)
                    except (OSError,ValueError,RuntimeError):
                        proof_code,pred_commit='prediction_original_verifier_failed_closed',None
                    if proof_code=='PASS' and pred_commit:
                        out['source_ready_with_proven_prediction']+=1
                        # Source-ready receipt has already passed its ORIGINAL
                        # Git-tree race/odds SHA checks. Compare the same
                        # hashes in the V136-validated prediction. A later
                        # source-ready observation is not proof the source
                        # was ready at the earlier snapshot creation time.
                        if saved < moment(rec.get('observed_at')):
                            parity='source_ready_observation_after_prediction'
                        elif (snap.get('race_sha256') !=
                              (rec.get('source_sha256') or {}).get('race') or
                              snap.get('odds_sha256') !=
                              (rec.get('source_sha256') or {}).get('odds')):
                            parity='prediction_race_or_odds_source_sha_mismatch'
                        else:
                            parity='PASS'
                        if parity=='PASS':
                            out['source_ready_with_exact_race_odds_sha']+=1
                        else:
                            out['source_ready_prediction_input_parity_unverified']+=1
                            counter=out['source_ready_prediction_input_parity_reasons']
                            counter[parity]=counter.get(parity,0)+1
                        continue
                    if proof_code=='PASS':proof_code='prediction_first_git_commit_unverified'
                else:proof_code='prediction_outside_v229_window'
            else:proof_code='prediction_snapshot_metadata_unverified'
        out['source_ready_without_proven_prediction']+=1
        out['source_ready_missing_prediction_keys'].append(key)
        out['source_ready_prediction_unverified_reasons'][proof_code]=(
            out['source_ready_prediction_unverified_reasons'].get(proof_code,0)+1)
    return out


def gate1c_read_only_report(root,now,verify=None):
    now=now.astimezone(timezone.utc)
    day=now.astimezone(JST).date()
    return {
        'schema':'BOAT_EDGE_GATE1C_FIRST_GIT_ORIGINAL_OBSERVATION_V1',
        'scope':'SITE_ONLY_PRE_RESULT_NO_OUTCOME_OR_FORMAL_INPUT',
        'today':gate1c_first_git_summary(root,day.strftime('%Y%m%d'),now,verify),
        'previous_day':gate1c_first_git_summary(
            root,(day-timedelta(days=1)).strftime('%Y%m%d'),now,verify),
        'prospective_source_ready':{
            'today':gate1c_source_receipt_summary(root,day.strftime('%Y%m%d'),now,verify),
            'previous_day':gate1c_source_receipt_summary(
                root,(day-timedelta(days=1)).strftime('%Y%m%d'),now,verify)},
        'note':'First Git original SHA is an independently checked numerator, '
               'not a proven source-eligible denominator. No 99% claim until '
               'eligibility and exclusions are independently reconciled.'
    }


def write_if_changed(path,doc):
    encoded=json.dumps(doc,sort_keys=True,ensure_ascii=False,indent=2)+'\n'
    if path.exists() and path.read_text(encoding='utf-8')==encoded:return False
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(encoded,encoding='utf-8')
    return True

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',default='.');parser.add_argument('--at');parser.add_argument('--recovery-plan',action='store_true');parser.add_argument('--gate1c-proof',action='store_true')
    a=parser.parse_args();now=moment(a.at) if a.at else datetime.now(timezone.utc)
    if not now:raise SystemExit('INVALID_CLOCK')
    doc=compute(Path(a.root),now)
    if a.gate1c_proof:
        # The ordinary V220 read-only report owner publishes this alongside
        # current.json. Recovery dispatch never invokes a Git-history scan.
        report=gate1c_read_only_report(Path(a.root),now)
        output=Path(a.root)/'data/site_ops_v220/gate1c_current.json'
        changed=write_if_changed(output,report)
        print('V220_GATE1C_FIRST_GIT_COUNTS_ONLY '+json.dumps({
            'today':report['today']['first_git_original_sha_proven'],
            'previous_day':report['previous_day']['first_git_original_sha_proven'],
            'saved':changed, 'rate_proven':False},sort_keys=True))
    elif a.recovery_plan:
        print(json.dumps({'workflows':doc['recovery_dispatch_candidates']},sort_keys=True))
    else:
        output=Path(a.root)/'data/site_ops_v220/current.json'
        changed=write_if_changed(output,doc)
        print('V220_SITE_OPERATIONS '+json.dumps({'status':doc['status'],'issues':doc['issues'],'window':doc['decision_window_races'],
                  'next':doc['next_race'],'saved':changed,'recovery':doc['recovery_dispatch_candidates']},ensure_ascii=False))
if __name__=='__main__':main()
