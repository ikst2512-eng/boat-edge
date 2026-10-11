#!/usr/bin/env python3
"""Site-only post-result diagnosis of separately frozen V232/V234 evidence.

Not a new model, Fresh score, V236 challenger or backfilled prediction.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import subprocess

SCHEMA='BOAT_EDGE_V238_SITE_HEAD_TAIL_DIAGNOSTIC_V1'
KEY=re.compile(r'^20\d{6}-\d{2}-\d{2}$')
COMBO=re.compile(r'^[1-6]-[1-6]-[1-6]$')
JST=dt.timezone(dt.timedelta(hours=9))


def read(path):
    try:
        data=json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data,dict) else None
    except (OSError,UnicodeError,ValueError):
        return None


def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def combo_ok(s):
    return isinstance(s,str) and COMBO.fullmatch(s) is not None and len(set(s.split('-')))==3


def timestamp(v):
    try:
        parsed=dt.datetime.fromisoformat(str(v).replace('Z','+00:00'))
        return parsed.astimezone(dt.timezone.utc) if parsed.tzinfo else None
    except (TypeError,ValueError,OverflowError):
        return None


def formal_closed(root):
    obj=read(root/'data/formal_status.json') or {}
    flags=obj.get('guards') or {}
    if any(flags.get(k) is not False for k in ('results_seen','unlock','scoring')) or flags.get('RESULT_UNLOCK_TOKEN') is not None:
        raise RuntimeError('V238_FORMAL_LOCK_NOT_CLOSED')
    if (obj.get('formalFirst100') or {}).get('races') != 0:
        raise RuntimeError('V238_FORMAL_COHORT_NOT_EMPTY')


def first_commit(root,relative):
    try:
        p=subprocess.run(['git','log','--diff-filter=A','--reverse','--format=%H|%cI','--',relative],cwd=root,capture_output=True,text=True,check=False)
        if p.returncode or not p.stdout.strip():return None
        sha,at=p.stdout.splitlines()[0].split('|',1)
        blob=subprocess.run(['git','show',f'{sha}:{relative}'],cwd=root,capture_output=True,check=False)
        if blob.returncode:return None
        return {'commit':sha,'time':timestamp(at),'sha256':hashlib.sha256(blob.stdout).hexdigest()}
    except (OSError,ValueError):return None


def classify(tickets,winning,predicted_head):
    actual_head,actual_second,actual_third=winning.split('-')
    if predicted_head!=actual_head:return 'HEAD_MISS'
    if winning in tickets:return 'EXACT_TOP10_HIT'
    same=[x.split('-') for x in tickets if x.startswith(actual_head+'-')]
    if f'{actual_head}-{actual_third}-{actual_second}' in tickets:return 'SECOND_THIRD_SWAPPED'
    second=any(x[1]==actual_second for x in same)
    third=any(x[2]==actual_third for x in same)
    if not second and not third:return 'SECOND_AND_THIRD_ABSENT'
    if not second:return 'SECOND_ABSENT'
    if not third:return 'THIRD_ABSENT'
    return 'PAIR_COMBINATION_ABSENT'


def verify_pair(root,score_path,require_git=True):
    key=score_path.stem
    score=read(score_path)
    source=root/'data/site_autopilot/v232_cohort'/f'{key}.json'
    cohort=read(source)
    if not KEY.fullmatch(key) or not score or not cohort:raise RuntimeError('V238_UNPAIRED_OR_INVALID_'+key)
    if score.get('schema')!='BOAT_EDGE_V234_PRECOMMITTED_SITE_ONLY_RESULT_SCORE_V1' or cohort.get('schema')!='BOAT_EDGE_V232_SITE_PROSPECTIVE_ACCURACY_COHORT_V1':
        raise RuntimeError('V238_SOURCE_SCHEMA_MISMATCH_'+key)
    if score.get('scope')!='POST_RESULT_SITE_RESEARCH_ONLY_FORMAL_FRESH_LOCKED' or cohort.get('scope')!='SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH':
        raise RuntimeError('V238_SCOPE_MISMATCH_'+key)
    if score.get('race_key')!=key or cohort.get('race_key')!=key or score.get('cohort_sha256')!=hash_file(source):
        raise RuntimeError('V238_COHORT_BYTES_MISMATCH_'+key)
    if any(cohort.get(x) is not False for x in ('formal_results_seen','formal_gate_unlocked','paper_purchases_authorized','real_purchases_authorized')):
        raise RuntimeError('V238_COHORT_GUARD_INVALID_'+key)
    if score.get('model_promotion_authorized') is not False or score.get('accuracy_improvement_proven') is not False:
        raise RuntimeError('V238_PRODUCTION_GUARD_INVALID_'+key)
    deadline=timestamp(cohort.get('deadline_jst'))
    committed=timestamp(score.get('first_git_committed_at'))
    fetched=timestamp(score.get('result_fetched_at'))
    if not deadline or not committed or not fetched or not committed<deadline<fetched:
        raise RuntimeError('V238_TEMPORAL_PROOF_INVALID_'+key)
    if require_git:
        proof=first_commit(root,source.relative_to(root).as_posix())
        if not proof or proof['commit']!=score.get('first_git_commit') or proof['time']!=committed or proof['sha256']!=hash_file(source):
            raise RuntimeError('V238_FIRST_GIT_PROOF_INVALID_'+key)
    win=score.get('winning_combo');top=cohort.get('top10');pred=str(cohort.get('head_top1'))
    if (not combo_ok(win) or not isinstance(top,list) or len(top)!=10 or len(set(top))!=10 or any(not combo_ok(c) for c in top)
            or pred!=str(score.get('head_prediction')) or pred!=top[0][0]
            or score.get('head_hit') is not (win[0]==pred) or score.get('top10_hit') is not (win in top)):
        raise RuntimeError('V238_HEAD_TAIL_PARITY_INVALID_'+key)
    modes=cohort.get('frozen_mode_tickets') or {}
    if not isinstance(modes,dict):raise RuntimeError('V238_MODES_MISSING_'+key)
    matched={}
    for name in ('hit','balance'):
        t=modes.get(name)
        if not isinstance(t,list) or len(t)!=10 or any(not isinstance(v,dict) or not combo_ok(v.get('combo')) for v in t):
            raise RuntimeError('V238_MODE_10PT_INCOMPLETE_'+key)
        combos=[v['combo'] for v in t]
        if len(set(combos))!=10:raise RuntimeError('V238_MODE_DUPLICATE_'+key)
        matched[name]=win in combos
        if (score.get('modes') or {}).get(name,{}).get('hit') is not matched[name]:
            raise RuntimeError('V238_MODE_OUTCOME_PARITY_'+key)
    if [x['combo'] for x in modes['hit']]!=top:raise RuntimeError('V238_TOP10_MODE_PARITY_'+key)
    return {'race_key':key,'venue':score.get('venue'),'winning':win,
        'predicted_head':pred,'actual_head':win[0], 'top10_hit':win in top,
        'reason':classify(top,win,pred), 'balance10_hit':matched['balance'],
        'hit10_hit':matched['hit'], 'cohort_sha256':score['cohort_sha256']}


def build(root,require_git=True):
    formal_closed(root)
    folder=root/'data/site_autopilot/v234_scored'
    rows=[verify_pair(root,p,require_git) for p in sorted(folder.glob('20??????-??-??.json'))] if folder.exists() else []
    types=['EXACT_TOP10_HIT','HEAD_MISS','SECOND_THIRD_SWAPPED','SECOND_AND_THIRD_ABSENT','SECOND_ABSENT','THIRD_ABSENT','PAIR_COMBINATION_ABSENT']
    reason_counts={name:sum(x['reason']==name for x in rows) for name in types}
    n=len(rows);good=sum(r['reason']!='HEAD_MISS' for r in rows)
    comparable={'races':n,'hit10_hits':sum(x['hit10_hit'] for x in rows),'balance10_hits':sum(x['balance10_hit'] for x in rows),
        'both_hit':sum(x['hit10_hit'] and x['balance10_hit'] for x in rows),
        'hit_only':sum(x['hit10_hit'] and not x['balance10_hit'] for x in rows),
        'balance_only':sum(x['balance10_hit'] and not x['hit10_hit'] for x in rows),
        'neither_hit':sum(not x['hit10_hit'] and not x['balance10_hit'] for x in rows)}
    return {'schema':SCHEMA,'scope':'POST_RESULT_V232_V234_SITE_DIAGNOSIS_ONLY_NOT_FORMAL_FRESH_OR_V236_FORWARD',
        'model_id':'SITE_REFERENCE_V122','settled_verified_pairs':n,'head_hits':good,
        'head_correct_and_top10_hit':reason_counts['EXACT_TOP10_HIT'],
        'head_hit_top10_miss':good-reason_counts['EXACT_TOP10_HIT'],
        'head_miss_but_top10_hit':sum(r['reason']=='HEAD_MISS' and r['top10_hit'] for r in rows),
        'reason_counts':reason_counts,'paired_existing_10pt_modes_descriptive':comparable,
        'production_model_changed':False,'promotion_authorized':False,'improvement_proven':False,
        'formal_result_access':False,'odds_used_for_selection':False,
        'notes':'Post-result diagnosis only. No retroactive V236 candidates or new model evidence.',
        'missed_top10_examples':[{'race_key':r['race_key'],'venue':r['venue'],'winning':r['winning'],'reason':r['reason']} for r in rows if not r['top10_hit']][-30:]}


def publish(root,require_git=True):
    summary=build(root,require_git)
    dest=root/'data/site_autopilot/v238_current.json'
    serialized=json.dumps(summary,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    if dest.is_file() and dest.read_text(encoding='utf-8')==serialized:
        print('V238_DIAGNOSTIC_UNCHANGED',summary['settled_verified_pairs']);return False
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(serialized,encoding='utf-8')
    print('V238_SITE_ONLY_TAIL_DIAGNOSTIC',json.dumps({'pairs':summary['settled_verified_pairs'],'reasons':summary['reason_counts']},sort_keys=True))
    return True


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path('.'))
    args=parser.parse_args()
    publish(args.root.resolve())
