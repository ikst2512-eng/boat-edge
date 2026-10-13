#!/usr/bin/env python3
"""V254 predeclared third-leg diversity shadow: site-only, future-only, no promotion.

Freeze reads only original Git-committed V232 PRE_RESULT cohorts; NEVER any results.
Score reads only separately Git-committed V254 frozen rows + verified V241 site
results after the deadline. Formal Fresh results remain completely locked.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess

UTC=dt.timezone.utc
JST=dt.timezone(dt.timedelta(hours=9))
BASE=Path('data/site_autopilot')
KEY=re.compile(r'^20\d{6}-\d{2}-\d{2}$')
TRI=re.compile(r'^[1-6]-[1-6]-[1-6]$')
FROZEN_SCHEMA='BOAT_EDGE_V254_FUTURE_THIRD_TAIL_FROZEN_V1'
SCORED_SCHEMA='BOAT_EDGE_V254_FUTURE_THIRD_TAIL_SCORED_V1'

def get(path):
    try:
        d=json.loads(path.read_text(encoding='utf-8'))
        return d if isinstance(d,dict) else None
    except (OSError,UnicodeError,ValueError):return None

def sha(path):
    try:return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:return None

def stamp(v):
    try:
        d=dt.datetime.fromisoformat(str(v).replace('Z','+00:00'))
        return d.astimezone(UTC) if d.tzinfo else None
    except (TypeError,ValueError,OverflowError):return None

def valid(c):
    return isinstance(c,str) and bool(TRI.fullmatch(c)) and len(set(c.split('-')))==3

def write_once(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:
        json.dump(obj,f,ensure_ascii=False,sort_keys=True,indent=2)
        f.write('\n')

def write_changed(path,obj):
    text=json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    if path.exists() and path.read_text(encoding='utf-8')==text:return False
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding='utf-8');return True

def formal_guard(root):
    status=get(root/'data/formal_status.json') or {}
    g=status.get('guards') or {}
    if any(g.get(k) is not False for k in ('results_seen','unlock','scoring')) or g.get('RESULT_UNLOCK_TOKEN') is not None:
        raise RuntimeError('V254_FORMAL_GATE_MUST_STAY_CLOSED')
    # Unlike a false flag, a missing/nonempty formal cohort is not proof of isolation.
    races=(status.get('formalFirst100') or {}).get('races')
    if type(races) is not int or races!=0:
        raise RuntimeError('V254_FORMAL_COHORT_MUST_BE_CONFIRMED_EMPTY')

def git_first(root,path):
    rel=path.relative_to(root).as_posix()
    try:
        commits=subprocess.check_output(['git','log','--diff-filter=A','--reverse','--format=%H','--',rel],cwd=root,text=True,stderr=subprocess.DEVNULL).splitlines()
        if not commits:return None
        h=commits[0]
        first=stamp(subprocess.check_output(['git','show','-s','--format=%cI',h],cwd=root,text=True,stderr=subprocess.DEVNULL).strip())
        data=subprocess.check_output(['git','show',f'{h}:{rel}'],cwd=root,stderr=subprocess.DEVNULL)
        return {'commit':h,'at':first,'sha256':hashlib.sha256(data).hexdigest()}
    except (OSError,subprocess.CalledProcessError):return None

def third_tail_candidate(hit,hole):
    """Top7 stays byte-identical; only extra tickets with SAME (1st,2nd) pairs.

    Source holes are pre-frozen ranks; never reorder by odds, results, or payouts.
    If fewer than 3 independent such tickets exist, backfill ORIGINAL Hit10,
    not imputed or post-result tickets. Always exactly 10 distinct valid tickets.
    """
    if (len(hit)!=10 or len(set(hit))!=10 or len(hole)<10 or len(set(hole))!=len(hole) or
        not all(valid(c) for c in hit+hole)):return None
    fixed=hit[:7];prefix={c[:3] for c in fixed}
    novel=[c for c in hole if c not in hit and c[:3] in prefix]
    result=list(fixed)
    for c in novel+hit[7:]:
        if c not in result:result.append(c)
        if len(result)==10:break
    if len(result)!=10:return None
    return result

def make_pre(root,path,now):
    formal_guard(root)
    key=path.stem
    source=get(path) or {}
    deadline=stamp(source.get('deadline_jst'))
    saved=stamp(source.get('snapshot_saved_at'))
    evidence=stamp(source.get('evidence_committed_at'))
    # HARD time gate: never create historical/backfilled research cohorts.
    if not KEY.fullmatch(key) or not deadline or not 90<=(deadline-now).total_seconds()<=900:
        return None,'NOT_IN_FUTURE_FREEZE_WINDOW'
    if not saved or not evidence or not saved<=evidence<=now<deadline:
        return None,'SOURCE_TIMESTAMPS_UNVERIFIED'
    proof=git_first(root,path)
    if not proof or not proof['at'] or not saved<=proof['at']<=now<deadline or proof['sha256']!=sha(path):
        return None,'SOURCE_GIT_PROVENANCE_UNVERIFIED'
    if (source.get('race_key')!=key or
        source.get('schema')!='BOAT_EDGE_V232_SITE_PROSPECTIVE_ACCURACY_COHORT_V1' or
        source.get('scope')!='SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH' or
        source.get('model_id')!='SITE_REFERENCE_V122' or
        source.get('formal_results_seen') is not False or
        source.get('formal_gate_unlocked') is not False or
        source.get('paper_purchases_authorized') is not False or
        source.get('real_purchases_authorized') is not False or
        source.get('production_accuracy_claim') is True):
        return None,'SOURCE_FRESH_CONTRACT_NOT_MET'
    modes=source.get('frozen_mode_tickets') or {}
    if not isinstance(modes,dict):return None,'NO_SAVED_MODE_TICKETS'
    hit=[t.get('combo') for t in modes.get('hit',[]) if isinstance(t,dict)]
    hole=[t.get('combo') for t in modes.get('hole',[]) if isinstance(t,dict)]
    if hit!=source.get('top10'):return None,'PARENT_TOP10_MISMATCH'
    challenger=third_tail_candidate(hit,hole)
    if challenger is None:return None,'THIRD_TAIL_CANDIDATE_INVALID'
    novelty=len(set(challenger)-set(hit))
    return {
      'schema':FROZEN_SCHEMA,'scope':'FUTURE_PRE_RESULT_SITE_ONLY_NOT_FORMAL_FRESH',
      'race_key':key,'deadline_jst':source['deadline_jst'],
      'frozen_at':now.isoformat(),'parent_first_git_commit':proof['commit'],
      'parent_first_commit_at':proof['at'].isoformat(),
      'parent_v232_sha256':sha(path),'parent_snapshot_saved_at':source['snapshot_saved_at'],
      'head_or_tail_strategy':'TOP7_FIXED_SAME_FIRST_SECOND_THIRD_TAIL_FROM_PRECOMMITTED_HOLE_BACKFILL_HIT10',
      'comparators':{'hit10':hit,'third_tail10':challenger},
      'third_tail_new_ticket_count':novelty,
      'formal_result_access':False,'results_seen_at_freeze':False,
      'production_model_changed':False,'accuracy_improvement_proven':False,
      'model_promotion_authorized':False,'real_or_paper_wagers_placed':0,
    },None

def freeze(root,now):
    formal_guard(root)
    day=now.astimezone(JST).strftime('%Y%m%d')
    folder=root/BASE/'v232_cohort';dest=root/BASE/'v254_frozen'
    fresh=0;rejected={}
    source_paths=sorted(folder.glob(day+'-??-??.json'))
    window_paths=[];unfrozen_window=0
    for path in source_paths:
        # Counts are only observed PRE_RESULT cohort metadata, not a guess about
        # official results or the number of races that could have been predicted.
        prior=get(path) or {}
        due=stamp(prior.get('deadline_jst'))
        if due and 90 <= (due-now).total_seconds() <= 900:
            window_paths.append(path.name)
            if not (dest/path.name).exists():unfrozen_window+=1
        if (dest/path.name).exists():continue
        row,error=make_pre(root,path,now)
        if row:
            write_once(dest/path.name,row);fresh+=1
        else:rejected[error]=rejected.get(error,0)+1
    history=[get(p) for p in sorted(dest.glob(day+'-??-??.json'))]
    history=[x for x in history if x and x.get('schema')==FROZEN_SCHEMA]
    obj={'schema':'BOAT_EDGE_V254_FUTURE_THIRD_TAIL_PRE_SUMMARY_V1',
       'day_jst':day,'frozen_today':len(history),
       'source_cohorts_today':len(source_paths),
       'upstream_diagnostic':('NO_V232_COHORTS_TODAY' if not source_paths else
                              'NO_COHORTS_IN_FUTURE_WINDOW' if not window_paths else
                              'FUTURE_WINDOW_COHORTS_PRESENT'),
       'future_window_cohorts_seen':len(window_paths),
       'unfrozen_future_window_at_start':unfrozen_window,
       'new_frozen_this_run':fresh,
       'rejected_current_run':dict(sorted(rejected.items())),
       'third_tail_novel_races_today':sum(x['third_tail_new_ticket_count']>0 for x in history),
       'third_tail_novel_tickets_today':sum(x['third_tail_new_ticket_count'] for x in history),
       'scope':'PRE_RESULT_FUTURE_SITE_RESEARCH_NOT_FORMAL_FRESH',
       'result_access':False,'production_model_changed':False,
       'accuracy_improvement_proven':False,'model_promotion_authorized':False}
    write_changed(root/BASE/'v254_pre_current.json',obj)
    print('V254_FUTURE_ONLY_FREEZE',json.dumps({'new':fresh,'frozen':len(history),'source_today':len(source_paths),
      'source_in_future_window':len(window_paths),'unfrozen_at_start':unfrozen_window,
      'skipped':rejected},sort_keys=True))
    return obj

def verified_site(root):
    formal_guard(root)
    report=get(root/BASE/'v241_results_current.json')
    if (not report or report.get('schema')!='BOAT_EDGE_V241_VERIFIED_SITE_RESULTS_V1' or
        report.get('scope')!='VERIFIED_POST_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH' or
        report.get('formal_result_access') is not False or
        report.get('real_or_paper_wagers_placed')!=0 or
        report.get('production_model_changed') is not False or
        report.get('accuracy_improvement_proven') is not False):return {}
    rows=report.get('rows')
    if not isinstance(rows,list) or len(rows)!=report.get('settled_verified_races'):return {}
    out={}
    for row in rows:
        key=row.get('race_key')
        if (not KEY.fullmatch(str(key or '')) or key in out or
            row.get('post_result_verified') is not True or
            not valid(row.get('winning_combo')) or
            row.get('precommitted_sha256') is None or
            not isinstance(row.get('top10_hit'),bool) or
            row.get('mode_outcomes',{}).get('hit',{}).get('hit') is not row.get('top10_hit')):
            return {}
        out[key]=row
    return out

def score_one(root,path,results,now):
    formal_guard(root)
    row=get(path) or {}
    key=path.stem
    deadline=stamp(row.get('deadline_jst'))
    if not deadline or now<=deadline+dt.timedelta(minutes=1):return None,'RACE_NOT_OVER'
    result=results.get(key)
    if not result:return None,'SITE_OFFICIAL_SCORE_NOT_VERIFIED'
    frozen=git_first(root,path)
    if not frozen or not frozen['at'] or frozen['at']>=deadline or frozen['sha256']!=sha(path):
        return None,'CANDIDATE_NOT_GIT_FROZEN_BEFORE_DEADLINE'
    original=root/BASE/'v232_cohort'/path.name
    parent=git_first(root,original)
    if (not parent or not parent['at'] or parent['at']>=deadline or
        parent['sha256']!=row.get('parent_v232_sha256') or
        parent['commit']!=row.get('parent_first_git_commit') or
        sha(original)!=parent['sha256'] or
        result.get('first_frozen_commit')!=parent['commit'] or
        result.get('precommitted_sha256')!=parent['sha256']):
        return None,'PARENT_PREDEADLINE_GIT_PROOF_FAILED'
    if (not stamp(row.get('frozen_at')) or stamp(row['frozen_at'])>=deadline or
        row.get('parent_snapshot_saved_at')!=(get(original) or {}).get('snapshot_saved_at') or
        row.get('schema')!=FROZEN_SCHEMA or
        row.get('scope')!='FUTURE_PRE_RESULT_SITE_ONLY_NOT_FORMAL_FRESH' or
        row.get('results_seen_at_freeze') is not False or
        row.get('formal_result_access') is not False or
        row.get('production_model_changed') is not False or
        row.get('accuracy_improvement_proven') is not False or
        row.get('model_promotion_authorized') is not False or
        row.get('real_or_paper_wagers_placed')!=0):return None,'FROZEN_SCOPE_OR_GUARD_FAILED'
    lists=row.get('comparators') or {}
    if set(lists)!=set(('hit10','third_tail10')) or any(not isinstance(v,list) or len(v)!=10 or len(set(v))!=10 or not all(valid(c) for c in v) for v in lists.values()):
        return None,'FROZEN_TICKET_LIST_CORRUPT'
    winning=result['winning_combo']
    if (lists['hit10']!=(get(original) or {}).get('top10') or
        lists['third_tail10']!=third_tail_candidate(lists['hit10'],
            [t.get('combo') for t in (get(original) or {}).get('frozen_mode_tickets',{}).get('hole',[])]) or
        (winning in lists['hit10']) != result['top10_hit']):
        return None,'FROZEN_TICKETS_VS_SCORED_RESULT_MISMATCH'
    return {'schema':SCORED_SCHEMA,'scope':'POST_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH',
      'race_key':key,'winning_combo':winning,
      'result_precommitted_sha256':result['precommitted_sha256'],
      'frozen_sha256':sha(path),'candidate_first_git_commit':frozen['commit'],
      'candidate_first_git_committed_at':frozen['at'].isoformat(),
      'outcomes':{k:winning in v for k,v in lists.items()},
      'novel_tickets':row['third_tail_new_ticket_count'],
      'production_model_changed':False,'model_promotion_authorized':False,
      'accuracy_improvement_proven':False,'formal_result_access':False,
      'real_or_paper_wagers_placed':0},None

def score(root,now):
    formal_guard(root)
    base=root/BASE/'v254_frozen';dest=root/BASE/'v254_scored'
    results=verified_site(root)
    rejected={};added=0
    for path in sorted(base.glob('20??????-??-??.json')):
        if (dest/path.name).exists():continue
        row,error=score_one(root,path,results,now)
        if row:
            write_once(dest/path.name,row);added+=1
        else:rejected[error]=rejected.get(error,0)+1
    rows=[get(p) for p in sorted(dest.glob('20??????-??-??.json'))]
    if any(not x or x.get('schema')!=SCORED_SCHEMA or x.get('production_model_changed') is not False for x in rows):
        raise RuntimeError('V254_SCORED_RESEARCH_DATA_CORRUPT')
    n=len(rows)
    current=sum(x['outcomes']['hit10'] for x in rows)
    candidate=sum(x['outcomes']['third_tail10'] for x in rows)
    a=sum(x['outcomes']['third_tail10'] and not x['outcomes']['hit10'] for x in rows)
    b=sum(x['outcomes']['hit10'] and not x['outcomes']['third_tail10'] for x in rows)
    doc={'schema':'BOAT_EDGE_V254_FUTURE_THIRD_TAIL_SCORE_SUMMARY_V1',
       'scope':'POST_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH',
       'scored_total':n,'comparisons':{'hit10':{'hits':current,'races':n,'points':10},
         'third_tail10':{'hits':candidate,'races':n,'points':10,'paired_gain':a,'paired_loss':b}},
       'affected_races':sum(x['novel_tickets']>0 for x in rows),
       'rejected_or_pending':dict(sorted(rejected.items())),
       'examples':[{'race_key':x['race_key'],'outcomes':x['outcomes'],'novel_tickets':x['novel_tickets']} for x in rows[-30:]],
       'formal_result_access':False,'production_model_changed':False,
       'accuracy_improvement_proven':False,'model_promotion_authorized':False,
       'real_or_paper_wagers_placed':0,
       'status':'UNSEEN_SHADOW_RESEARCH_NO_PRODUCTION_PROMOTION'}
    write_changed(root/BASE/'v254_score_current.json',doc)
    print('V254_FUTURE_ONLY_PAIRED_SCORE',json.dumps({'new':added,'scored':n,'control':current,'candidate':candidate,'gains':a,'losses':b,'pending':rejected},sort_keys=True))
    return doc

def main():
    p=argparse.ArgumentParser()
    p.add_argument('phase',choices=('freeze','score'))
    p.add_argument('--root',default='.')
    p.add_argument('--now')
    a=p.parse_args()
    now=stamp(a.now) if a.now else dt.datetime.now(UTC)
    if not now:raise SystemExit('V254_CLOCK_UNVERIFIED')
    root=Path(a.root).resolve()
    if a.phase=='freeze':freeze(root,now)
    else:score(root,now)

if __name__=='__main__':main()
