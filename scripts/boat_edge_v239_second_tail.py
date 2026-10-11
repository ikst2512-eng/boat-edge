#!/usr/bin/env python3
"""V239 prospective site-only ten-ticket second-place / tail A-B shadow.

Never reads formal results. Only previously Git-committed V232 cohorts before
race deadline and independently scored V234 SITE records after settlement.
Not authorized to change production predictions, betting, or model versions.
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

UTC = dt.timezone.utc
JST = dt.timezone(dt.timedelta(hours=9))
KEY = re.compile(r'^20\d{6}-\d{2}-\d{2}$')
TRI = re.compile(r'^[1-6]-[1-6]-[1-6]$')
PRE_SCHEMA = 'BOAT_EDGE_V239_SECOND_TAIL_FORWARD_10PT_V1'
SCORE_SCHEMA = 'BOAT_EDGE_V239_SECOND_TAIL_SCORE_V1'
PATH = Path('data/site_autopilot')
MODES = ('hit10', 'balance10', 'second_diverse10', 'tail_swap10')


def read(path):
    try:
        obj=json.loads(path.read_text(encoding='utf-8'))
        return obj if isinstance(obj,dict) else None
    except (OSError,UnicodeError,ValueError):return None


def stamp(s):
    try:
        d=dt.datetime.fromisoformat(str(s).replace('Z','+00:00'))
        return d.astimezone(UTC) if d.tzinfo else None
    except (ValueError,TypeError,OverflowError):return None


def digest(path):
    try:return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:return None


def valid(s):
    return isinstance(s,str) and TRI.fullmatch(s) is not None and len(set(s.split('-')))==3


def formal_closed(root):
    obj=read(root/'data/formal_status.json') or {}
    g=obj.get('guards') or {}
    if any(g.get(x) is not False for x in ('results_seen','unlock','scoring')) or g.get('RESULT_UNLOCK_TOKEN') is not None:
        raise RuntimeError('V239_FORMAL_GATE_NOT_LOCKED')
    if (obj.get('formalFirst100') or {}).get('races',0)!=0:
        raise RuntimeError('V239_FORMAL_FIRST100_NOT_EMPTY')


def first_git(root,path):
    rel=path.relative_to(root).as_posix()
    try:
        p=subprocess.run(['git','log','--diff-filter=A','--reverse','--format=%H|%cI','--',rel],cwd=root,capture_output=True,text=True,check=False)
        if p.returncode or not p.stdout.strip():return None
        commit,when=p.stdout.splitlines()[0].split('|',1)
        blob=subprocess.run(['git','show',f'{commit}:{rel}'],cwd=root,capture_output=True,check=False)
        if blob.returncode:return None
        return {'commit':commit,'at':stamp(when),'sha256':hashlib.sha256(blob.stdout).hexdigest()}
    except (OSError,ValueError):return None


def unique_extend(seed,extra,count=10):
    out=list(seed)
    for s in extra:
        if s not in out:out.append(s)
        if len(out)>=count:break
    return out[:count]


def second_diverse(hit,balance,hole,head):
    """Keep first 7, then seek new second-place runners from pre-frozen modes.

    If the precommitted source lists have no such alternatives, fill by original
    hit rank; no proxy or model-driven odds calculation is invented.
    """
    seed=hit[:7];seen={x[2] for x in seed if x[0]==head}
    pool=list(balance)+list(hole)+hit[7:]
    chosen=[]
    for x in pool:
        if x in seed or x in chosen or x[0]!=head or x[2] in seen:continue
        chosen.append(x);seen.add(x[2])
        if len(chosen)>=3:break
    return unique_extend(seed,chosen+hit[7:]+balance+hole,10)


def tail_swap(hit):
    """Keep 7 top-ranked combos and use deterministic 2nd/3rd flips.

    This is a *future-only*, predeclared hypothesis; results cannot influence
    which combos are flipped. Does not claim the flipped bets are more likely.
    """
    seed=hit[:7];flips=[]
    for x in hit:
        a,b,c=x.split('-')
        flipped=f'{a}-{c}-{b}'
        if flipped not in seed and flipped not in flips:flips.append(flipped)
    return unique_extend(seed,flips+hit[7:],10)


def prepare(root,path,now):
    src=read(path) or {};key=path.stem
    if not KEY.fullmatch(key) or src.get('race_key')!=key:return None,'bad_race_key'
    due=stamp(src.get('deadline_jst'))
    if not due or not 90 <= (due-now).total_seconds() <= 900:return None,'not_in_prospective_window'
    created=stamp(src.get('snapshot_saved_at'));published=stamp(src.get('evidence_committed_at'))
    proof=first_git(root,path)
    if (not created or not published or not proof or not proof['at'] or not
       created<=published<=proof['at']<=now<due or proof['sha256']!=digest(path)):
        return None,'unverified_original_git_before_deadline'
    if (src.get('schema')!='BOAT_EDGE_V232_SITE_PROSPECTIVE_ACCURACY_COHORT_V1' or
        src.get('scope')!='SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH' or
        src.get('formal_results_seen') is not False or src.get('formal_gate_unlocked') is not False or
        src.get('paper_purchases_authorized') is not False or src.get('real_purchases_authorized') is not False or
        src.get('model_id')!='SITE_REFERENCE_V122'):
        return None,'cohort_guards_or_scope_invalid'
    modes=src.get('frozen_mode_tickets')
    if not isinstance(modes,dict):return None,'missing_frozen_modes'
    lists={}
    for mode in ('hit','balance','hole'):
        raw=modes.get(mode)
        if not isinstance(raw,list) or len(raw)<10:return None,'mode_has_less_than_ten'
        tickets=[x.get('combo') if isinstance(x,dict) else None for x in raw]
        if len(set(tickets))!=len(tickets) or any(not valid(x) for x in tickets):return None,'invalid_mode_tickets'
        lists[mode]=tickets
    hit,balance,hole=lists['hit'],lists['balance'],lists['hole']
    if len(hit)!=10 or len(balance)!=10 or src.get('top10')!=hit or src.get('head_top1')!=hit[0][0]:
        return None,'top10_or_head_mismatch'
    comp={'hit10':hit,'balance10':balance,
          'second_diverse10':second_diverse(hit,balance,hole,hit[0][0]),
          'tail_swap10':tail_swap(hit)}
    if any(len(v)!=10 or len(set(v))!=10 or any(not valid(x) for x in v) for v in comp.values()):
        return None,'challenger_not_exact_ten'
    return {'schema':PRE_SCHEMA,'scope':'PROSPECTIVE_SITE_SHADOW_NO_FORMAL_ACCESS',
        'race_key':key,'deadline_jst':src['deadline_jst'],'frozen_at_utc':now.isoformat(),
        'v232_cohort_sha256':digest(path),'v232_first_git_commit':proof['commit'],
        'v232_first_git_committed_at':proof['at'].isoformat(), 'comparators':comp,
        'predeclared_policy':'TOP7_PLUS_SECOND_RUNNER_COVERAGE_VS_TOP7_PLUS_SECOND_THIRD_FLIPS',
        'production_model_changed':False,'betting_authorized':False,
        'result_seen_at_freeze':False,'accuracy_improvement_proven':False},None


def save_once(path,row):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:
        f.write(json.dumps(row,sort_keys=True,ensure_ascii=False,indent=2)+'\n')


def save_changed(path,row,keys):
    old=read(path) or {}
    if path.exists() and all(old.get(k)==row.get(k) for k in keys):return False
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(row,sort_keys=True,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return True


def freeze(root,now):
    formal_closed(root)
    day=now.astimezone(JST).strftime('%Y%m%d')
    srcdir=root/PATH/'v232_cohort';dest=root/PATH/'v239_frozen';excluded={};added=0
    for src in sorted(srcdir.glob(day+'-??-??.json')):
        output=dest/src.name
        if output.exists():continue
        obj,reason=prepare(root,src,now)
        if reason:excluded[reason]=excluded.get(reason,0)+1
        else:save_once(output,obj);added+=1
    n=len(list(dest.glob(day+'-??-??.json'))) if dest.exists() else 0
    summary={'schema':'BOAT_EDGE_V239_PRE_SUMMARY_V1','day_jst':day,'frozen_today':n,
        'new_frozen_this_run':added,'rejected_current_window':excluded,
        'candidate_names':list(MODES),'all_modes_ten_points':True,
        'accuracy_improvement_proven':False,'production_model_changed':False,'formal_result_access':False}
    save_changed(root/PATH/'v239_pre_current.json',summary,['day_jst','frozen_today','rejected_current_window'])
    print('V239_FUTURE_ONLY_PRE_RESULT',json.dumps({'new':added,'today':n,'rejected':excluded},sort_keys=True))
    return summary


def score_one(root,path,now):
    key=path.stem;src=read(path) or {}
    if not KEY.fullmatch(key) or src.get('race_key')!=key or src.get('schema')!=PRE_SCHEMA:
        return None,'bad_frozen_schema_or_key'
    due=stamp(src.get('deadline_jst'))
    if not due or now<=due+dt.timedelta(minutes=2):return None,'race_not_finished'
    proof=first_git(root,path)
    if not proof or not proof['at'] or proof['at']>=due or proof['sha256']!=digest(path):
        return None,'challenger_not_git_attested_before_deadline'
    cohort=root/PATH/'v232_cohort'/path.name
    if digest(cohort)!=src.get('v232_cohort_sha256'):return None,'original_cohort_mutated'
    parentproof=first_git(root,cohort)
    if (not parentproof or parentproof['sha256']!=digest(cohort) or
       parentproof['commit']!=src.get('v232_first_git_commit') or
       not parentproof['at'] or parentproof['at']>=due or
       parentproof['at'].isoformat()!=src.get('v232_first_git_committed_at')):
        return None,'parent_provenance_mismatch'
    scorepath=root/PATH/'v234_scored'/path.name
    official=read(scorepath)
    if (not official or official.get('schema')!='BOAT_EDGE_V234_PRECOMMITTED_SITE_ONLY_RESULT_SCORE_V1' or
        official.get('scope')!='POST_RESULT_SITE_RESEARCH_ONLY_FORMAL_FRESH_LOCKED' or
        official.get('race_key')!=key or official.get('cohort_sha256')!=digest(cohort)):
        return None,'v234_site_verified_result_not_available'
    firstscore=first_git(root,scorepath)
    checked=stamp(official.get('result_fetched_at'))
    if (not firstscore or firstscore['sha256']!=digest(scorepath) or not firstscore['at'] or
        firstscore['at']<=due or not checked or checked<=due):
        return None,'v234_result_provenance_invalid'
    source=urlsplit(str(official.get('result_source') or ''))
    hd,jcd,rno=key.split('-')
    if (source.scheme!='https' or source.netloc!='www.boatrace.jp' or source.path!='/owpc/pc/race/raceresult' or
        parse_qs(source.query)!={'hd':[hd],'jcd':[jcd],'rno':[str(int(rno))]}):
        return None,'v234_result_url_invalid'
    winning=official.get('winning_combo');comps=src.get('comparators')
    if not valid(winning) or not isinstance(comps,dict) or set(comps)!=set(MODES):return None,'invalid_comparison_contract'
    if any(not isinstance(t,list) or len(t)!=10 or len(set(t))!=10 or any(not valid(s) for s in t) for t in comps.values()):
        return None,'invalid_ten_point_list'
    if official.get('top10_hit') is not (winning in comps['hit10']):return None,'v234_baseline_parity_failed'
    result={name:winning in picks for name,picks in comps.items()}
    return {'schema':SCORE_SCHEMA,'scope':'POST_RESULT_SITE_ONLY_V239_PAIRED_NOT_FORMAL',
        'race_key':key,'winning_combo':winning,'frozen_sha256':digest(path),
        'v234_score_sha256':digest(scorepath),'first_candidate_git_commit':proof['commit'],
        'v234_first_git_commit':firstscore['commit'],
        'outcomes':result,'ticket_counts':{name:10 for name in MODES},
        'production_model_changed':False,'promotion_authorized':False,
        'real_or_paper_bet':False},None


def score(root,now):
    formal_closed(root)
    folder=root/PATH/'v239_frozen';dest=root/PATH/'v239_scored'
    excluded={};new=0
    if folder.exists():
        for f in sorted(folder.glob('20??????-??-??.json')):
            if (dest/f.name).exists():continue
            obj,reason=score_one(root,f,now)
            if reason:excluded[reason]=excluded.get(reason,0)+1
            else:save_once(dest/f.name,obj);new+=1
    validrows=[]
    if dest.exists():
        for f in sorted(dest.glob('20??????-??-??.json')):
            row=read(f)
            if not row or row.get('schema')!=SCORE_SCHEMA or row.get('race_key')!=f.stem:
                raise RuntimeError('V239_SCORED_ROW_CORRUPTED_'+f.stem)
            if set(row.get('outcomes',{}))!=set(MODES) or any(type(x)!=bool for x in row['outcomes'].values()):
                raise RuntimeError('V239_OUTCOMES_INVALID_'+f.stem)
            validrows.append(row)
    n=len(validrows);baseline=sum(x['outcomes']['hit10'] for x in validrows)
    comparisons={mode:{'races':n,'hits':sum(x['outcomes'][mode] for x in validrows),
         'hit_rate_percent':round(100*sum(x['outcomes'][mode] for x in validrows)/n,2) if n else None,
         'paired_gain_vs_hit10':sum(x['outcomes'][mode] and not x['outcomes']['hit10'] for x in validrows),
         'paired_loss_vs_hit10':sum(x['outcomes']['hit10'] and not x['outcomes'][mode] for x in validrows),
         'points':10} for mode in MODES}
    summary={'schema':'BOAT_EDGE_V239_PAIRED_SCORE_SUMMARY_V1','scope':'FUTURE_ONLY_SITE_SHADOW_NOT_FORMAL',
        'scored_total':n,'new_scored_this_run':new,'baseline_hit10':baseline,
        'comparisons':comparisons,'pending':excluded,'promotion_authorized':False,
        'accuracy_improvement_proven':False,'production_model_changed':False,
        'status':'NOT_READY_FOR_PROMOTION_REQUIRE_INDEPENDENT_MULTI_DAY_FRESH',
        'paired_examples':[{'race_key':r['race_key'],'winning_combo':r['winning_combo'],'outcomes':r['outcomes']} for r in validrows[-25:]]}
    save_changed(root/PATH/'v239_score_current.json',summary,['scored_total','comparisons','pending'])
    print('V239_FROZEN_TEN_POINT_PAIRED_SCORE',json.dumps({'new':new,'total':n,'comparisons':comparisons,'pending':excluded},sort_keys=True))
    return summary


def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['freeze','score']);p.add_argument('--root',type=Path,default=Path('.'));p.add_argument('--now')
    args=p.parse_args();now=stamp(args.now) if args.now else dt.datetime.now(UTC)
    if not now:raise SystemExit('V239_BAD_CLOCK')
    root=args.root.resolve()
    if args.phase=='freeze':freeze(root,now)
    else:score(root,now)

if __name__=='__main__':main()
