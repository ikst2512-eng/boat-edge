"""BOAT EDGE V199: untouched prospective site-only scenario ablations.

No payout/settlement/result source may be opened during freeze. No production
prediction, formal-fresh, or existing immutable V185 files are modified.
"""
from __future__ import annotations
import argparse
from collections import Counter
from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path('.')
JST = timezone(timedelta(hours=9))
START = '20261010'
MODEL = 'V199_UNSEEN_HEAD_SECOND_ORIGINAL_ABLATIONS_V1'
PATH = Path('data/site_shadow_v199')
VERSIONS = ('v185', 'head', 'second', 'original', 'combined')
DATE_RE = re.compile(r'20\d{6}-\d{2}-\d{2}')


def canonical(o):
    return (json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def utc(value):
    try:
        d = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (TypeError, ValueError, OverflowError):
        return None


def num(v):
    if v is None or isinstance(v, bool):
        return None
    try:
        out = float(v)
        return out if math.isfinite(out) else None
    except (ValueError, TypeError):
        return None


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def normalization(values):
    s = sum(values.values())
    if not math.isfinite(s) or s <= 0:
        raise ValueError('NON_POSITIVE_MASS')
    return {k: v/s for k,v in values.items()}


def source_strength(rows, selector, *, faster=False, positive=False):
    """Race-local rank centered score; never interpolate missing or unknown observations."""
    vals = {}
    for h,r in rows.items():
        v = num(selector(r))
        if v is None or (positive and v <= 0):
            continue
        vals[h] = v
    if len(vals) < 4:
        return {}
    out = {}
    for h,v in vals.items():
        less = sum(w < v for w in vals.values())
        equal = sum(w == v for w in vals.values())
        rank = less+(equal-1)/2
        z = 2*rank/(len(vals)-1)-1
        out[h] = -z if faster else z
    return out


def strength_stats(race):
    racers = race.get('racers') or []
    if len(racers) != 6:
        raise ValueError('SIX_PARTICIPANTS_REQUIRED')
    rows = {}
    for r in racers:
        try: h=str(int(r.get('lane')))
        except (TypeError, ValueError):raise ValueError('INVALID_LANE')
        if h not in '123456' or h in rows:raise ValueError('INVALID_OR_DUPLICATE_LANE')
        rows[h]=r
    if len(rows)!=6:raise ValueError('NOT_PERMUTATION_OF_SIX')
    defs={
        'national_win':(lambda r:(r.get('national') or {}).get('win_rate'), False, True),
        'local_win':(lambda r:(r.get('local') or {}).get('win_rate'), False, True),
        'national_quinella':(lambda r:(r.get('national') or {}).get('quinella_rate'), False, True),
        'local_quinella':(lambda r:(r.get('local') or {}).get('quinella_rate'), False, True),
        'motor_quinella':(lambda r:(r.get('motor') or {}).get('quinella_rate'), False, True),
        'average_st':(lambda r:r.get('avg_st'), True, True),
    }
    vals={k:source_strength(rows, f, faster=inv,positive=pos) for k,(f,inv,pos) in defs.items()}
    # Only exhibition COURSE may be used; this is NOT a claim about the final actual entry.
    st = (race.get('beforeinfo') or {}).get('start_exhibition') or []
    courses={}
    for d in st:
        if not isinstance(d,dict):continue
        try:h=str(int(d.get('lane')));c=int(d.get('course'))
        except (TypeError,ValueError):continue
        if h in rows and 1<=c<=6 and h not in courses:courses[h]=c
    reliable_courses = len(courses)==6 and len(set(courses.values()))==6
    course_to_lane={c:h for h,c in courses.items()} if reliable_courses else {}
    stvals={h:num(r.get('st')) for h,r in rows.items()}
    for d in st:
        if not isinstance(d,dict):continue
        try:h=str(int(d.get('lane')))
        except (TypeError,ValueError):continue
        value=num(d.get('st'))
        if h in rows and value is not None and value>=0 and value<=0.5 and d.get('exhibition_f') is not True:
            stvals[h]=value
    # Exhibition ST is optional and is not a proxy for actual race ST.
    vals['exhibition_st']=source_strength({h:{'st':v} for h,v in stvals.items() if v is not None},lambda r:r['st'],faster=True,positive=False)
    return rows,vals,course_to_lane


def weighted_score(h, scores, weights):
    present=[(k,w,scores[k][h]) for k,w in weights if h in scores.get(k,{})]
    if not present:return None
    return sum(w*v for _,w,v in present)/sum(w for _,w,_ in present)


def original_scores(race, source_commit_time):
    audit=(race.get('source_audit') or {}).get('original_exhibition') or {}
    original=race.get('original_exhibition') or {}
    t=utc(audit.get('fetched_at'))
    if audit.get('status')!='ok' or not t or t>source_commit_time or not original:
        return {}, ['ORIGINAL_UNAVAILABLE_AT_FIRST_FROZEN_SOURCE']
    labels=original.get('labels') or []
    if not isinstance(labels,list):return {},['ORIGINAL_BAD_LABELS']
    boats=original.get('boats') or []
    by_label={str(l):{} for l in labels if l in ('一周','まわり足','直線')}
    for entry in boats:
        if not isinstance(entry,dict):continue
        try:h=str(int(entry.get('lane')))
        except (ValueError,TypeError):continue
        if h not in '123456':continue
        for label,value in zip(labels,entry.get('values') or []):
            v=num(value)
            if label in by_label and v is not None and v>0:by_label[label][h]=v
    signals={}
    present=[]
    for label,weight in [('一周',.45),('まわり足',.40),('直線',.15)]:
        source=by_label.get(label,{})
        d=source_strength({h:{'metric':v} for h,v in source.items()},lambda r:r['metric'],faster=True,positive=True)
        if not d:continue
        present.append((label,weight,d))
        for h,val in d.items():
            m=signals.setdefault(h,{'num':0.,'den':0.})
            m['num']+=weight*val;m['den']+=weight
    if not present:return {},['ORIGINAL_LESS_THAN_FOUR_ACTUAL_MEASUREMENTS']
    # Missing lanes are neutral (0 shift); no synthetic measurement is generated.
    return {h:v['num']/v['den'] for h,v in signals.items()},[v[0] for v in present]


def ranked(score_map):
    keys=[f'{h}-{s}-{t}' for h in '123456' for s in '123456' if s!=h for t in '123456' if t not in (h,s)]
    if len(score_map)!=120 or set(score_map)!=set(keys):raise ValueError('INVALID_120_COMBINATIONS')
    if any(v<=0 or not math.isfinite(v) for v in score_map.values()):raise ValueError('INVALID_PROB_MASS')
    nm=normalization(score_map)
    arr=[{'combo':k,'score':v} for k,v in nm.items()]
    arr.sort(key=lambda r:(-r['score'],r['combo']))
    return arr


def reweight_head(base, head_strength, course2lane, stats):
    mass={h:sum(v for key,v in base.items() if key[0]==h) for h in '123456'}
    adj={h:(head_strength.get(h) or 0.0) for h in '123456'}
    if course2lane and all(stats['average_st'].get(course2lane.get(c)) is not None for c in (1,2,4)):
        # A stronger 4-course break against a weaker 2-course wall is a predeclared
        # EXHIBITION-ENTRY scenario only, NOT a guaranteed actual attack.
        h1,h2,h4=[course2lane[c] for c in (1,2,4)]
        attack=clamp((stats['average_st'][h4]-stats['average_st'][h2])/1.0,0,1)
        # source_strength ranks speed so higher is faster
        if attack>0:
            adj[h1]-=.3*attack;adj[h4]+=.3*attack
    logits={h:math.exp(clamp(.95*adj[h],-2,2)) for h in '123456'}
    prior=normalization(logits)
    mixed=normalization({h:.82*mass[h]+.18*prior[h] for h in mass})
    return {combo:p*(mixed[combo[0]]/mass[combo[0]]) for combo,p in base.items()}


def reweight_second(base, second):
    out={}
    for h in '123456':
        mass=sum(p for k,p in base.items() if k[0]==h)
        psec={s:sum(p for k,p in base.items() if k[:3]==h+'-'+s) for s in '123456' if s!=h}
        prior=normalization({s:math.exp(clamp(.95*(second.get(s) or 0),-2,2)) for s in psec})
        desired={s:.65*(p/mass)+.35*prior[s] for s,p in psec.items()}
        for combo,v in base.items():
            if combo[0]!=h:continue
            sec=combo[2]
            out[combo]=v*desired[sec]/(psec[sec]/mass)
    return normalization(out)


def reweight_original(base, orig):
    if not orig:return dict(base)
    out={}
    for h in '123456':
        sub={key:p for key,p in base.items() if key[0]==h}
        total=sum(sub.values())
        aug={}
        for combo,p in sub.items():
            second,third=combo[2],combo[4]
            score=.55*orig.get(second,0.)+.45*orig.get(third,0.)
            aug[combo]=p*math.exp(clamp(.85*score,-2,2))
        den=sum(aug.values())
        for combo,p in sub.items():out[combo]=.70*p+.30*total*aug[combo]/den
    return normalization(out)


def generate(v185, race, source_commit_time):
    key=v185['race_key']
    if v185.get('candidate_id')!='V185_THIRD_ROLE_TRIO_EXHIBITION_CONDITIONAL_70_30_V1':
        raise ValueError('PARENT_MODEL_ID_MISMATCH')
    parent=v185['candidate_ranked_120']
    baseline={r['combo']:num(r['score']) for r in parent}
    if any(v is None for v in baseline.values()):raise ValueError('BAD_PARENT_SCORES')
    parent_rank=ranked(baseline)
    if [r['combo'] for r in parent_rank]!=[r['combo'] for r in parent]:
        raise ValueError('PARENT_120_RANK_MISMATCH')
    rows,features,courses=strength_stats(race)
    head={h:weighted_score(h,features,[('national_win',.45),('local_win',.10),('motor_quinella',.20),('average_st',.25)]) for h in rows}
    # Missing features remain neutral; zero is not an inferred quality estimate.
    head={h:val for h,val in head.items() if val is not None}
    second={h:weighted_score(h,features,[('national_quinella',.35),('local_quinella',.15),('motor_quinella',.15),('average_st',.25),('exhibition_st',.10)]) for h in rows}
    second={h:val for h,val in second.items() if val is not None}
    orig,orig_sources=original_scores(race,source_commit_time)
    head_map=reweight_head(baseline,head,courses,features)
    second_map=reweight_second(baseline,second)
    orig_map=reweight_original(baseline,orig)
    combined=reweight_original(reweight_second(head_map,second),orig)
    variants={'v185':dict(baseline),'head':head_map,'second':second_map,'original':orig_map,'combined':combined}
    ranks={k:ranked(v) for k,v in variants.items()}
    def mass_by_head(rr):
        return {h:sum(x['score'] for x in rr if x['combo'][0]==h) for h in '123456'}
    for v in ('second','original'):
        assert all(abs(mass_by_head(ranks[v])[h]-mass_by_head(ranks['v185'])[h])<1e-9 for h in '123456')
    assert ranks['original']==ranks['v185'] if not orig else True
    return ranks,{'original_features_available_at_freeze':orig_sources,
        'original_branch_abstains_no_source':not bool(orig),
        'exhibition_course_available_at_freeze':len(courses)==6,
        'head_features':sorted({k for k in features if features[k]}),
        'second_features':sorted({k for k in features if features[k]}),
        'head_mass_changed':any(abs(mass_by_head(ranks['head'])[h]-mass_by_head(ranks['v185'])[h])>1e-10 for h in '123456')}


def load_parent_from_git(root, parent_file):
    sys.path.insert(0,str((root/'scripts').resolve()))
    import site_v185_score as scorer
    verified,error=scorer.valid_freeze(root,parent_file)
    if error:return None,error
    document,commit=verified
    key=parent_file.stem
    race_raw=scorer.git_blob(root,commit['sha'],f'data/races/{key}.json')
    if not race_raw:return None,'NO_PARENT_INITIAL_COMMIT_RACE_SOURCE'
    race=json.loads(race_raw)
    return (document,commit,race_raw,race),None


def make(doc,commit,race_raw,race,modelhash,source_commit_time):
    ranks,metadata=generate(doc,race,source_commit_time)
    key=doc['race_key']
    return {'schema_version':'boat-edge-v199-unseen-prospective-ablation-v1',
        'scope':'RESEARCH_ONLY_NOT_FORMAL_FRESH', 'model_id':MODEL,'model_script_sha256':modelhash,
        'race_key':key,'parent_v185_first_commit_sha':commit['sha'],
        'parent_v185_document_sha256':sha(canonical(doc)),
        'v199_race_source_sha256':sha(race_raw),
        'v199_race_original_audit_status':((race.get('source_audit') or {}).get('original_exhibition') or {}).get('status'),
        'deadline':doc['source_deadline'],'source_first_saved_at':doc['source_first_saved_at'],
        'v185_first_commit_time':commit['time'].isoformat(),
        'features':metadata,
        'candidate_top3':{k:[x['combo'] for x in arr[:3]] for k,arr in ranks.items()},
        'candidate_top5':{k:[x['combo'] for x in arr[:5]] for k,arr in ranks.items()},
        'candidate_top10':{k:[x['combo'] for x in arr[:10]] for k,arr in ranks.items()},
        'ranked_120':ranks,
        'approval':'RESEARCH_ONLY_NO_PRODUCTION_ADOPTION',
        'pre_result_guard':{'results_seen':False,'unlock':False,'scoring':False},
        'no_payout_or_result_read_before_prediction_commit':True}


def repo_run(root,args):
    try:return subprocess.run(['git',*args],cwd=root,capture_output=True,check=True,timeout=30).stdout
    except (OSError,subprocess.SubprocessError):return None


def first_commit(root,path):
    out=repo_run(root,['log','--diff-filter=A','--format=%H|%cI','--',path]);
    if not out:return None
    lines=out.decode().strip().splitlines()
    if len(lines)!=1:return None
    try:h,t=lines[0].split('|');return {'sha':h,'time':utc(t)}
    except (TypeError,ValueError):return None


def frozen_at_commit(root,commit,path):
    return repo_run(root,['show',f'{commit}:{path}'])


def safe_current_pre_result_source(root,key,now):
    file=root/'data/races'/f'{key}.json'
    try:
        raw=file.read_bytes();race=json.loads(raw)
    except (OSError,ValueError,UnicodeError):return None
    meta=race.get('meta') or {}
    if race.get('race_key')!=key or meta.get('date')!=f'{key[:4]}-{key[4:6]}-{key[6:8]}':return None
    if meta.get('phase')!='PRE_RESULT' or any(meta.get(k) is not False for k in ('results_seen','unlock','scoring')):return None
    if any((race.get('validation') or {}).get(k) not in (None,False) for k in ('result','result_unlock_token')):return None
    audit=race.get('source_audit') or {};card=audit.get('race_card') or {}
    t=utc(card.get('fetched_at'))
    if card.get('status')!='ok' or not t or t>now or now-t>timedelta(minutes=20):return None
    bt=(audit.get('beforeinfo') or {})
    btime=utc(bt.get('fetched_at'))
    if bt.get('status')!='ok' or not btime or btime>now or now-btime>timedelta(minutes=16):return None
    if len(race.get('racers') or [])!=6:return None
    return raw,race


def predict(root,now,modelhash):
    dst=root/PATH/'predictions';dst.mkdir(parents=True,exist_ok=True)
    frozen=abstained=expired=invalid=0
    for p in sorted((root/'data/site_tail_shadow_v185/predictions').glob('20??????-??-??.json')):
        key=p.stem
        if not DATE_RE.fullmatch(key) or key[:8]<START or key[:8]!=now.astimezone(JST).strftime('%Y%m%d'):continue
        if (dst/f'{key}.json').exists():continue
        try:due=utc(f'{key[:4]}-{key[4:6]}-{key[6:8]}T{key_deadline(root,p)}:00+09:00')
        except (TypeError,ValueError):due=None
        if not due or not timedelta(minutes=2)<due-now<=timedelta(minutes=15):expired+=1;continue
        pair,err=load_parent_from_git(root,p)
        if err:invalid+=1;continue
        doc,commit,old_race_raw,old_race=pair
        current=safe_current_pre_result_source(root,key,now)
        if not current:
            invalid+=1;continue
        race_raw,race=current
        if now>=due-timedelta(minutes=2):expired+=1;continue
        try:data=make(doc,commit,race_raw,race,modelhash,now)
        except (ValueError,AssertionError,OverflowError):invalid+=1;continue
        assert canonical(data)==canonical(make(doc,commit,race_raw,race,modelhash,now)),'NONDETERMINISTIC'
        with (dst/f'{key}.json').open('xb') as f:f.write(canonical(data))
        frozen+=1
        if data['features']['original_branch_abstains_no_source']:abstained+=1
    return {'newly_frozen':frozen,'original_abstentions':abstained,'not_yet_or_no_longer_eligible':expired,
        'invalid_parent_or_features':invalid,'formal_touched':False,'result_access':False}


def key_deadline(root,p):
    try:return json.loads(p.read_text(encoding='utf-8')).get('source_deadline')
    except (OSError,ValueError,UnicodeError):return None


def safe_frozen_metadata(race,key,now):
    meta=race.get('meta') or {}
    if race.get('race_key')!=key or meta.get('date')!=f'{key[:4]}-{key[4:6]}-{key[6:8]}':return False
    if meta.get('phase')!='PRE_RESULT' or any(meta.get(k) is not False for k in ('results_seen','unlock','scoring')):return False
    if any((race.get('validation') or {}).get(k) not in (None,False) for k in ('result','result_unlock_token')):return False
    audit=race.get('source_audit') or {}
    card=audit.get('race_card') or {};ct=utc(card.get('fetched_at'))
    before=audit.get('beforeinfo') or {};bt=utc(before.get('fetched_at'))
    if card.get('status')!='ok' or not ct or ct>now:return False
    if before.get('status')!='ok' or not bt or bt>now:return False
    return len(race.get('racers') or [])==6


def verify_self(root,path,modelhash):
    if path.stem[:8]<START:return None,'BEFORE_START'
    rel=path.relative_to(root).as_posix()
    initial=first_commit(root,rel)
    if not initial or not initial['time']:return None,'NO_INITIAL_COMMIT'
    old=frozen_at_commit(root,initial['sha'],rel)
    if not old or old!=path.read_bytes():return None,'MUTATED_PREDICTION'
    try:doc=json.loads(old)
    except (ValueError,UnicodeError):return None,'INVALID_JSON'
    if doc.get('model_id')!=MODEL or doc.get('model_script_sha256')!=modelhash:return None,'MODEL_SHA_MISMATCH'
    if doc.get('race_key')!=path.stem or doc.get('scope')!='RESEARCH_ONLY_NOT_FORMAL_FRESH':return None,'SCOPE_MISMATCH'
    if doc.get('approval')!='RESEARCH_ONLY_NO_PRODUCTION_ADOPTION':return None,'APPROVAL_MISMATCH'
    if any(doc.get('pre_result_guard',{}).get(k) is not False for k in ('results_seen','unlock','scoring')):return None,'GUARD_MISMATCH'
    due=utc(f'{path.stem[:4]}-{path.stem[4:6]}-{path.stem[6:8]}T{doc.get("deadline")}:00+09:00')
    if not due or not initial['time']<due or initial['time']<utc(doc.get('v185_first_commit_time')):
        return None,'NOT_FROZEN_PREDEADLINE'
    parent=root/'data/site_tail_shadow_v185/predictions'/path.name
    pair,err=load_parent_from_git(root,parent)
    if err:return None,'PARENT_'+err
    parent_doc,commit,old_race_raw,old_race=pair
    # Use the race file FROM V199's initial commit, not mutable current race
    # data (and never use data added after that commit).
    race_raw=frozen_at_commit(root,initial['sha'],f'data/races/{path.stem}.json')
    if not race_raw or sha(race_raw)!=doc.get('v199_race_source_sha256'):
        return None,'INITIAL_COMMIT_RACE_SOURCE_SHA_MISMATCH'
    try:race=json.loads(race_raw)
    except (TypeError,ValueError,UnicodeError):return None,'BAD_FROZEN_RACE_SOURCE'
    if doc.get('parent_v185_first_commit_sha')!=commit['sha'] or doc.get('parent_v185_document_sha256')!=sha(canonical(parent_doc)):
        return None,'PARENT_SOURCE_SHA_MISMATCH'
    if not safe_frozen_metadata(race,path.stem,initial['time']):return None,'FROZEN_RACE_NOT_PRE_RESULT'
    expected=make(parent_doc,commit,race_raw,race,modelhash,initial['time'])
    if canonical(expected)!=old:return None,'REPLAY_MISMATCH'
    return doc,None


def classify_top10(winner,combos):
    if winner in combos:return 'TOP10_HIT'
    h,second,_=winner.split('-')
    if not any(c.startswith(h+'-') for c in combos):return 'HEAD_ABSENT'
    if not any(c.startswith(h+'-'+second+'-') for c in combos):return 'SECOND_ABSENT'
    return 'THIRD_ABSENT'


def scoring(root,modelhash):
    # Site-only results are read ONLY after verifying the first-committed V199
    # candidate, its V185 parent and every original prediction source checksum.
    rows=[];pending=0;invalid=[]
    sys.path.insert(0,str((root/'scripts').resolve()))
    import site_v180_shadow as v180
    import site_v185_role_shadow as v185
    pred_folder=root/PATH/'predictions'
    for p in sorted(pred_folder.glob('20??????-??-??.json')):
        doc,error=verify_self(root,p,modelhash)
        if error:invalid.append({'race_key':p.stem,'reason':error});continue
        result=v185.load_json(root/'data/site_results'/p.name)
        if not isinstance(result,dict) or result.get('status')!='confirmed':pending+=1;continue
        winner=result.get('trifecta')
        if not v180.valid_combo(winner):invalid.append({'race_key':p.stem,'reason':'INVALID_CONFIRMED_RESULT'});continue
        payout=num(result.get('trifecta_payout_yen_per_100'))
        band=('unknown' if payout is None or payout<=0 else '<10' if payout<1000 else '10-20' if payout<=2000 else '20-50' if payout<=5000 else '>50')
        hits={v:{str(n):winner in doc[f'candidate_top{n}'][v] for n in (3,5,10)} for v in VERSIONS}
        miss={v:classify_top10(winner,doc['candidate_top10'][v]) for v in VERSIONS}
        top1head={v:doc['ranked_120'][v][0]['combo'][0]==winner[0] for v in VERSIONS}
        rows.append({'race_key':p.stem,'winner':winner,'band':band,'hits':hits,
            'top10_miss_classes':miss,'top1_head_hits':top1head,
            'actual_non1_head':winner[0]!='1',
            'original_abstained':doc['features']['original_branch_abstains_no_source'],
            'top10_new_combos':{v:len(set(doc['candidate_top10'][v])-set(doc['candidate_top10']['v185'])) for v in VERSIONS[1:]}})
    def aggregate(subset):
        return {'races':len(subset),
            'hits':{v:{str(n):sum(x['hits'][v][str(n)] for x in subset) for n in (3,5,10)} for v in VERSIONS},
            'top1_head_hits':{v:sum(x['top1_head_hits'][v] for x in subset) for v in VERSIONS},
            'top10_miss_classes':{v:dict(sorted(Counter(x['top10_miss_classes'][v] for x in subset).items())) for v in VERSIONS},
            'top10_new_combo_count':{v:sum(x['top10_new_combos'][v] for x in subset) for v in VERSIONS[1:]}}
    bands={b:aggregate(rows if b=='all' else [r for r in rows if (r['actual_non1_head'] if b=='non1_head' else r['band']==b)]) for b in ('all','non1_head','10-20','<10','20-50','>50','unknown')}
    return {'schema_version':'boat-edge-v199-independent-future-only-score-v1',
        'model_id':MODEL,'scope':'SITE_REFERENCE_RESEARCH_ONLY_NOT_FORMAL_FRESH',
        'decision':'NOT_ADOPTABLE_WITHOUT_MULTIDAY_FRESH_PRECOMMIT_GAINS',
        'settled_verified':len(rows),'pending_results':pending,'invalid':invalid,
        'by_band':bands,'races':rows,
        'result_access':'ONLY_CONFIRMED_SITE_FILE_AFTER_ALL_PRE_RESULT_GIT_CHECKS',
        'formal_results_accessed':False,'production_model_changed':False}


def self_test():
    import itertools
    arr={f'{h}-{s}-{t}':1+(int(h)==1)*9 + int(s==2)*2 for h,s,t in itertools.permutations('123456',3)}
    arr=normalization(arr)
    racers=[]
    for i in range(1,7):
        racers.append({'lane':i,'avg_st':.10+i*.01,'national':{'win_rate':5+i*.25,'quinella_rate':21+i*4},
            'local':{'win_rate':3+i*.1,'quinella_rate':20+i*2},'motor':{'quinella_rate':31+i}})
    mock={'racers':racers,'beforeinfo':{'start_exhibition':[{'lane':i,'course':i,'st':str(.12+i*.01)} for i in range(1,7)]},
          'source_audit':{'original_exhibition':{'status':'missing','fetched_at':None}}}
    parent={'race_key':'20261011-23-01','candidate_id':'V185_THIRD_ROLE_TRIO_EXHIBITION_CONDITIONAL_70_30_V1',
        'candidate_ranked_120':ranked(arr)}
    ranks,meta=generate(parent,mock,utc('2026-10-11T01:00:00Z'))
    assert len(ranks)==len(VERSIONS)==5
    assert all(len(r)==120 and abs(sum(x['score'] for x in r)-1)<1e-9 for r in ranks.values())
    assert meta['original_branch_abstains_no_source'] and ranks['original']==ranks['v185']
    assert set(x['combo'] for x in ranks['head'][:10]) != set(x['combo'] for x in ranks['v185'][:10]) or meta['head_mass_changed']
    for mode in ('second','original'):
        for h in '123456':
            pm=sum(x['score'] for x in ranks['v185'] if x['combo'][0]==h)
            qm=sum(x['score'] for x in ranks[mode] if x['combo'][0]==h)
            assert abs(pm-qm)<1e-9,(mode,h,pm,qm)
    assert canonical(ranks)==canonical(generate(parent,mock,utc('2026-10-11T01:00:00Z'))[0])
    assert not original_scores(mock,utc('2026-10-11T01:00:00Z'))[0]
    assert classify_top10('1-2-3',['1-2-3'])=='TOP10_HIT'
    assert classify_top10('3-1-2',['1-2-3'])=='HEAD_ABSENT'
    assert classify_top10('1-3-2',['1-2-3'])=='SECOND_ABSENT'
    assert classify_top10('1-2-5',['1-2-3'])=='THIRD_ABSENT'
    # Positive actual original source only if its acquisition precedes the freeze.
    mock['original_exhibition']={'labels':['一周','まわり足','直線'],'boats':[{'lane':i,'values':[35+i*.13,5+i*.1,6+i*.08]} for i in range(1,7)]}
    mock['source_audit']['original_exhibition']={'status':'ok','fetched_at':'2026-10-11T00:59:00Z'}
    r,metadata=generate(parent,mock,utc('2026-10-11T01:00:00Z'))
    assert not metadata['original_branch_abstains_no_source']
    assert r['original']!=r['v185']
    mock['source_audit']['original_exhibition']['fetched_at']='2026-10-11T01:02:00Z'
    assert generate(parent,mock,utc('2026-10-11T01:00:00Z'))[1]['original_branch_abstains_no_source']
    print('V199_SELFTEST_120_COMBOS_HEAD_MASS_ROLE_ISOLATION_ORIGINAL_CUTOFF_REPLAY_PASS')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=('self-test','freeze','score'))
    parser.add_argument('--repo',default='.')
    parser.add_argument('--model-sha',default=None)
    parser.add_argument('--out',default=None)
    opts=parser.parse_args()
    if opts.action=='self-test':return self_test()
    global ROOT
    ROOT=Path(opts.repo).resolve()
    modelhash=sha(Path(__file__).read_bytes())
    if opts.model_sha and modelhash!=opts.model_sha:raise SystemExit('V199_MODEL_SHA_MISMATCH')
    if opts.action=='freeze':
        doc=predict(ROOT,datetime.now(timezone.utc),modelhash)
        print('V199_PRE_RESULT_FUTURE_FREEZE '+json.dumps(doc,sort_keys=True,ensure_ascii=False))
    else:
        result=scoring(ROOT,modelhash)
        if result['invalid']:
            print('V199_INVALID_FROZEN_NO_SCORE_PUBLICATION '+json.dumps(result['invalid'],sort_keys=True,ensure_ascii=False))
            raise SystemExit(3)
        dst=ROOT/(opts.out or str(PATH/'evaluation.json'));dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_bytes(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False).encode()+b'\n')
        print('V199_VERIFIED_FUTURE_SCORE '+json.dumps({'settled':result['settled_verified'],'pending':result['pending_results'],'status':result['decision']}))


if __name__=='__main__':main()
