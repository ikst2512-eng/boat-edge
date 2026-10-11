#!/usr/bin/env python3
"""BOAT EDGE V227: pre-result site-health and validated-model status only.

Explicitly does not open data/results, formal target manifests, payout data,
combined APIs, or implement model/paper-money promotion. It records evidence.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import re

JST = dt.timezone(dt.timedelta(hours=9))
UTC = dt.timezone.utc
KEY = re.compile(r'^20\d{6}-\d{2}-\d{2}$')
COMBOS = {f'{a}-{b}-{c}' for a in range(1,7) for b in range(1,7) for c in range(1,7) if a!=b and a!=c and b!=c}
SCHEMA = 'BOAT_EDGE_V227_SITE_AI_SELF_DRIVE_STATUS_V1'


def get(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError, UnicodeError):
        return None


def instant(value):
    try:
        v=dt.datetime.fromisoformat(str(value).replace('Z','+00:00'))
        return v.astimezone(UTC) if v.tzinfo else None
    except (TypeError, ValueError, OverflowError):
        return None


def fresh(value, now, minutes):
    at=instant(value)
    return at is not None and 0 <= (now-at).total_seconds() <= minutes*60


def deadline(key, clock):
    if not KEY.fullmatch(str(key)) or not re.fullmatch(r'\d{2}:\d{2}',str(clock)):
        return None
    try:
        return dt.datetime.strptime(key[:8]+clock, '%Y%m%d%H:%M').replace(tzinfo=JST).astimezone(UTC)
    except ValueError:
        return None


def risk(root,key,now):
    race=get(root/'data/races'/f'{key}.json') or {}
    audit=race.get('source_audit') or {}
    card=audit.get('race_card') or {}
    before=audit.get('beforeinfo') or {}
    scratch=get(root/'data/site_scratches_v182'/f'{key}.json') or {}
    odds=get(root/'data/site_odds'/f'{key}.json') or {}
    snap_path=root/'data/site_prediction_snapshots'/f'{key}.json'
    snap=get(snap_path) or {}
    gaps=[]
    meta=race.get('meta') or {}
    if meta.get('phase')!='PRE_RESULT' or any(meta.get(g) is not False for g in ('results_seen','unlock','scoring')):
        gaps.append('PRE_RESULT未確認')
    if len(race.get('racers') or [])!=6:
        gaps.append('6艇未確認')
    if card.get('status')!='ok' or not fresh(card.get('fetched_at'),now,16):
        gaps.append('出走表期限切れ')
    if before.get('status')!='ok' or not fresh(before.get('fetched_at'),now,15):
        gaps.append('直前情報未取得または期限切れ')
    if (scratch.get('race_key')!=key or scratch.get('blocked') is not False
            or scratch.get('race_card_source_status')!='ok'
            or scratch.get('official_beforeinfo_source_status')!='ok'
            or not fresh(scratch.get('checked_at'),now,15)):
        gaps.append('欠場照合未確認')
    o=odds.get('trifecta_odds') or {}
    if (odds.get('race_key')!=key or odds.get('phase')!='PRE_RESULT_PURCHASE_ONLY'
            or not fresh(odds.get('fetched_at'),now,15)
            or set(o)!=COMBOS or any(not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) or v<=0 for v in o.values())):
        gaps.append('最新オッズ120通り未確認')
    if (snap.get('race_key')!=key or snap.get('snapshot_window')!='FINAL_15M'
            or not snap.get('odds_sha256')):
        gaps.append('締切前予想未保存')
    else:
        a=get(root/'data/site_prediction_audit'/f'{key}.json') or {}
        if (a.get('pass') is not True or a.get('latest_snapshot_sha256')!=hashlib.sha256(snap_path.read_bytes()).hexdigest()):
            gaps.append('予想SHA監査未一致')
    return gaps


def summary(root,now):
    now=now.astimezone(UTC)
    today=now.astimezone(JST).strftime('%Y%m%d')
    site=get(root/'data/site_ops_v220/current.json') or {}
    readiness=get(root/'data/site_paper_sim/readiness_v215_current.json') or {}
    paper=get(root/'data/site_paper_sim/current.json') or {}
    validation=get(root/'data/site_autovalidation/current.json') or {}
    parity=get(root/'data/site_odds/verification_v167.json') or {}
    formal=get(root/'data/formal_status.json') or {}
    schedule=get(root/'data/today.json') or {}
    safe_schedule=str(schedule.get('date') or '').replace('-','')==today
    races=[]
    if safe_schedule:
        for venue in schedule.get('venues') or []:
            for rec in venue.get('races') or []:
                key=rec.get('race_key')
                end=deadline(key,rec.get('deadline'))
                if not end or not key.startswith(today+'-'):continue
                left=(end-now).total_seconds()/60
                if 0<=left<=15:
                    races.append({'race_key':key,'venue':venue.get('venue'),'deadline_jst':end.astimezone(JST).strftime('%H:%M'),
                                  'minutes_left':round(left,1),'issues':risk(root,key,now)})
    races.sort(key=lambda x:(x['minutes_left'],x['race_key']))
    eng=(root/'scripts/site_final_history_v133.py')
    try:
        engine=eng.read_text(encoding='utf-8')
        source_guarded=all(engine.count(marker)==1 for marker in (
            'V226_IMMUTABLE_ORIGINAL_SNAPSHOT','V226_SOURCE_GUARD',
            'V226_DECISION_WINDOW','V226_ODDS_GUARD'))
    except (OSError,UnicodeError):
        source_guarded=False
    now_snap=root/'data/site_prediction_snapshots'
    count_today=sum(1 for _ in now_snap.glob(f'{today}-??-??.json'))
    current_v185=validation.get('site_v185') or {}
    current_v199=validation.get('site_v199') or {}
    m=paper.get('money') or {}
    formal_guard=formal.get('guards') or {}
    formal_closed=(all(formal_guard.get(k) is False for k in ('results_seen','unlock','scoring'))
                   and formal_guard.get('RESULT_UNLOCK_TOKEN') is None)
    return {
        'schema':SCHEMA,'scope':'SITE_DIAGNOSTICS_ONLY_NO_FORMAL_RESULT_OR_PAYOUT_READ',
        'day_jst':today,'checked_at':now.isoformat(),
        'site':{'schedule_today':safe_schedule,'status':site.get('status','UNVERIFIED'),
            'v226_source_guard_active':source_guarded,'snapshot_files_today':count_today,
            'readiness_observed_races':readiness.get('day_observed_races',0) if readiness.get('day_jst')==today else 0,
            'readiness_shadow_verified_races':readiness.get('day_verified_races',0) if readiness.get('day_jst')==today else 0,
            'readiness_reasons':readiness.get('day_latest_reasons',{}) if readiness.get('day_jst')==today else {},
            'current_window':races[:12],
            'live_odds_parity_status':parity.get('status','NOT_VERIFIED'),
            'collector_health_issues':site.get('issues',[])},
        'prediction':{'production_improvement_proven':False,
            'evidence_claim':validation.get('performance_claim','NOT_PROVEN'),
            'site_v185_evaluated_races':current_v185.get('verified_races',0),
            'site_v199_evaluated_races':current_v199.get('verified_races',0),
            'site_v185_10_20x_settled_races':current_v185.get('confirmed_payout_10_20x_races',0),
            'site_v199_10_20x_settled_races':current_v199.get('confirmed_payout_10_20x_races',0),
            'site_v185_candidate_top':(((current_v185.get('candidate_comparisons') or {}).get('candidate') or {}).get('all_races') or {}),
            'site_v199_head_top':(((current_v199.get('candidate_comparisons') or {}).get('head') or {}).get('all_races') or {}),
            'site_v199_head_top1':((((current_v199.get('candidate_comparisons') or {}).get('head') or {}).get('all_races') or {}).get('top1_head') or {}),
            'model_auto_promotion':False},
        'paper':{'mode':paper.get('mode','NOT_AVAILABLE'),'calibration_status':paper.get('calibration_status','NOT_AVAILABLE'),
            'daily_budget_yen':m.get('daily_budget_yen'),'spent_yen':m.get('today_spent_yen'),
            'balance_yen':m.get('balance_yen'),'buy_races':m.get('today_paper_races',0),
            'real_purchases_enabled':False},
        'formal':{'guard_closed':formal_closed,'first100_frozen':(formal.get('formalFirst100') or {}).get('races'),
            'auto_unlock':False,'results_read_by_v227':False,'scoring_by_v227':False},
        'follow_up_order':['直前公式データと欠場照合','締切前スナップショットの保存とSHA監査',
          'A頭・Top3/5/10・10〜20倍帯の未見比較','証明済みモデルだけ本番候補','Pagesと画面の回帰確認'],
        'not_accuracy_or_return_guarantee':True,
    }


def run(root,now):
    out=root/'data/site_autopilot/v227_current.json'
    new=summary(root,now)
    old=get(out) or {}
    meaningful={k:v for k,v in new.items() if k!='checked_at'}!={k:v for k,v in old.items() if k!='checked_at'}
    last=instant(old.get('checked_at'))
    # Bound write frequency: don't churn pages for a heartbeat without changed evidence.
    if meaningful or last is None or (now.astimezone(UTC)-last).total_seconds()>=30*60:
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(new,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
        saved=True
    else:
        saved=False
    print('V227_SITE_AI_PROSPECTIVE_STATUS',json.dumps({'saved':saved,'site':new['site']['status'],
        'observed':new['site']['readiness_observed_races'],'verified':new['site']['readiness_shadow_verified_races'],
        'paper_spent':new['paper']['spent_yen'],'prediction_proven':new['prediction']['production_improvement_proven'],
        'formal_closed':new['formal']['guard_closed']},ensure_ascii=False,sort_keys=True))
    return new,saved


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--now')
    args=p.parse_args()
    n=instant(args.now) if args.now else dt.datetime.now(UTC)
    if n is None:raise SystemExit('INVALID_CLOCK')
    run(Path(args.root),n)
