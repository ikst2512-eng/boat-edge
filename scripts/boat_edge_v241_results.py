#!/usr/bin/env python3
"""V241 site-only verified result board. Never queries endpoints or alters picks."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit, parse_qs

KEY = re.compile(r'^20\d{6}-\d{2}-\d{2}$')
TRIPLE = re.compile(r'^[1-6]-[1-6]-[1-6]$')
V234='BOAT_EDGE_V234_PRECOMMITTED_SITE_ONLY_RESULT_SCORE_V1'
V232='BOAT_EDGE_V232_SITE_PROSPECTIVE_ACCURACY_COHORT_V1'
OUTPUT_SCHEMA='BOAT_EDGE_V241_VERIFIED_SITE_RESULTS_V1'
MODES=('hit','balance','hole','narrow')
BASE=Path('data/site_autopilot')

def read(path):
    v=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(v,dict):raise ValueError('NOT_A_JSON_OBJECT')
    return v

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def timestamp(v):
    d=dt.datetime.fromisoformat(str(v).replace('Z','+00:00'))
    if not d.tzinfo:raise ValueError('TIMEZONE_MISSING')
    return d.astimezone(dt.timezone.utc)
def valid_combo(s):return isinstance(s,str) and bool(TRIPLE.fullmatch(s)) and len(set(s.split('-')))==3

def git_first(root,path):
    rel=path.relative_to(root).as_posix()
    p=subprocess.run(['git','log','--diff-filter=A','--reverse','--format=%H|%cI','--',rel],cwd=root,capture_output=True,text=True,check=True)
    if not p.stdout.strip():raise ValueError('NO_GIT_FIRST_COMMIT')
    commit,stamp=p.stdout.splitlines()[0].split('|',1)
    saved=subprocess.run(['git','show',f'{commit}:{rel}'],cwd=root,capture_output=True,check=True)
    if hashlib.sha256(saved.stdout).hexdigest()!=sha(path):raise ValueError('GIT_FIRST_CONTENT_CHANGED')
    return commit,timestamp(stamp)

def check_formal_guard(root):
    formal=read(root/'data/formal_status.json')
    guard=formal.get('guards',{})
    if not isinstance(guard,dict) or any(guard.get(k) is not False for k in ('results_seen','unlock','scoring')) or guard.get('RESULT_UNLOCK_TOKEN') is not None or (formal.get('formalFirst100') or {}).get('races')!=0:
        raise ValueError('FORMAL_FRESH_GATE_OPEN_STOP')

def examine(root,scored):
    key=scored.stem
    if not KEY.fullmatch(key):raise ValueError('BAD_RACE_KEY')
    result=read(scored)
    if result.get('schema')!=V234 or result.get('scope')!='POST_RESULT_SITE_RESEARCH_ONLY_FORMAL_FRESH_LOCKED' or result.get('race_key')!=key:raise ValueError('INVALID_SITE_ONLY_SCORE')
    frozen=root/BASE/'v232_cohort'/scored.name
    original=read(frozen)
    if original.get('schema')!=V232 or original.get('scope')!='SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH' or original.get('race_key')!=key or result.get('cohort_sha256')!=sha(frozen):raise ValueError('INVALID_PRECOMMITTED_COHORT')
    if any(original.get(k) is not False for k in ('formal_results_seen','formal_gate_unlocked','paper_purchases_authorized','real_purchases_authorized')):raise ValueError('COHORT_NOT_BLIND')
    if original.get('model_id')!=result.get('model_id'):raise ValueError('MODEL_MISMATCH')
    if result.get('real_or_paper_wagers_placed')!=0 or result.get('model_promotion_authorized') is not False:raise ValueError('SITE_RESEARCH_ONLY')
    due=timestamp(original['deadline_jst'])
    if due!=timestamp(result['deadline_jst']):raise ValueError('DEADLINE_CHANGED')
    first_id,first_at=git_first(root,frozen)
    if first_at>=due or first_id!=result.get('first_git_commit') or abs((first_at-timestamp(result['first_git_committed_at'])).total_seconds())>2:raise ValueError('NO_VERIFIED_PREDEADLINE_FREEZE')
    if timestamp(result['result_fetched_at'])<=due:raise ValueError('RESULT_TOO_EARLY')
    result_commit,result_commit_at=git_first(root,scored)
    if result_commit_at<=due:raise ValueError('POST_RESULT_NOT_COMMITTED_AFTER_DEADLINE')
    venue_code=key.split('-')[1];round_no=int(key.split('-')[2]);date=key[:8]
    source=urlsplit(str(result.get('result_source') or ''))
    if source.scheme!='https' or source.netloc!='www.boatrace.jp' or source.path!='/owpc/pc/race/raceresult' or parse_qs(source.query)!={'hd':[date],'jcd':[venue_code],'rno':[str(round_no)]}:raise ValueError('RESULT_SOURCE_MISMATCH')
    combo=result.get('winning_combo')
    if not valid_combo(combo):raise ValueError('BAD_WINNING_ORDER')
    if str(result.get('actual_head'))!=combo[0] or bool(result['head_hit'])!=(str(original['head_top1'])==combo[0]):raise ValueError('HEAD_PARITY_INVALID')
    tickets=original.get('frozen_mode_tickets') or {}
    payout=result.get('official_payout_per_100_yen')
    if not isinstance(payout,int) or payout<=0:raise ValueError('OFFICIAL_PAYOUT_INVALID')
    mode_outcomes={}
    for mode in MODES:
        bets=tickets.get(mode)
        scored_mode=(result.get('modes') or {}).get(mode)
        if not isinstance(bets,list) or not isinstance(scored_mode,dict):raise ValueError('MODE_MISSING')
        combos=[b.get('combo') for b in bets]
        if len(set(combos))!=len(combos) or any(not valid_combo(c) for c in combos):raise ValueError('MODE_DUPLICATE_OR_INVALID')
        stakes=[b.get('stake_yen') for b in bets]
        if any(not isinstance(s,int) or s<0 or s%100 for s in stakes):raise ValueError('BAD_FROZEN_STAKE')
        spent=sum(stakes)
        if spent!=10000 or scored_mode.get('frozen_stake_yen')!=spent or scored_mode.get('tickets')!=len(combos):raise ValueError('MODE_TICKETS_OR_STAKE_MISMATCH')
        hit=combo in combos
        winstake=next((b['stake_yen'] for b in bets if b['combo']==combo),0)
        returned=payout*winstake//100
        if hit!=scored_mode.get('hit') or returned!=scored_mode.get('hypothetical_return_yen'):raise ValueError('MODE_RETURN_PARITY_FAILED')
        mode_outcomes[mode]={'hit':hit,'tickets':len(combos),'stake_yen':spent,'winning_ticket_stake_yen':winstake,'hypothetical_return_yen':returned,'hypothetical_profit_yen':returned-spent}
    if bool(result.get('top10_hit'))!=mode_outcomes['hit']['hit'] or result.get('top3_hit')!=(combo in original.get('top3',[])) or result.get('top5_hit')!=(combo in original.get('top5',[])):raise ValueError('TOP_N_PARITY_MISMATCH')
    return {'race_key':key,'date_jst':date,'venue':result['venue'],'venue_code':venue_code,'round':round_no,
            'deadline_jst':result['deadline_jst'],'winning_combo':combo,'official_payout_per_100_yen':payout,'official_odds':round(payout/100,2),
            'head_prediction':str(original['head_top1']),'head_hit':bool(result['head_hit']),
            'top3_hit':bool(result['top3_hit']),'top5_hit':bool(result['top5_hit']),'top10_hit':bool(result['top10_hit']),
            'mode_outcomes':mode_outcomes,'model_id':result['model_id'],'result_source':result['result_source'],
            'precommitted_sha256':sha(frozen),'score_sha256':sha(scored),'first_frozen_commit':first_id,
            'first_score_commit':result_commit,'post_result_verified':True}

def build(root:Path):
    root=root.resolve()
    check_formal_guard(root)
    source=root/BASE/'v234_scored'
    items=[examine(root,p) for p in sorted(source.glob('20??????-??-??.json'))]
    items.sort(key=lambda x:(timestamp(x['deadline_jst']),x['race_key']),reverse=True)
    n=len(items); wins=sum(x['top10_hit'] for x in items);heads=sum(x['head_hit'] for x in items)
    by_day={}
    for x in items:
        d=by_day.setdefault(x['date_jst'],{'date_jst':x['date_jst'],'settled_races':0,'top10_hits':0,'head_hits':0,'hypothetical_stake_yen':0,'hypothetical_return_yen':0})
        d['settled_races']+=1;d['top10_hits']+=x['top10_hit'];d['head_hits']+=x['head_hit']
        d['hypothetical_stake_yen']+=x['mode_outcomes']['hit']['stake_yen'];d['hypothetical_return_yen']+=x['mode_outcomes']['hit']['hypothetical_return_yen']
    summary={'schema':OUTPUT_SCHEMA,'scope':'VERIFIED_POST_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH','status':'HISTORICAL_SITE_ONLY_NOT_REAL_BETTING',
             'settled_verified_races':n,'top10_hits':wins,'head_hits':heads,'top3_hits':sum(x['top3_hit'] for x in items),'top5_hits':sum(x['top5_hit'] for x in items),
             'top10_hit_rate_percent':round(100*wins/n,2) if n else None,'hypothetical_stake_yen':sum(d['hypothetical_stake_yen'] for d in by_day.values()),
             'hypothetical_return_yen':sum(d['hypothetical_return_yen'] for d in by_day.values()),
             'date_latest':max(by_day,default=None),'by_day':[by_day[d] for d in sorted(by_day,reverse=True)],
             'rows':items,'formal_result_access':False,'production_model_changed':False,'accuracy_improvement_proven':False,'real_or_paper_wagers_placed':0}
    # Deterministic bytes: no wall-clock timestamps or build hash/unstable ordering.
    return summary

def main():
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--root',default='.');args=a.parse_args()
    root=Path(args.root).resolve();report=build(root)
    path=root/BASE/'v241_results_current.json';path.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+'\n'
    if not path.exists() or path.read_text(encoding='utf-8')!=text:path.write_text(text,encoding='utf-8')
    print(f'V241_SITE_VERIFIED_RESULTS_PUBLISHED rows={report["settled_verified_races"]} top10={report["top10_hits"]} latest={report["date_latest"]}')

if __name__=='__main__':main()
