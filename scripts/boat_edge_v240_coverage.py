#!/usr/bin/env python3
"""V240 prospective, site-only candidate diversity and paired audit.

No formal data, result access in freeze, odds-based ranking, weight change or promotion.
Candidate constructions are uncalibrated, pre-declared counterfactual research ONLY.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit, parse_qs

JST=dt.timezone(dt.timedelta(hours=9))
UTC=dt.timezone.utc
PATH=Path('data/site_autopilot')
KEY=re.compile(r'^20\d{6}-\d\d-\d\d$')
TRI=re.compile(r'^[1-6]-[1-6]-[1-6]$')
PRE_SCHEMA='BOAT_EDGE_V240_INDEPENDENT_SECOND_COVERAGE_PRE_V1'
SCORE_SCHEMA='BOAT_EDGE_V240_INDEPENDENT_SECOND_COVERAGE_SCORE_V1'
MODES=('hit10','second_coverage10','pair_coverage10')


def read(p):
    try:
        o=json.loads(p.read_text(encoding='utf-8'))
        return o if isinstance(o,dict) else None
    except (OSError, UnicodeError, ValueError):return None


def stamp(v):
    try:
        d=dt.datetime.fromisoformat(str(v).replace('Z','+00:00'))
        return d.astimezone(UTC) if d.tzinfo else None
    except (ValueError,TypeError,OverflowError):return None


def sha(p):
    try:return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:return None


def combo_valid(c):
    return isinstance(c,str) and TRI.fullmatch(c) is not None and len(set(c.split('-')))==3


def guard(root):
    f=read(root/'data/formal_status.json') or {}
    g=f.get('guards') or {}
    if (any(g.get(x) is not False for x in ('results_seen','unlock','scoring')) or
            g.get('RESULT_UNLOCK_TOKEN') is not None or (f.get('formalFirst100') or {}).get('races') != 0):
        raise RuntimeError('V240_FORMAL_FRESH_MUST_REMAIN_LOCKED')


def first_git(root,p):
    rel=p.relative_to(root).as_posix()
    try:
        q=subprocess.run(['git','log','--diff-filter=A','--reverse','--format=%H|%cI','--',rel],cwd=root,capture_output=True,text=True,check=False)
        if q.returncode or not q.stdout.strip():return None
        commit,when=q.stdout.splitlines()[0].split('|',1)
        original=subprocess.run(['git','show',f'{commit}:{rel}'],cwd=root,capture_output=True,check=False)
        if original.returncode:return None
        return {'commit':commit,'at':stamp(when),'sha256':hashlib.sha256(original.stdout).hexdigest()}
    except (OSError, ValueError):return None


def frozen_lists(cohort):
    modes=cohort.get('frozen_mode_tickets') or {}
    if not isinstance(modes,dict):return None
    result={}
    for mode in ('hit','balance','hole'):
        rows=modes.get(mode)
        if not isinstance(rows,list) or len(rows)<10:return None
        picks=[row.get('combo') if isinstance(row,dict) else None for row in rows]
        if len(set(picks))!=len(picks) or any(not combo_valid(x) for x in picks):return None
        result[mode]=picks
    if len(result['hit'])!=10 or len(result['balance'])!=10:return None
    return result


def append_unique(seed, candidates, count=10):
    result=list(seed)
    for c in candidates:
        if c not in result:result.append(c)
        if len(result)==count:break
    return result[:count]


def second_coverage(hit, balance, hole):
    """Top7 + up to 3 genuinely novel SECOND-slot placements.

    Uses only pre-committed tickets, reversed pre-committed pairs, and
    six-racer permutation identities. No result/odds/probability at construction.
    Prefer a new second absent in baseline; then missing in top7; then a
    candidate whose head-second-third identity is absent in full baseline.
    """
    seed=hit[:7];head=hit[0][0]
    core_second={x[2] for x in seed if x[0]==head}
    baseline_second={x[2] for x in hit if x[0]==head}
    source=list(dict.fromkeys(hit+balance+hole))
    # Reversals are positional hypotheses; their outcomes are not looked up.
    flips=[f'{a}-{c}-{b}' for x in source for a,b,c in [x.split('-')] if a==head]
    # Build from existing source boat orders, then deterministic full-race fallback.
    ranked=list(dict.fromkeys(source+flips))
    thirds=[x[4] for x in ranked if x[0]==head]
    seconds=[x[2] for x in ranked if x[0]==head]
    allseconds=list(dict.fromkeys(seconds+[str(i) for i in range(1,7) if str(i)!=head]))
    allthirds=list(dict.fromkeys(thirds+[str(i) for i in range(1,7) if str(i)!=head]))
    generated=[f'{head}-{b}-{c}' for b in allseconds for c in allthirds if b!=c and b!=head and c!=head]
    candidates=list(dict.fromkeys(ranked+generated))
    unseen=[x for x in candidates if combo_valid(x) and x[0]==head and x not in hit]
    unseen.sort(key=lambda x:(0 if x[2] not in baseline_second else 1 if x[2] not in core_second else 2,
                            0 if x in ranked else 1,
                            candidates.index(x)))
    out=append_unique(seed,unseen+hit[7:]+balance+hole)
    if len(out)!=10 or len(set(out))!=10:return None
    return out


def pair_coverage(hit, balance, hole):
    """Top7 + uncovered conditional (head, second, third) combinations.

    The ordering is frozen-source rank then reversible source pairs, without
    a newly estimated probability or current odds multiplier.
    """
    head=hit[0][0];seed=hit[:7]
    source=list(dict.fromkeys(hit+balance+hole))
    flips=[f'{a}-{c}-{b}' for x in source for a,b,c in [x.split('-')] if a==head]
    head_source=[x for x in source if x[0]==head]
    seconds=list(dict.fromkeys([x[2] for x in head_source]))
    thirds=list(dict.fromkeys([x[4] for x in head_source]))
    mixed=[f'{head}-{b}-{c}' for b in seconds for c in thirds if b!=c and b!=head and c!=head]
    candidates=[x for x in list(dict.fromkeys(flips+head_source+mixed)) if combo_valid(x) and x not in hit]
    return append_unique(seed,candidates+hit[7:]+balance+hole)


def prepare(root,p,now):
    key=p.stem;c=read(p) or {}
    if not KEY.fullmatch(key) or c.get('race_key')!=key:return None,'bad_race_key'
    due=stamp(c.get('deadline_jst'))
    if not due or not 90<=(due-now).total_seconds()<=900:return None,'outside_predeadline_window'
    saved=stamp(c.get('snapshot_saved_at'));created=stamp(c.get('evidence_committed_at'));proof=first_git(root,p)
    if not saved or not created or not proof or not proof['at'] or not saved<=created<=proof['at']<=now<due or proof['sha256']!=sha(p):
        return None,'unverified_parent_predeadline_commit'
    if (c.get('schema')!='BOAT_EDGE_V232_SITE_PROSPECTIVE_ACCURACY_COHORT_V1' or
        c.get('scope')!='SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH' or
        any(c.get(k) is not False for k in ('formal_results_seen','formal_gate_unlocked','paper_purchases_authorized','real_purchases_authorized')) or
        c.get('model_id')!='SITE_REFERENCE_V122'):
        return None,'invalid_parent_scope_or_guard'
    lists=frozen_lists(c)
    if not lists or lists['hit']!=c.get('top10') or c.get('head_top1')!=lists['hit'][0][0]:return None,'invalid_parent_ticket_policy'
    comps={'hit10':lists['hit'],
           'second_coverage10':second_coverage(lists['hit'],lists['balance'],lists['hole']),
           'pair_coverage10':pair_coverage(lists['hit'],lists['balance'],lists['hole'])}
    if any(not isinstance(v,list) or len(v)!=10 or len(set(v))!=10 or any(not combo_valid(s) for s in v) for v in comps.values()):return None,'comparator_invalid'
    novelty={k:len(set(v)-set(lists['hit'])) for k,v in comps.items()}
    out={'schema':PRE_SCHEMA,'scope':'PRE_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH',
         'race_key':key,'deadline_jst':c['deadline_jst'],'frozen_at':now.isoformat(),
         'parent_sha256':sha(p),'parent_first_commit':proof['commit'],'parent_first_commit_at':proof['at'].isoformat(),
         'model_id':c['model_id'],'comparators':comps,'ticket_novelty_vs_hit10':novelty,
         'research_policy':'PREDECLARED_TOP7_HEAD_SECOND_COVERAGE_AND_PAIR_COVERAGE_NO_ODDS',
         'results_seen_at_freeze':False,'formal_result_access':False,'production_model_changed':False,
         'model_promotion_authorized':False,'accuracy_improvement_proven':False}
    return out,None


def write_once(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:f.write(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n')


def write_if_changed(p,obj,compare):
    old=read(p) or {}
    if p.exists() and all(old.get(k)==obj.get(k) for k in compare):return False
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    return True


def freeze(root,now):
    guard(root)
    day=now.astimezone(JST).strftime('%Y%m%d');base=root/PATH/'v232_cohort';dest=root/PATH/'v240_frozen'
    rejected={};new=0
    for p in sorted(base.glob(day+'-??-??.json')):
        if (dest/p.name).exists():continue
        out,reason=prepare(root,p,now)
        if reason:rejected[reason]=rejected.get(reason,0)+1
        else:write_once(dest/p.name,out);new+=1
    allrows=[read(p) for p in dest.glob(day+'-??-??.json')] if dest.exists() else []
    allrows=[x for x in allrows if x]
    novelty={name:sum(x['ticket_novelty_vs_hit10'][name]>0 for x in allrows) for name in MODES}
    summary={'schema':'BOAT_EDGE_V240_PRE_SUMMARY_V1','day_jst':day,'frozen_today':len(allrows),
             'new_frozen_this_run':new,'comparators':list(MODES),'novel_candidate_races_today':novelty,
             'rejected_current_window':rejected,'production_model_changed':False,'formal_result_access':False,
             'accuracy_improvement_proven':False}
    write_if_changed(root/PATH/'v240_pre_current.json',summary,['day_jst','frozen_today','novel_candidate_races_today','rejected_current_window'])
    print('V240_PRE_RESULT_GUARDED',json.dumps({'new':new,'frozen_today':len(allrows),'novel':novelty,'excluded':rejected},sort_keys=True))
    return summary


def score_one(root,p,now):
    row=read(p) or {};key=p.stem
    if not KEY.fullmatch(key) or row.get('race_key')!=key or row.get('schema')!=PRE_SCHEMA:return None,'not_v240_frozen'
    due=stamp(row.get('deadline_jst'))
    if not due or now<=due+dt.timedelta(minutes=2):return None,'race_not_over'
    first=first_git(root,p)
    if not first or not first['at'] or not first['at']<due or first['sha256']!=sha(p):return None,'candidate_not_git_frozen_before_deadline'
    base=root/PATH/'v232_cohort'/p.name;parent=first_git(root,base)
    if (sha(base)!=row.get('parent_sha256') or not parent or parent['commit']!=row.get('parent_first_commit') or
        parent['sha256']!=sha(base) or not parent['at'] or not parent['at']<due or parent['at'].isoformat()!=row.get('parent_first_commit_at')):
        return None,'parent_provenance_invalid'
    source=root/PATH/'v234_scored'/p.name;official=read(source)
    if (not official or official.get('schema')!='BOAT_EDGE_V234_PRECOMMITTED_SITE_ONLY_RESULT_SCORE_V1' or
        official.get('scope')!='POST_RESULT_SITE_RESEARCH_ONLY_FORMAL_FRESH_LOCKED' or
        official.get('race_key')!=key or official.get('cohort_sha256')!=sha(base)):
        return None,'site_only_v234_result_unavailable'
    commit=first_git(root,source);fetched=stamp(official.get('result_fetched_at'))
    if not commit or not commit['at'] or commit['at']<=due or commit['sha256']!=sha(source) or not fetched or fetched<=due:
        return None,'v234_result_provenance_invalid'
    url=urlsplit(str(official.get('result_source') or ''))
    date,venue,rno=key.split('-')
    if (url.scheme!='https' or url.netloc!='www.boatrace.jp' or url.path!='/owpc/pc/race/raceresult' or
        parse_qs(url.query)!={'hd':[date],'jcd':[venue],'rno':[str(int(rno))]}):return None,'official_source_mismatch'
    win=official.get('winning_combo');comps=row.get('comparators')
    if not combo_valid(win) or not isinstance(comps,dict) or set(comps)!=set(MODES):return None,'bad_outcome_or_comparators'
    if any(not isinstance(v,list) or len(v)!=10 or len(set(v))!=10 or any(not combo_valid(x) for x in v) for v in comps.values()):return None,'invalid_stored_comparator'
    if (official.get('top10_hit') is not (win in comps['hit10'])):return None,'site_baseline_parity_error'
    outcomes={name:win in vals for name,vals in comps.items()}
    return {'schema':SCORE_SCHEMA,'scope':'POST_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH',
            'race_key':key,'winning_combo':win,'frozen_sha256':sha(p),'v234_sha256':sha(source),
            'candidate_git_commit':first['commit'],'result_git_commit':commit['commit'],
            'outcomes':outcomes,'novelty':row['ticket_novelty_vs_hit10'],'production_model_changed':False,
            'model_promotion_authorized':False,'real_or_paper_purchase':False},None


def score(root,now):
    guard(root)
    base=root/PATH/'v240_frozen';dest=root/PATH/'v240_scored';rejected={};new=0
    for p in sorted(base.glob('20??????-??-??.json')) if base.exists() else []:
        if (dest/p.name).exists():continue
        out,reason=score_one(root,p,now)
        if reason:rejected[reason]=rejected.get(reason,0)+1
        else:write_once(dest/p.name,out);new+=1
    rows=[]
    for p in sorted(dest.glob('20??????-??-??.json')) if dest.exists() else []:
        row=read(p)
        if not row or row.get('schema')!=SCORE_SCHEMA or row.get('race_key')!=p.stem or set(row.get('outcomes') or {})!=set(MODES):
            raise RuntimeError('V240_STORED_RESULT_CORRUPT_'+p.stem)
        rows.append(row)
    n=len(rows);summary={}
    for mode in MODES:
        hits=sum(x['outcomes'][mode] for x in rows)
        summary[mode]={'races':n,'hits':hits,'hit_rate_percent':round(100*hits/n,2) if n else None,'points':10,
                       'paired_gain':sum(x['outcomes'][mode] and not x['outcomes']['hit10'] for x in rows),
                       'paired_loss':sum(x['outcomes']['hit10'] and not x['outcomes'][mode] for x in rows),
                       'changed_races':sum(x['novelty'][mode]>0 for x in rows)}
    obj={'schema':'BOAT_EDGE_V240_SCORE_SUMMARY_V1','scope':'POST_RESULT_SITE_RESEARCH_NO_FORMAL_ACCESS',
         'scored_total':n,'new_scored_this_run':new,'comparisons':summary,'pending':rejected,
         'production_model_changed':False,'promotion_authorized':False,'accuracy_improvement_proven':False,
         'status':'DESCRIPTIVE_ONLY_WAIT_INDEPENDENT_MULTIDAY_FRESH',
         'examples':[{'race_key':x['race_key'],'outcomes':x['outcomes']} for x in rows]}
    write_if_changed(root/PATH/'v240_score_current.json',obj,['scored_total','comparisons','pending'])
    print('V240_PAIRED_SITE_ONLY_SCORE',json.dumps({'new':new,'total':n,'comparisons':summary,'pending':rejected},sort_keys=True))
    return obj


def main():
    ap=argparse.ArgumentParser();ap.add_argument('phase',choices=['freeze','score']);ap.add_argument('--root',type=Path,default=Path('.'));ap.add_argument('--now')
    a=ap.parse_args();t=stamp(a.now) if a.now else dt.datetime.now(UTC)
    if not t:raise SystemExit('V240_INVALID_CLOCK')
    root=a.root.resolve()
    if a.phase=='freeze':freeze(root,t)
    else:score(root,t)

if __name__=='__main__':main()
