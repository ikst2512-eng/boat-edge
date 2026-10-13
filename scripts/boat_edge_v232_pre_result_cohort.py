#!/usr/bin/env python3
"""V232: source-proven site-only prospective accuracy cohort, before race deadline.

Intentionally separate from the V214 raw-EV/betting shadow. A prediction can be
eligible for Top1-head, Top3, Top5, Top10 and 10-20x research without containing
any 'buy' recommendation. Does not open results, payouts, combined APIs or formal
predictions. No retrospective enrolment and no changes to production models.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import re

UTC=dt.timezone.utc
JST=dt.timezone(dt.timedelta(hours=9))
KEY=re.compile(r'^20\d{6}-\d{2}-\d{2}$')
SHA=re.compile(r'^[0-9a-f]{64}$')
COMBOS={f'{i}-{j}-{k}' for i in range(1,7) for j in range(1,7) for k in range(1,7) if len({i,j,k})==3}
SCHEMA='BOAT_EDGE_V232_SITE_PROSPECTIVE_ACCURACY_COHORT_V1'
SUMMARY_SCHEMA='BOAT_EDGE_V232_SITE_PROSPECTIVE_COHORT_SUMMARY_V1'


def read(path):
    try:
        d=json.loads(path.read_text(encoding='utf-8'))
        return d if isinstance(d,dict) else None
    except (OSError,UnicodeError,ValueError):return None


def stamp(v):
    try:
        d=dt.datetime.fromisoformat(str(v).replace('Z','+00:00'))
        return d.astimezone(UTC) if d.tzinfo else None
    except (TypeError,ValueError,OverflowError):return None


def digest(path):
    try:return hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError,ValueError):return None


def deadline(key, clock):
    if not KEY.fullmatch(key) or not re.fullmatch(r'\d{2}:\d{2}',str(clock)):return None
    try:return dt.datetime.strptime(key[:8]+clock,'%Y%m%d%H:%M').replace(tzinfo=JST).astimezone(UTC)
    except ValueError:return None


def age(newer,older,max_sec):
    return newer is not None and older is not None and 0 <= (newer-older).total_seconds() <= max_sec


def formal_guard(root):
    d=read(root/'data/formal_status.json') or {}
    g=d.get('guards') or {}
    if not all(g.get(k) is False for k in ('results_seen','unlock','scoring')) or g.get('RESULT_UNLOCK_TOKEN') is not None:
        raise RuntimeError('V232_FORMAL_GUARD_NOT_CLOSED')
    if (d.get('formalFirst100') or {}).get('races',0):
        raise RuntimeError('V232_FORMAL_FRESH_IN_PROGRESS_NO_SITE_RESEARCH_FREEZE')


def verified(root,key,now):
    """Return frozen source-bound observation, or an explicit reason; never repair/backfill."""
    if not KEY.fullmatch(key):return None,'invalid_key'
    path=root/'data/site_prediction_snapshots'/f'{key}.json'
    s=read(path)
    if s is None:return None,'snapshot_missing_or_invalid'
    if s.get('race_key')!=key or s.get('prediction_kind')!='SITE_REFERENCE_V122' or s.get('snapshot_window')!='FINAL_15M':
        return None,'not_site_reference_final'
    if any((s.get('guards') or {}).get(n) is not False for n in ('results_seen','unlock','scoring')):
        return None,'result_guard_not_closed'
    saved=stamp(s.get('saved_at')); first=stamp(s.get('first_saved_at'))
    due=deadline(key,s.get('deadline'))
    if not saved or not due or not first or not age(saved,first,10):return None,'snapshot_clock_invalid'
    if not (120 <= (due-now).total_seconds() <= 900):return None,'not_prospectively_in_window'
    if not (120 <= (due-saved).total_seconds() <= 900) or not age(now,saved,600):
        return None,'snapshot_outside_evidence_window'
    snapsha=digest(path)
    audit_path=root/'data/site_prediction_audit'/f'{key}.json'
    a=read(audit_path) or {}
    first_audited=stamp(a.get('first_audited_at'))
    if audit_path.exists():
        if (a.get('pass') is not True or a.get('latest_snapshot_sha256')!=snapsha
                or first_audited is None or not (saved <= first_audited <= now < due)):
            return None,'sha_audit_missing_or_late'
        audit_type='V125_VERIFIED_AT_PRE_RESULT'
    else:
        # Do NOT fabricate a V125 audit. Capture a separate contemporaneous
        # V232 proof from source bytes below, before the actual deadline.
        audit_type='V232_SELF_CONTAINED_SHA_AND_SOURCE_PRE_RESULT'
    race_path=root/'data/races'/f'{key}.json'
    race=read(race_path) or {}
    meta=race.get('meta') or {}
    if (race.get('race_key')!=key or meta.get('phase')!='PRE_RESULT'
            or any(meta.get(n) is not False for n in ('results_seen','unlock','scoring'))
            or len(race.get('racers') or [])!=6):
        return None,'race_pre_result_or_six_boats_unverified'
    if digest(race_path)!=s.get('race_sha256'):
        # A later race-card revision is possible, but there is no saved-time
        # race-card archive in this version: do not infer unchanged provenance.
        return None,'race_bytes_changed_since_prediction'
    for source,limit in (('race_card',960),('beforeinfo',900)):
        row=(race.get('source_audit') or {}).get(source) or {}
        if row.get('status')!='ok' or not age(saved,stamp(row.get('fetched_at')),limit):
            return None,source+'_not_fresh_at_prediction'
    scratch_path=root/'data/site_scratches_v182'/f'{key}.json'
    scratch=read(scratch_path) or {}
    if (scratch.get('race_key')!=key or scratch.get('blocked') is not False
            or scratch.get('race_card_source_status')!='ok'
            or scratch.get('official_beforeinfo_source_status')!='ok'
            or not age(saved,stamp(scratch.get('checked_at')),900)):
        return None,'scratch_not_certified_before_prediction'
    osha=s.get('odds_sha256')
    if not isinstance(osha,str) or not SHA.fullmatch(osha):return None,'odds_source_sha_missing'
    side=root/'data/site_prediction_snapshots/odds_v214'/f'{key}-{osha}.json'
    if not side.is_file() or digest(side)!=osha:return None,'odds_sidecar_missing_or_modified'
    odds=read(side) or {}
    points=odds.get('trifecta_odds') or {}
    if (odds.get('race_key')!=key or odds.get('phase')!='PRE_RESULT_PURCHASE_ONLY'
            or not age(saved,stamp(odds.get('fetched_at')),900) or not isinstance(points,dict)
            or set(points)!=COMBOS or any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in points.values())):
        return None,'odds_board_not_120_healthy_at_prediction'
    modes=s.get('modes') or {};freeze_modes={}
    if s.get('stake_plan_version')!='V141-10000-PROSPECTIVE':return None,'stake_plan_not_prospectively_saved'
    for mode in ('hit','balance','hole','narrow'):
        rows=(modes.get(mode) or {}).get('tickets')
        if not isinstance(rows,list) or not rows or len(rows)>25:return None,'invalid_mode_'+mode
        selected=[];seen=set();total=0
        for row in rows:
            if not isinstance(row,dict):return None,'invalid_ticket_'+mode
            combo=row.get('combo');p=row.get('p');n=row.get('stake_yen');o=row.get('odds')
            if (combo not in COMBOS or combo in seen or type(p) not in (int,float)
                    or not math.isfinite(p) or p<=0 or p>=100 or type(n) is not int or n<0 or n%100
                    or type(o) not in (int,float) or not math.isfinite(o)
                    or abs(o-points[combo])>0.05):return None,'ticket_not_source_bound_'+mode
            seen.add(combo);total+=n
            selected.append({'combo':combo,'p_raw_percent':round(float(p),6),'odds_at_freeze':float(o),'stake_yen':n})
        if total!=10000:return None,'stake_not_10000_'+mode
        freeze_modes[mode]=selected
    hit=freeze_modes['hit']
    ranked=sorted(hit,key=lambda x:(-x['p_raw_percent'],x['combo']))
    if [x['combo'] for x in hit]!=[x['combo'] for x in ranked]:return None,'hit_not_probability_ranked'
    top=[x['combo'] for x in hit]
    band=[x['combo'] for x in hit if 10<=x['odds_at_freeze']<=20]
    if len(top)<10:return None,'top10_not_present'
    return {
        'schema':SCHEMA,'scope':'SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH',
        'race_key':key,'venue':s.get('venue'),'deadline_jst':due.astimezone(JST).isoformat(),
        'snapshot_saved_at':saved.isoformat(),'evidence_committed_at':now.isoformat(),
        'snapshot_sha256':snapsha,'audit_evidence_type':audit_type,
        'source_race_sha256':s['race_sha256'],
        'source_scratch_sha256':digest(scratch_path),'odds_source_sha256':osha,
        'odds_combinations_verified':120,
        'model_id':s.get('prediction_kind'),'selection_policy':s.get('selection_policy'),
        'head_top1':top[0].split('-')[0],
        'top3':top[:3],'top5':top[:5],'top10':top[:10],
        'top10_10_to_20x_at_freeze':band,
        'frozen_mode_tickets':freeze_modes,
        'scoring_status':'PRE_RESULT_AWAITING_FUTURE_SITE_ONLY_SETTLEMENT',
        'formal_results_seen':False,'formal_gate_unlocked':False,
        'production_accuracy_claim':'NOT_PROVEN',
        'paper_purchases_authorized':False,'real_purchases_authorized':False,
    },None


def collect(root,now):
    root=root.resolve();now=now.astimezone(UTC)
    formal_guard(root)
    date=now.astimezone(JST).strftime('%Y%m%d')
    base=root/'data/site_autopilot/v232_cohort'
    valid=[];excluded={};window=0
    snapshot_counts={'total':0,'missing_deadline':0,'before_window':0,'after_window':0}
    for s in sorted((root/'data/site_prediction_snapshots').glob(date+'-??-??.json')):
        key=s.stem
        x=read(s) or {};due=deadline(key,x.get('deadline'))
        snapshot_counts['total']+=1
        if due is None:
            snapshot_counts['missing_deadline']+=1;continue
        seconds=(due-now).total_seconds()
        if seconds>900:
            snapshot_counts['before_window']+=1;continue
        if seconds<120:
            snapshot_counts['after_window']+=1;continue
        window+=1
        if (base/f'{key}.json').is_file():continue
        obs,why=verified(root,key,now)
        if obs:valid.append((key,obs))
        else:excluded[why]=excluded.get(why,0)+1
    # Validate all prospective rows before writing any.
    base.mkdir(parents=True,exist_ok=True)
    for key,obs in valid:
        with (base/f'{key}.json').open('x',encoding='utf-8') as f:
            f.write(json.dumps(obs,sort_keys=True,ensure_ascii=False,indent=2)+'\n')
    all_today=sorted(base.glob(date+'-??-??.json'))
    payload={'schema':SUMMARY_SCHEMA,'scope':'FROZEN_SITE_ONLY_RESEARCH_NO_RESULT_READ',
       'day_jst':date,'checked_at':now.isoformat(),
       'frozen_research_races_today':len(all_today),
       'new_research_races_this_run':len(valid),
       'current_prediction_window_races':window,
       'snapshot_window_diagnostic':snapshot_counts,
       'not_eligible_reasons':excluded,
       'frozen_races':[
          {'race_key':k,'venue':d.get('venue'),'saved_at':d.get('snapshot_saved_at'),
           'top1_head':d.get('head_top1'),'top10_10_20x_candidates':len(d.get('top10_10_to_20x_at_freeze') or [])}
          for p in all_today if (d:=read(p)) and (k:=d.get('race_key'))],
       'accuracy_improvement_proven':False,'formal_scoring_unlocked':False,
       'real_or_paper_wagers_placed':0,
       'explanation':'Pre-result frozen evidence for independent Top1 head, Top3/5/10 and odds-band scoring. NOT a betting/ROI claim.'}
    report=root/'data/site_autopilot/v232_current.json'
    old=read(report) or {}
    cmp_keys=['frozen_research_races_today','current_prediction_window_races','snapshot_window_diagnostic','not_eligible_reasons','frozen_races']
    new_total=len(valid)>0 or any(old.get(k)!=payload.get(k) for k in cmp_keys) or old.get('day_jst')!=date
    if new_total or not report.is_file():
        report.parent.mkdir(parents=True,exist_ok=True)
        report.write_text(json.dumps(payload,sort_keys=True,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('V232_PRE_RESULT_SITE_COHORT',json.dumps({'date':date,'new':len(valid),'total':len(all_today),
          'in_window':window,'snapshot_diagnostic':snapshot_counts,'rejected':excluded,'saved_report':new_total},ensure_ascii=False,sort_keys=True))
    return payload

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--now')
    a=p.parse_args();now=stamp(a.now) if a.now else dt.datetime.now(UTC)
    if now is None:raise SystemExit('V232_INVALID_CLOCK')
    collect(a.root,now)
