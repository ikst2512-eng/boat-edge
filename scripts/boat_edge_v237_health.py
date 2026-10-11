#!/usr/bin/env python3
"""Read-only research health summary. No formal result access or production model edits."""
from __future__ import annotations
import argparse
import datetime as dt
import json
from pathlib import Path

UTC=dt.timezone.utc
JST=dt.timezone(dt.timedelta(hours=9))
SCHEMA='BOAT_EDGE_V237_SITE_SELF_DRIVE_HEALTH_V1'


def read(path):
    try:
        x=json.loads(path.read_text(encoding='utf-8'))
        return x if isinstance(x,dict) else None
    except (OSError,UnicodeError,ValueError):
        return None


def formal_guard(root):
    status=read(root/'data/formal_status.json') or {}
    flags=status.get('guards') or {}
    if any(flags.get(k) is not False for k in ('results_seen','unlock','scoring')) or flags.get('RESULT_UNLOCK_TOKEN') is not None:
        raise RuntimeError('V237_FORMAL_GATE_NOT_CLOSED')
    if (status.get('formalFirst100') or {}).get('races',0)!=0:
        raise RuntimeError('V237_FORMAL_FRESH_ACTIVE_NO_RESEARCH_REPORT')


def counter(x,field):
    v=(x or {}).get(field)
    return v if isinstance(v,int) and not isinstance(v,bool) and v>=0 else None


def build(root,now):
    formal_guard(root)
    day=now.astimezone(JST).strftime('%Y%m%d')
    p=root/'data/site_autopilot'
    pre=read(p/'v232_current.json') or {}
    acc=read(p/'v234_current.json') or {}
    compare_pre=read(p/'v236_pre_current.json') or {}
    compare=read(p/'v236_score_current.json') or {}
    wallet=read(root/'data/site_paper_sim/current.json') or {}
    money=wallet.get('money') or {}
    if pre.get('schema')!='BOAT_EDGE_V232_SITE_PROSPECTIVE_COHORT_SUMMARY_V1':
        raise RuntimeError('V237_V232_SOURCE_MISSING_OR_WRONG_SCHEMA')
    if acc.get('schema')!='BOAT_EDGE_V234_SITE_ONLY_ACCURACY_SUMMARY_V1':
        raise RuntimeError('V237_V234_SOURCE_MISSING_OR_WRONG_SCHEMA')
    if compare_pre.get('schema')!='BOAT_EDGE_V236_HITRATE_PRE_RESULT_SUMMARY_V1':
        raise RuntimeError('V237_V236_PRE_SOURCE_MISSING_OR_WRONG_SCHEMA')
    if compare.get('schema')!='BOAT_EDGE_V236_HITRATE_SCORE_SUMMARY_V1':
        raise RuntimeError('V237_V236_SCORE_SOURCE_MISSING_OR_WRONG_SCHEMA')
    n=counter(acc,'settled_verified_races')
    if n is None:raise RuntimeError('V237_SITE_SCORE_COUNT_INVALID')
    comparisons={}
    for mode in ('hit10','balance10','scenario7plus3','coverage15'):
        record=(compare.get('comparisons') or {}).get(mode)
        if not isinstance(record,dict):raise RuntimeError('V237_COMPARATOR_MISSING_'+mode)
        races=counter(record,'races');hit=counter(record,'hit')
        if races is None or hit is None or hit>races:raise RuntimeError('V237_INVALID_COMPARATOR_'+mode)
        comparisons[mode]={'races':races,'hits':hit,'points_average':record.get('avg_points'),
                           'hit_rate_percent':round(hit/races*100,2) if races else None}
    today_registered=counter(pre,'frozen_research_races_today') if pre.get('day_jst')==day else 0
    today_challengers=counter(compare_pre,'frozen_today') if compare_pre.get('day_jst')==day else 0
    if today_registered is None or today_challengers is None:raise RuntimeError('V237_COUNT_INVALID')
    values={
        'schema':SCHEMA,'scope':'SITE_ONLY_OPERATIONAL_MONITOR_NOT_FORMAL_FRESH',
        'day_jst':day,'as_of_jst':now.astimezone(JST).isoformat(),
        'current_reference':{'registered_today':today_registered,'registered_last_report_at':pre.get('checked_at'),
            'settled_total':n,'head_hits':counter(acc,'head_hit'),'top3_hits':counter(acc,'top3_hit'),
            'top5_hits':counter(acc,'top5_hit'),'top10_hits':counter(acc,'top10_hit'),
            'scored_last_report_at':acc.get('checked_at')},
        'research_candidates':{'pre_result_registered_today':today_challengers,
            'scored_total':counter(compare,'scored_total'),'comparisons':comparisons,
            'research_status':compare.get('status')},
        'simulator':{'daily_budget_yen':counter(money,'daily_budget_yen'),
            'today_spent_yen':counter(money,'today_spent_yen'),
            'today_paper_races':counter(money,'today_paper_races'),'virtual_only':money.get('virtual_only') is True},
        'formal_guard_closed':True,'formal_results_read_by_v237':False,
        'production_model_changed':False,'model_promotion_authorized':False,
        'accuracy_improvement_proven':False,'retrospective_experiment_is_not_proof':True,
        'no_new_forward_cohort_is_not_a_failure':True,
    }
    if values['research_candidates']['scored_total'] is None:raise RuntimeError('V237_SCORE_TOTAL_INVALID')
    if not values['simulator']['virtual_only']:raise RuntimeError('V237_SIMULATOR_NOT_VIRTUAL')
    if values['simulator']['today_spent_yen'] is None:raise RuntimeError('V237_BUDGET_SOURCE_MISSING')
    return values


def publish(root,now):
    row=build(root,now)
    path=root/'data/site_autopilot/v237_current.json'
    old=read(path)
    keys=[k for k in row if k!='as_of_jst']
    if old and all(old.get(k)==row.get(k) for k in keys):
        print('V237_HEALTH_NO_NEW_MEANINGFUL_STATE');return False
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(row,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print('V237_SITE_RESEARCH_HEALTH_WRITTEN',json.dumps({'registered_today':row['current_reference']['registered_today'],
          'settled':row['current_reference']['settled_total'],
          'forward_scored':row['research_candidates']['scored_total']},sort_keys=True));return True

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('.'))
    args=ap.parse_args()
    publish(args.root.resolve(),dt.datetime.now(UTC))
