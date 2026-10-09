"""BOAT EDGE V180: prospective site-reference tail-conditional shadow freeze.

Research-only, strictly PRE_RESULT. Does not import prediction-history,
results, payout, combined API, formal-Fresh, or alter production models.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

JST = timezone(timedelta(hours=9))
FIRST_DATE = '20261010'  # NEVER backfill 2026-10-09 settled research cohort.
POLICY = 'BALANCE10_WAVE12_15_18_V133_FIXED'
ALGO = 'V180_SITE_REFERENCE_SHADOW_HEAD_SECOND_THIRD_CONDITIONAL_v1_85_15'
RACE_RE = re.compile(r'^20\d{6}-\d{2}-\d{2}$')

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def canon(x) -> bytes:
    return (json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')

def parse_utc(x):
    try:
        d = datetime.fromisoformat(str(x).replace('Z', '+00:00'))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (TypeError, ValueError):
        return None

def valid_combo(combo):
    return isinstance(combo, str) and bool(re.fullmatch(r'[1-6]-[1-6]-[1-6]', combo)) and len(set(combo.split('-')))==3

def cutoff_ok(snap, key, now):
    if not RACE_RE.fullmatch(key) or key[:8] < FIRST_DATE:
        return False
    if key[:8] != now.astimezone(JST).strftime('%Y%m%d'):
        return False
    if snap.get('schema_version')!='boat-edge-server-site-final-v123' or snap.get('snapshot_window')!='FINAL_15M':
        return False
    if snap.get('race_key')!=key or snap.get('prediction_kind')!='SITE_REFERENCE_V122' or snap.get('mode_policy')!=POLICY:
        return False
    g=snap.get('guards') or {}
    if any(g.get(n) is not False for n in ('results_seen','unlock','scoring')):
        return False
    deadline=str(snap.get('deadline') or '')
    if not re.fullmatch(r'\d{2}:\d{2}', deadline):
        return False
    try:
        due=datetime.strptime(key[:8]+deadline,'%Y%m%d%H:%M').replace(tzinfo=JST).astimezone(timezone.utc)
    except ValueError:
        return False
    saved=parse_utc(snap.get('saved_at'))
    first=parse_utc(snap.get('first_saved_at'))
    if not saved or not first or first>saved or saved>now or due<=now:
        return False
    remain=(due-now).total_seconds()/60
    saved_remain=(due-saved).total_seconds()/60
    if not (0 < remain <= 15 and 0 < saved_remain <= 16):
        return False
    try:
        claimed=float(snap['minutes_to_deadline'])
    except (TypeError,ValueError,KeyError):
        return False
    if abs(claimed-saved_remain)>1.5:
        return False
    if not re.fullmatch(r'[a-f0-9]{64}',str(snap.get('race_sha256') or '')):
        return False
    modes=snap.get('modes') or {}
    hit=(modes.get('hit') or {}).get('tickets') or []
    hole=(modes.get('hole') or {}).get('tickets') or []
    if len(hit)!=10 or len(hole) not in (12,15,18):
        return False
    for rows in (hit,hole):
        names=[r.get('combo') for r in rows if isinstance(r,dict)]
        if len(names)!=len(rows) or len(set(names))!=len(names) or any(not valid_combo(c) for c in names):
            return False
        if any(not isinstance(r.get('p'),(int,float)) or not math.isfinite(r['p']) or r['p']<0 for r in rows):
            return False
    return True

def normalize(d):
    total=sum(max(0.0,float(v)) for v in d.values())
    if total==0:return {k:1/len(d) for k in d}
    return {k:max(0.,float(v))/total for k,v in d.items()}

def candidate_rows(snap):
    """Predeclared shadow only: mixture of same-engine projections, not calibrated chances.

    For each head h, estimate P(h), P(second|h), P(third|h,second).
    Backoff to global position and head-specific third distributions; no post-result tuning.
    Odds, payout and manual high-price bonuses are NEVER inputs.
    """
    modes=snap['modes']
    masses={}
    for mode,blend in (('hit',.85),('hole',.15)):
        rows=modes[mode]['tickets']
        vals=[max(0.,float(r['p'])) for r in rows]
        denom=sum(vals)
        if not denom:vals=[1.]*len(rows);denom=len(rows)
        for r,v in zip(rows,vals):
            c=r['combo'];masses[c]=masses.get(c,0.)+blend*v/denom
    heads={h:0. for h in '123456'}
    seconds={h:{s:0. for s in '123456' if s!=h} for h in '123456'}
    thirds={h:{t:0. for t in '123456' if t!=h} for h in '123456'}
    pairs={(h,s):{t:0. for t in '123456' if t not in (h,s)} for h in '123456' for s in '123456' if s!=h}
    gsecond={s:0. for s in '123456'}
    gthird={t:0. for t in '123456'}
    for combo,w in masses.items():
        h,s,t=combo.split('-')
        heads[h]+=w;seconds[h][s]+=w;thirds[h][t]+=w;pairs[h,s][t]+=w;gsecond[s]+=w;gthird[t]+=w
    headP=normalize({h:.98*heads[h]+.02/6 for h in heads})
    scored=[]
    for h in '123456':
        secData=normalize({s:seconds[h][s]+.001 for s in seconds[h]})
        secGlobal=normalize({s:gsecond[s]+.001 for s in seconds[h]})
        secP=normalize({s:.70*secData[s]+.30*secGlobal[s] for s in seconds[h]})
        for s in secP:
            thirdLocal=normalize({t:pairs[h,s][t]+.003 for t in pairs[h,s]})
            thirdHead=normalize({t:thirds[h][t]+.003 for t in pairs[h,s]})
            thirdGlobal=normalize({t:gthird[t]+.003 for t in pairs[h,s]})
            thirdP=normalize({t:.60*thirdLocal[t]+.30*thirdHead[t]+.10*thirdGlobal[t] for t in pairs[h,s]})
            for t in thirdP:
                scored.append({'combo':f'{h}-{s}-{t}', 'score':headP[h]*secP[s]*thirdP[t]})
    scored.sort(key=lambda r:(-r['score'],r['combo']))
    if len(scored)!=120 or abs(sum(r['score'] for r in scored)-1)>1e-9 or len({r['combo'] for r in scored})!=120:
        raise ValueError('SHADOW_120_INVALID')
    return scored

def freeze(snap, key, original_bytes):
    base=[r['combo'] for r in snap['modes']['hit']['tickets']]
    candidate=candidate_rows(snap)
    return {
        'schema_version':'boat-edge-v180-site-reference-future-shadow-v1',
        'scope':'SITE_REFERENCE_PROSPECTIVE_RESEARCH_ONLY_NOT_FORMAL_FRESH',
        'race_key':key,
        'source_saved_at':snap['saved_at'],
        'source_first_saved_at':snap['first_saved_at'],
        'source_sha256':sha(original_bytes),
        'source_race_sha256':snap['race_sha256'],
        'source_mode_policy':POLICY,
        'candidate_id':ALGO,
        'candidate_predeclared_weights':{'hit':.85,'hole':.15},
        'baseline_top3':base[:3], 'baseline_top5':base[:5], 'baseline_top10':base,
        'candidate_top3':[x['combo'] for x in candidate[:3]],
        'candidate_top5':[x['combo'] for x in candidate[:5]],
        'candidate_top10':[x['combo'] for x in candidate[:10]],
        'candidate_ranked_120':candidate,
        'research_note':'Relative shadow scores are not calibrated win probabilities. No outcome was read; no weights/production were changed.',
        'guards':{'results_seen':False,'unlock':False,'scoring':False},
        'fresh_validation_pass':False,'production_adoption':False
    }

def run(root,now):
    dest=root/'data/site_tail_shadow_v180/predictions'
    sources=root/'data/site_prediction_snapshots'
    checked=created=existing=0
    for path in sorted(sources.glob('20??????-??-??.json')):
        key=path.stem
        if key[:8]!=now.astimezone(JST).strftime('%Y%m%d') or key[:8]<FIRST_DATE:
            continue
        target=dest/f'{key}.json'
        if target.exists():
            existing+=1
            # Immutable: never rewrite the frozen prospective artefact.
            continue
        raw=path.read_bytes()
        try:snap=json.loads(raw)
        except (ValueError,UnicodeDecodeError):continue
        if not cutoff_ok(snap,key,now):continue
        checked+=1
        candidate=freeze(snap,key,raw)
        assert canon(candidate)==canon(freeze(snap,key,raw)), 'NONDETERMINISTIC_FREEZE'
        dest.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as fh:fh.write(canon(candidate))
        created+=1
    return {'candidate_id':ALGO,'fresh_only_from':FIRST_DATE,'newly_frozen':created,
            'eligible_now':checked,'already_immutable':existing,
            'no_outcome_read':True,'formal_lane_modified':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path('.'))
    a=p.parse_args()
    print(json.dumps(run(a.repo,datetime.now(timezone.utc)),ensure_ascii=False,sort_keys=True))
