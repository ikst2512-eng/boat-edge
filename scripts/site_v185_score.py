"""Independently verify V185 pre-deadline immutability, then score only
confirmed SITE results. Formal Fresh targets and APIs are never opened.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys,re,math
from pathlib import Path
from datetime import datetime,timezone,timedelta
import site_v185_role_shadow as model
import site_v180_shadow as v180

SCOPE='SITE_REFERENCE_UNTOUCHED_FUTURE_RESEARCH_ONLY_NOT_FORMAL_FRESH'
RANKS=(3,5,10)

def sha(b):return hashlib.sha256(b).hexdigest()
def cmd(repo,args):
    try:
        p=subprocess.run(['git',*args],cwd=repo,text=False,capture_output=True,check=True,timeout=20)
        return p.stdout
    except (OSError,subprocess.SubprocessError):return None

def first_commit(repo,path):
    raw=cmd(repo,['log','--diff-filter=A','--format=%H|%cI','--',path]);
    if not raw:return None
    a=raw.decode().strip().splitlines()
    if len(a)!=1:return None # Unexpected duplicate path creation history is not auditable.
    try:
        commit,time=a[0].split('|',1)
        if not re.fullmatch(r'(?:[a-f0-9]{40}|[a-f0-9]{64})',commit) or not model.utc(time):return None
        return {'sha':commit,'time':model.utc(time)}
    except ValueError:return None

def git_blob(repo,rev,path):
    if not re.fullmatch(r'(?:[a-f0-9]{40}|[a-f0-9]{64})',str(rev)):return None
    if not re.fullmatch(r'[\w.\-/]+',str(path)) or '..' in path:return None
    return cmd(repo,['show',f'{rev}:{path}'])

def valid_freeze(root,path):
    key=path.stem
    if not re.fullmatch(r'20\d{6}-\d\d-\d\d',key) or key[:8]<'20261010':return None,'INVALID_COHORT'
    rel=path.relative_to(root).as_posix()
    c=first_commit(root,rel)
    if not c:return None,'NO_INITIAL_GIT_COMMIT'
    stored=path.read_bytes();original=git_blob(root,c['sha'],rel)
    if stored!=original:return None,'MUTATED_SINCE_FIRST_GIT_COMMIT'
    try:doc=json.loads(original)
    except (ValueError,TypeError):return None,'BAD_JSON'
    if doc.get('schema_version')!='boat-edge-v185-prospective-tail-role-shadow-v1' or doc.get('scope')!=SCOPE:return None,'BAD_SCHEMA'
    if doc.get('race_key')!=key or doc.get('candidate_id')!=model.IDENT:return None,'BAD_BINDING'
    if doc.get('approval')!='RESEARCH_ONLY_NOT_PRODUCTION' or doc.get('no_result_read') is not True:return None,'BAD_GUARDS'
    if any(doc.get('guards',{}).get(k) is not False for k in ('results_seen','unlock','scoring')):return None,'BAD_PRE_RESULT_GUARDS'
    deadline=model.utc(f'{key[:4]}-{key[4:6]}-{key[6:8]}T{doc.get("source_deadline")}:00+09:00')
    saved=model.utc(doc.get('source_saved_at'))
    first=model.utc(doc.get('source_first_saved_at'))
    if not deadline or not saved or not first:return None,'INVALID_CLOCKS'
    if not (first<=saved<=c['time']<deadline and c['time']-saved<=timedelta(minutes=20)):
        return None,'COMMIT_NOT_PROVEN_PRE_DEADLINE'
    snap_path=f'data/site_prediction_snapshots/{key}.json'
    race_path=f'data/races/{key}.json'
    scratch_path=f'data/site_scratches_v182/{key}.json'
    source=git_blob(root,c['sha'],snap_path)
    race=git_blob(root,c['sha'],race_path)
    scratchbytes=git_blob(root,c['sha'],scratch_path)
    if not source or not race or not scratchbytes:return None,'SOURCE_BLOBS_NOT_AT_INITIAL_COMMIT'
    if sha(source)!=doc.get('source_snapshot_sha256') or sha(race)!=doc.get('source_race_sha256'):
        return None,'SOURCE_SHA_BINDING_MISMATCH'
    try:
        snapshot=json.loads(source);rac=json.loads(race);scr=json.loads(scratchbytes)
    except (ValueError,UnicodeError):return None,'SOURCE_JSON_INVALID'
    if scr.get('race_key')!=key or scr.get('blocked') is not False:return None,'SCRATCH_NOT_PROVEN_VALID'
    if sha(model.canonical({k:v for k,v in scr.items() if k!='checked_at'}))!=doc.get('source_scratch_sha256'):
        return None,'SCRATCH_SHA_BINDING_MISMATCH'
    if rac.get('race_key')!=key or snapshot.get('race_key')!=key:return None,'SOURCE_RACE_MISMATCH'
    if (rac.get('meta') or {}).get('results_seen') is not False:return None,'RESULT_FLAG_IN_PRE_RESULT_SOURCE'
    expected=model.build(snapshot,source,rac,race,scr,v180)
    if expected is None or model.canonical(expected)!=original:return None,'SHADOW_NOT_REPRODUCIBLE'
    return (doc,c),None

def band(y):
    if not isinstance(y,(int,float)) or not math.isfinite(y) or y<=0:return 'unknown'
    if y<1000:return '<10'
    if y<=2000:return '10-20'
    if y<=5000:return '20-50'
    return '>50'

def scoring(root):
    root=Path(root);rows=[];invalid=[];pending=0
    folder=root/'data/site_tail_shadow_v185/predictions'
    for path in sorted(folder.glob('20??????-??-??.json')):
        verified,why=valid_freeze(root,path)
        if why:invalid.append({'race_key':path.stem,'reason':why});continue
        doc,commit=verified;key=path.stem
        # Read result only after immutable predeadline prediction verification PASS.
        result=model.load_json(root/'data/site_results'/f'{key}.json')
        if not isinstance(result,dict) or result.get('status')!='confirmed':pending+=1;continue
        win=result.get('trifecta')
        if not v180.valid_combo(win):invalid.append({'race_key':key,'reason':'CONFIRMED_RESULT_INVALID'});continue
        payout=result.get('trifecta_payout_yen_per_100')
        if model.num(payout) is None or model.num(payout)<=0:payout=None
        hits={name:{str(n):win in doc[f'{name}_top{n}'] for n in RANKS} for name in ('baseline','v180','candidate')}
        rows.append({'race_key':key,'commit_sha':commit['sha'],'commit_time':commit['time'].isoformat(),
           'winning_combo':win,'payout_yen_per_100':payout,'band':band(payout),'hits':hits,
           'candidate_top15_hit':win in doc['candidate_top15'],
           'candidate_top20_hit':win in doc['candidate_top20']})
    bands={}
    for b in ('all','<10','10-20','20-50','>50','unknown'):
        subset=rows if b=='all' else [r for r in rows if r['band']==b]
        bands[b]={'races':len(subset),'hit':{name:{str(n):sum(r['hits'][name][str(n)] for r in subset) for n in RANKS} for name in ('baseline','v180','candidate')},
            'candidate_top15_hits':sum(r['candidate_top15_hit'] for r in subset),
            'candidate_top20_hits':sum(r['candidate_top20_hit'] for r in subset)}
    return {'schema_version':'boat-edge-v185-post-settlement-independent-site-shadow-v1',
            'scope':'SITE_REFERENCE_RESEARCH_NOT_FORMAL_FRESH',
            'decision':'NO_PRODUCTION_PROMOTION_WITHOUT_MULTIDAY_PROSPECTIVE_IMPROVEMENT',
            'observed_source':'FIRST_COMMITTED_GIT_BLOB_SHA_AND_REPRODUCIBLE_SHADOW',
            'status':'RESEARCH_ONLY' if rows else 'WAITING_FOR_PRE_COMMITTED_FUTURE_SETTLEMENTS',
            'settled_verified':len(rows),'awaiting_result':pending,'invalid':invalid,
            'by_band':bands,'races':rows,
            'production_changed':False,'formal_results_accessed':False}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--repo',type=Path,default=Path('.'));parser.add_argument('--out',type=Path,default=Path('data/site_tail_shadow_v185/evaluation.json'))
    args=parser.parse_args();report=scoring(args.repo);data=json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+'\n'
    path=args.repo/args.out;path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists() or path.read_text(encoding='utf-8')!=data:path.write_text(data,encoding='utf-8')
    print('V185_EVALUATE '+json.dumps({'settled':report['settled_verified'],'pending':report['awaiting_result'],'invalid':len(report['invalid'])}))
