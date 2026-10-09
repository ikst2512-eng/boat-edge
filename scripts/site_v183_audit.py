"""BOAT EDGE V183: independent prospective V180 site-reference shadow scoring.

Never loads formal Fresh cohorts/results, target 2026-10-09, odds for prediction,
or mutable site model weights. Scores only committed, predeadline 2026-10-10+
V180 shadow artefacts against separately confirmed site results.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

JST=timezone(timedelta(hours=9))
KEY=re.compile(r'^20\d{6}-\d{2}-\d{2}$')
HEX=re.compile(r'^[0-9a-f]{64}$')
GITHEX=re.compile(r'^(?:[0-9a-f]{40}|[0-9a-f]{64})$')
CANDIDATE='V180_SITE_REFERENCE_SHADOW_HEAD_SECOND_THIRD_CONDITIONAL_v1_85_15'
SCOPE='SITE_REFERENCE_PROSPECTIVE_RESEARCH_ONLY_NOT_FORMAL_FRESH'
MODES=(3,5,10)

def combo(s):
    return isinstance(s,str) and bool(re.fullmatch(r'[1-6]-[1-6]-[1-6]',s)) and len(set(s.split('-')))==3

def utc(s):
    try:
        dt=datetime.fromisoformat(str(s).replace('Z','+00:00'))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except (ValueError,TypeError):return None

def json_file(p):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except (OSError,UnicodeError,ValueError):return None

def source_commit(root:Path,relative:str):
    """First adding commit must exist in git history with time < start of race.
    Git log's adding commit is the independent on-repository predeadline marker.
    """
    try:
        p=subprocess.run(['git','log','--diff-filter=A','--format=%H|%cI','--',relative],
                         cwd=root,text=True,capture_output=True,timeout=20,check=True)
        line=next((s.strip() for s in reversed(p.stdout.splitlines()) if '|' in s),None)
        if not line:return None
        sha,when=line.split('|',1)
        if not GITHEX.fullmatch(sha.lower()) or not utc(when):return None
        return {'commit':sha,'time':when}
    except (subprocess.SubprocessError,OSError):return None

def frozen_valid(x,key,added):
    if not KEY.fullmatch(key) or key[:8]<'20261010':return (False,'BEFORE_FUTURE_COHORT')
    if not isinstance(x,dict) or x.get('schema_version')!='boat-edge-v180-site-reference-future-shadow-v1':return (False,'BAD_SHADOW_SCHEMA')
    if x.get('scope')!=SCOPE or x.get('candidate_id')!=CANDIDATE or x.get('race_key')!=key:return (False,'SHADOW_BINDING_MISMATCH')
    if x.get('fresh_validation_pass') is not False or x.get('production_adoption') is not False:return (False,'RESEARCH_FLAGS_TAMPERED')
    if any((x.get('guards') or {}).get(k) is not False for k in ('results_seen','unlock','scoring')):return (False,'PRE_RESULT_GUARDS_MISSING')
    if not HEX.fullmatch(str(x.get('source_sha256',''))) or not HEX.fullmatch(str(x.get('source_race_sha256',''))):return (False,'SOURCE_HASH_MISSING')
    first=utc(x.get('source_first_saved_at'));saved=utc(x.get('source_saved_at'))
    if not first or not saved or first>saved:return (False,'SNAPSHOT_TIMES_INVALID')
    if not added or not utc(added.get('time')):return (False,'NO_INDEPENDENT_ADDITION_COMMIT')
    if not GITHEX.fullmatch(str(added.get('commit','')).lower()):return (False,'COMMIT_HASH_MISSING')
    date=datetime.strptime(key[:8],'%Y%m%d').date()
    # The originally sourced FINAL_15M window cannot be inferred from key's race number.
    # We therefore anchor commitment to the source snapshot clock and its <=15m provenance.
    if saved>utc(added['time']):return (False,'SOURCE_SAVED_AFTER_COMMIT')
    if utc(added['time'])-saved>timedelta(minutes=20):return (False,'FIRST_COMMIT_TOO_LATE_AFTER_SOURCE')
    # No test relies on payout or the outcome to validate the stored prediction.
    ranked=x.get('candidate_ranked_120')
    if not isinstance(ranked,list) or len(ranked)!=120:return (False,'NOT_120_WAY')
    combos=[r.get('combo') if isinstance(r,dict) else None for r in ranked]
    p=[r.get('score') if isinstance(r,dict) else None for r in ranked]
    if any(not combo(c) for c in combos) or len(set(combos))!=120:return (False,'DUPLICATE_OR_INVALID_COMBOS')
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in p):return (False,'SCORES_INVALID')
    if any(p[i]<p[i+1]-1e-12 for i in range(119)) or abs(sum(p)-1)>1e-6:return (False,'RANK_PROBABILITY_INVALID')
    bas=x.get('baseline_top10')
    if not isinstance(bas,list) or len(bas)!=10 or any(not combo(c) for c in bas) or len(set(bas))!=10:return (False,'BASELINE_INVALID')
    for n in MODES:
        if x.get(f'baseline_top{n}')!=bas[:n] or x.get(f'candidate_top{n}')!=combos[:n]:return (False,'TOP_N_MISMATCH')
    # For the on-disk git source, inspect its initially-added blob timestamp.
    # Additional timestamp validation uses the official race deadline if saved in source.
    return (True,'PASS')

def band(p):
    if not isinstance(p,(int,float)) or not math.isfinite(p) or p<=0:return 'payout_unknown'
    if p<1000:return 'under10'
    if p<=2000:return '10to20'
    if p<=5000:return '20to50'
    return 'over50'

def classify(win,top10):
    h,s,t=win.split('-')
    a=[z.split('-') for z in top10 if z.startswith(h+'-')]
    if not a:return 'head_missing'
    yes_s=any(z[1]==s for z in a)
    yes_t=any(z[2]==t for z in a)
    if yes_s and yes_t:return 'pairing_miss'
    if yes_s:return 'third_missing'
    if yes_t:return 'second_missing'
    return 'both_tails_missing'

def score_one(x,result,key,added):
    win=result.get('trifecta')
    if not combo(win):return None
    payout=result.get('trifecta_payout_yen_per_100')
    if not isinstance(payout,(int,float)) or not math.isfinite(payout) or payout<=0:payout=None
    base=x['baseline_top10'];cand=x['candidate_top10']
    b={str(n):win in x[f'baseline_top{n}'] for n in MODES}
    c={str(n):win in x[f'candidate_top{n}'] for n in MODES}
    return {'race_key':key,'added_commit':added['commit'],'added_at':added['time'],
            'source_saved_at':x['source_saved_at'], 'source_sha256':x['source_sha256'],
            'result_status':'confirmed','winning_combo':win,'payout_yen_per_100':payout,'payout_band':band(payout),
            'baseline_hits':b,'candidate_hits':c,
            'baseline_head_top10':any(z[0]==win[0] for z in base),
            'candidate_head_top10':any(z[0]==win[0] for z in cand),
            'baseline_miss_class':None if b['10'] else classify(win,base),
            'candidate_miss_class':None if c['10'] else classify(win,cand)}

def evaluate(root:Path,lookup=source_commit):
    pred_dir=root/'data/site_tail_shadow_v180/predictions'
    out=[];invalid=[];awaiting=0
    # Probe result files only after a validated, precommitted future shadow exists.
    for p in sorted(pred_dir.glob('20??????-??-??.json')):
        key=p.stem
        if not KEY.fullmatch(key) or key[:8]<'20261010':continue
        data=json_file(p)
        rel=p.relative_to(root).as_posix()
        added=lookup(root,rel)
        okay,reason=frozen_valid(data,key,added)
        if not okay:
            invalid.append({'race_key':key,'reason':reason});continue
        # Additional hard stop: first commit before race deadline using *pre-result* source snapshot.
        source=json_file(root/'data/site_prediction_snapshots'/f'{key}.json')
        if isinstance(source,dict) and source.get('race_key')==key and isinstance(source.get('deadline'),str):
            due=utc(key[:4]+'-'+key[4:6]+'-'+key[6:8]+'T'+source['deadline']+':00+09:00')
            if due and (utc(added['time'])>=due or utc(data['source_saved_at'])>=due):
                invalid.append({'race_key':key,'reason':'FIRST_COMMIT_NOT_BEFORE_RACE_DEADLINE'});continue
        else:
            invalid.append({'race_key':key,'reason':'DEADLINE_NOT_IN_SOURCE_SNAPSHOT'});continue
        raw_result=json_file(root/'data/site_results'/f'{key}.json')
        if not isinstance(raw_result,dict) or raw_result.get('status')!='confirmed':
            awaiting+=1;continue
        row=score_one(data,raw_result,key,added)
        if row:out.append(row)
        else:invalid.append({'race_key':key,'reason':'CONFIRMED_RESULT_HAS_NO_VALID_COMBO'})
    groups={}
    for group in ['all','under10','10to20','20to50','over50','payout_unknown']:
        sel=out if group=='all' else [r for r in out if r['payout_band']==group]
        groups[group]={'races':len(sel),
           'baseline_hits':{str(n):sum(r['baseline_hits'][str(n)] for r in sel) for n in MODES},
           'candidate_hits':{str(n):sum(r['candidate_hits'][str(n)] for r in sel) for n in MODES},
           'net_hits':{str(n):sum(r['candidate_hits'][str(n)]-r['baseline_hits'][str(n)] for r in sel) for n in MODES}}
    return {'schema_version':'boat-edge-v183-independent-shadow-score-v1',
            'scope':'POST_SETTLEMENT_FUTURE_SITE_REFERENCE_ONLY_NOT_FORMAL_FRESH',
            'candidate_id':CANDIDATE,'cohort_from':'2026-10-10',
            'status':'RESEARCH_ONLY_NO_ADOPTION' if out else 'WAITING_FOR_FUTURE_COMMITTED_SETTLED_RACES',
            'formal_current_results_accessed':False, 'prediction_weights_changed':False,
            'no_odds_used_for_prediction':True,'pre_result_commit_provenance_required':True,
            'settled_races':len(out),'pending_results':awaiting,
            'invalid_shadows':invalid,'bands':groups,
            'decisions':'NO_PROMOTION_WITHOUT_INDEPENDENT_MULTI_DAY_FRESH',
            'note':'Realized-payout bands are post-settlement diagnostics, never odds-based ticket selection. First-commit time must precede deadline.',
            'races':out}

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path('.'));p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();report=evaluate(a.repo)
    b=(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode('utf-8')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    if not a.out.exists() or a.out.read_bytes()!=b:a.out.write_bytes(b)
    print('V183_REPORT '+json.dumps({'settled_races':report['settled_races'],'pending':report['pending_results'],
              'invalid':len(report['invalid_shadows']),'status':report['status'],'sha256':hashlib.sha256(b).hexdigest()}))

if __name__=='__main__':main()
