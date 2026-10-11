#!/usr/bin/env python3
"""V234 independent retrospective scoring ONLY for pre-committed site-only V232 cohorts.

Never reads formal Fresh targets, combined endpoints, or unfrozen prediction data.
PRE_RESULT collection is in a separate workflow step before THIS scorer runs.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit, parse_qs

UTC=dt.timezone.utc
JST=dt.timezone(dt.timedelta(hours=9))
KEY=re.compile(r'^20\d{6}-\d{2}-\d{2}$')
COMBOS={f'{a}-{b}-{c}' for a in range(1,7) for b in range(1,7) for c in range(1,7) if len({a,b,c})==3}
FROZEN_SCHEMA='BOAT_EDGE_V232_SITE_PROSPECTIVE_ACCURACY_COHORT_V1'
SCORE_SCHEMA='BOAT_EDGE_V234_PRECOMMITTED_SITE_ONLY_RESULT_SCORE_V1'
SUMMARY_SCHEMA='BOAT_EDGE_V234_SITE_ONLY_ACCURACY_SUMMARY_V1'

def read(path):
    try:
        x=json.loads(path.read_text(encoding='utf-8'))
        return x if isinstance(x,dict) else None
    except (ValueError, UnicodeError, OSError):return None

def write_once(path,item):
    blob=(json.dumps(item,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=blob:raise RuntimeError('V234_EXISTING_SETTLED_ROW_IMMUTABLE_'+path.stem)
        return False
    path.write_bytes(blob)
    return True

def time(v):
    try:
        x=dt.datetime.fromisoformat(str(v).replace('Z','+00:00'))
        return x.astimezone(UTC) if x.tzinfo else None
    except (ValueError, TypeError, OverflowError):return None

def sha(path):
    try:return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:return None

def git_creation(root,path):
    rel=path.relative_to(root).as_posix()
    # The first Git commit which introduced THIS file is independent evidence that
    # the frozen bytes existed before the race. No retroactive date assumption.
    p=subprocess.run(['git','log','--diff-filter=A','--reverse','--format=%H|%cI','--',rel],cwd=root,
                     capture_output=True,text=True,check=False)
    if p.returncode or not p.stdout.strip():return None,None
    row=p.stdout.strip().splitlines()[0]
    commit,when=row.split('|',1)
    created=time(when)
    if not created:return None,None
    original=subprocess.run(['git','show',f'{commit}:{rel}'],cwd=root,capture_output=True,check=False)
    if original.returncode or hashlib.sha256(original.stdout).hexdigest()!=sha(path):return None,None
    return commit,created

def guard(root):
    formal=read(root/'data/formal_status.json') or {}
    g=formal.get('guards') or {}
    if not (g.get('results_seen') is False and g.get('unlock') is False
            and g.get('scoring') is False and g.get('RESULT_UNLOCK_TOKEN') is None
            and not (formal.get('formalFirst100') or {}).get('races')):
        raise RuntimeError('V234_FORMAL_FRESH_GUARD_NOT_CLOSED')

def verify_frozen(root,path,now):
    key=path.stem
    d=read(path)
    if not KEY.fullmatch(key) or d is None or d.get('race_key')!=key:return None,'invalid_frozen_row'
    if d.get('schema')!=FROZEN_SCHEMA or d.get('scope')!='SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH':
        return None,'not_v232_site_only'
    due=time(d.get('deadline_jst')); saved=time(d.get('snapshot_saved_at'))
    observed=time(d.get('evidence_committed_at'))
    if not due or not saved or not observed or not saved<=observed<due:
        return None,'invalid_pre_result_time'
    if now<due+dt.timedelta(minutes=2):return None,'race_not_over'
    commit,committed=git_creation(root,path)
    if not commit or not saved<=committed<due:return None,'no_pre_deadline_git_commit_or_mutated_proof'
    if d.get('formal_results_seen') is not False or d.get('formal_gate_unlocked') is not False:
        return None,'formal_guard_on_cohort'
    if d.get('model_id')!='SITE_REFERENCE_V122' or d.get('real_purchases_authorized') is not False or d.get('paper_purchases_authorized') is not False:
        return None,'unexpected_model_or_purchase'
    top=d.get('top10'); t3=d.get('top3'); t5=d.get('top5'); band=d.get('top10_10_to_20x_at_freeze')
    if not isinstance(top,list) or len(top)!=10 or len(set(top))!=10 or set(top)-COMBOS:
        return None,'invalid_top10'
    if t3!=top[:3] or t5!=top[:5] or not isinstance(band,list) or set(band)-set(top) or len(set(band))!=len(band):
        return None,'bad_top_or_odds_band'
    if str(d.get('head_top1'))!=top[0][0]:return None,'invalid_head'
    if d.get('odds_combinations_verified')!=120:return None,'unverified_odds_at_freeze'
    modes=d.get('frozen_mode_tickets') or {}
    for name in ('hit','balance','hole','narrow'):
        rows=modes.get(name)
        if not isinstance(rows,list) or not rows or len(rows)>25:return None,'invalid_frozen_mode'
        amounts=[];seen=set()
        for r in rows:
            if not isinstance(r,dict) or r.get('combo') not in COMBOS or r['combo'] in seen:
                return None,'invalid_frozen_ticket'
            seen.add(r['combo']);stake=r.get('stake_yen');odds=r.get('odds_at_freeze')
            if type(stake)!=int or stake<0 or stake%100 or not isinstance(odds,(int,float)) or odds<=0:
                return None,'invalid_ticket_allocation'
            amounts.append(stake)
            if name=='hit' and r['combo'] in band and not 10<=odds<=20:
                return None,'band_odds_not_source_bound'
        if sum(amounts)!=10000:return None,'not_ten_thousand_yen_frozen'
        if name=='hit' and [r['combo'] for r in rows]!=top:return None,'top10_not_matching_frozen_tickets'
    expected_band=[r['combo'] for r in modes['hit'] if 10<=r['odds_at_freeze']<=20]
    if expected_band!=band:return None,'band_not_exact_from_odds'
    return (d,due,commit,committed),None

def verify_result(root,key,due,committed):
    p=root/'data/site_results'/f'{key}.json'
    r=read(p)
    if not r:return None,'confirmed_site_result_not_yet_available'
    if r.get('schema_version')!='boat-edge-site-result-v109' or r.get('race_key')!=key or r.get('status')!='confirmed':
        return None,'unconfirmed_or_wrong_site_result'
    fetched=time(r.get('fetched_at'))
    if not fetched or not fetched>due+dt.timedelta(minutes=1) or fetched<=committed:
        return None,'result_timing_invalid'
    url=urlsplit(str(r.get('source') or ''))
    query=parse_qs(url.query)
    if (url.scheme!='https' or url.hostname!='www.boatrace.jp'
            or url.path!='/owpc/pc/race/raceresult'
            or query!={'hd':[key[:8]],'jcd':[key[9:11]],'rno':[str(int(key[12:14]))]}):
        return None,'result_origin_mismatch'
    finish=r.get('finish_order');win=r.get('trifecta');payout=r.get('trifecta_payout_yen_per_100')
    if (win not in COMBOS or not isinstance(finish,list) or len(finish)!=3
            or any(type(x)!=int for x in finish) or '-'.join(map(str,finish))!=win
            or type(payout) not in (int,float) or not 100<=payout<=100000000):
        return None,'result_contents_not_confirmable'
    return (r,p,win,int(payout),fetched),None

def score(root,path,now):
    base,reason=verify_frozen(root,path,now)
    if reason:return None,reason
    frozen,due,commit,committed=base
    key=path.stem
    result,reason=verify_result(root,key,due,committed)
    if reason:return None,reason
    r,p,win,payout,fetched=result
    band=frozen['top10_10_to_20x_at_freeze'];mode_out={}
    for name,rows in frozen['frozen_mode_tickets'].items():
        return_yen=sum(int(payout*(x['stake_yen']//100)) for x in rows if x['combo']==win)
        mode_out[name]={'tickets':len(rows),'frozen_stake_yen':sum(x['stake_yen'] for x in rows),
                        'hypothetical_return_yen':return_yen,'hit':return_yen>0}
    band_cost=len(band)*100
    return {'schema':SCORE_SCHEMA,'scope':'POST_RESULT_SITE_RESEARCH_ONLY_FORMAL_FRESH_LOCKED',
            'race_key':key,'venue':frozen.get('venue'),'model_id':frozen['model_id'],
            'cohort_sha256':sha(path),'first_git_commit':commit,'first_git_committed_at':committed.isoformat(),
            'evidence_recorded_at':frozen['evidence_committed_at'],
            'deadline_jst':frozen['deadline_jst'],'result_source':r['source'],
            'result_fetched_at':fetched.isoformat(),'result_sha256':sha(p),
            'winning_combo':win,'official_payout_per_100_yen':payout,
            'head_prediction':frozen['head_top1'],'actual_head':win[0],
            'head_hit':frozen['head_top1']==win[0],
            'top3_hit':win in frozen['top3'],'top5_hit':win in frozen['top5'],'top10_hit':win in frozen['top10'],
            'top10_10_20x_candidates':len(band),'top10_10_20x_hit':win in band,
            'band_flat100_hypothetical_stake_yen':band_cost,
            'band_flat100_hypothetical_return_yen':payout if win in band else 0,
            'modes':mode_out,'real_or_paper_wagers_placed':0,
            'accuracy_improvement_proven':False,'model_promotion_authorized':False},None

def summarize(root,now,scored_now,reasons):
    scores=root/'data/site_autopilot/v234_scored'
    valid=[]
    for path in sorted(scores.glob('20??????-??-??.json')):
        v=read(path)
        if not v or v.get('schema')!=SCORE_SCHEMA or v.get('race_key')!=path.stem:
            raise RuntimeError('V234_CORRUPTED_SETTLED_PROOF_'+path.stem)
        valid.append(v)
    def count(k):return sum(v[k] is True for v in valid)
    d={}
    for name in ('hit','balance','hole','narrow'):
        stake=sum(v['modes'][name]['frozen_stake_yen'] for v in valid)
        ret=sum(v['modes'][name]['hypothetical_return_yen'] for v in valid)
        d[name]={'hypothetical_stake_yen':stake,'hypothetical_return_yen':ret,
                 'hypothetical_roi_percent':round(100*ret/stake,2) if stake else None,
                 'hit_races':sum(v['modes'][name]['hit'] for v in valid)}
    cost=sum(v['band_flat100_hypothetical_stake_yen'] for v in valid)
    ret=sum(v['band_flat100_hypothetical_return_yen'] for v in valid)
    return {'schema':SUMMARY_SCHEMA,'scope':'POST_RESULT_SITE_ONLY_NOT_FORMAL_FRESH',
            'checked_at':now.isoformat(),'settled_verified_races':len(valid),
            'new_settled_races_this_run':scored_now,
            'head_hit':count('head_hit'),'top3_hit':count('top3_hit'),
            'top5_hit':count('top5_hit'),'top10_hit':count('top10_hit'),
            'band_10_20x_hit':count('top10_10_20x_hit'),
            'band_10_20x_eligible_races':sum(v['top10_10_20x_candidates']>0 for v in valid),
            'band_10_20x_flat100_stake_yen':cost,
            'band_10_20x_flat100_return_yen':ret,
            'band_10_20x_observed_roi_percent':round(100*ret/cost,2) if cost else None,
            'frozen_mode_hypothetical_outcomes':d,
            'scoring_exclusions_this_run':reasons,
            'research_only_insufficient_for_promotion':len(valid)<100,
            'production_accuracy_improvement_proven':False,
            'production_model_changed':False,'real_or_paper_wagers_placed':0,
            'recent':list(reversed([{'race_key':v['race_key'],'venue':v['venue'],
                        'head_hit':v['head_hit'],'top3_hit':v['top3_hit'],
                        'top5_hit':v['top5_hit'],'top10_hit':v['top10_hit'],
                        'band_hit':v['top10_10_20x_hit'],'payout_per_100_yen':v['official_payout_per_100_yen'],
                        'winning_combo':v['winning_combo']} for v in valid][-40:]))}

def run(root,now):
    root=root.resolve();guard(root)
    base=root/'data/site_autopilot/v232_cohort'
    out=root/'data/site_autopilot/v234_scored'
    new=0;reasons={}
    for p in sorted(base.glob('20??????-??-??.json')):
        if (out/p.name).is_file():
            # Never rewrite a settled result even if the source later changes.
            continue
        record,why=score(root,p,now)
        if record:
            new+=write_once(out/p.name,record)
        else:
            reasons[why]=reasons.get(why,0)+1
    summary=summarize(root,now,new,reasons)
    destination=root/'data/site_autopilot/v234_current.json'
    old=read(destination) or {}
    compare=['settled_verified_races','head_hit','top3_hit','top5_hit','top10_hit','band_10_20x_hit',
             'band_10_20x_eligible_races','band_10_20x_flat100_stake_yen','band_10_20x_flat100_return_yen',
             'frozen_mode_hypothetical_outcomes','scoring_exclusions_this_run']
    if not destination.is_file() or new or any(old.get(k)!=summary.get(k) for k in compare):
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('V234_SITE_ONLY_CONFIRMED_SCORE',json.dumps({'new':new,'settled':summary['settled_verified_races'],
         'head':summary['head_hit'],'top3':summary['top3_hit'],'top5':summary['top5_hit'],
         'top10':summary['top10_hit'],'10_20x':summary['band_10_20x_hit'],'pending_reasons':reasons},sort_keys=True))
    return summary

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path('.'));ap.add_argument('--now')
    args=ap.parse_args();n=time(args.now) if args.now else dt.datetime.now(UTC)
    if n is None:raise SystemExit('V234_BAD_CLOCK')
    run(args.root,n)
