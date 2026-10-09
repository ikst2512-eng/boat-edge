"""V185 prospective THIRD-ROLE challenger. NEVER opens outcome/result/payout data.

Site reference research only, not the independent formal Fresh lane.
Uses the V180 committed-before-result source snapshot plus race PRE_RESULT
features, not historical outcome-selected odds or settlement data.
"""
from __future__ import annotations
import argparse, hashlib, json, math, re, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

JST=timezone(timedelta(hours=9))
START='20261010'
IDENT='V185_THIRD_ROLE_TRIO_EXHIBITION_CONDITIONAL_70_30_V1'
REQUIRED_POLICY='BALANCE10_WAVE12_15_18_V133_FIXED'
SHA=lambda b:hashlib.sha256(b).hexdigest()
def canonical(x):return (json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode()

def load_json(path):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError,UnicodeError):return None

def utc(s):
    try:
        d=datetime.fromisoformat(str(s).replace('Z','+00:00'))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (ValueError,TypeError):return None

def num(x):
    if x is None or isinstance(x,bool) or (isinstance(x,str) and not x.strip()):return None
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except (ValueError,TypeError):return None

def differences(rows,attr,invert=False):
    """Rank-centered source measurements. Missing values make NO contribution."""
    vals={i:num(attr(i,r)) for i,r in rows.items()}
    good=sorted(((i,v) for i,v in vals.items() if v is not None),key=lambda iv:(iv[1],iv[0]))
    if len(good)<4:return {}
    # Ties receive identical average ranks, no arbitrary boat-ID advantage.
    out={}
    for i,v in good:
        less=sum(1 for _,x in good if x<v)
        equal=sum(1 for _,x in good if x==v)
        rank=less+(equal-1)/2
        score=(2*rank/(len(good)-1))-1
        out[i]= -score if invert else score
    return out

def role_strength(race):
    racers={int(r['lane']):r for r in race.get('racers',[]) if isinstance(r,dict) and str(r.get('lane','')).isdigit() and 1<=int(r['lane'])<=6}
    if len(racers)!=6 or len(set(racers))!=6:return None
    before=race.get('beforeinfo') or {}
    ex={int(r['lane']):r for r in before.get('racers',[]) if isinstance(r,dict) and str(r.get('lane','')).isdigit() and 1<=int(r['lane'])<=6}
    st={int(r['lane']):r for r in before.get('start_exhibition',[]) if isinstance(r,dict) and str(r.get('lane','')).isdigit() and 1<=int(r['lane'])<=6}
    original=race.get('original_exhibition') or {}
    lab=[str(x) for x in original.get('labels',[]) if isinstance(x,str)]
    ol={}
    for r in original.get('boats',[]):
        if not isinstance(r,dict):continue
        try:lane=int(r.get('lane'))
        except (ValueError,TypeError):continue
        if lane not in racers:continue
        ol[lane]={k:num(v) for k,v in zip(lab,r.get('values') or [])}
    def clean_exhibition_st(lane):
        x=st.get(lane,{})
        val=num(x.get('st'))
        return val if val is not None and val>=0 and x.get('exhibition_f') is not True else None
    measures={
       # Intentional: first-class 3着能力 uses recent-ish 3連対 rather than first-rate proxy.
       'trio_national':(lambda lane,r:num((r.get('national') or {}).get('trio_rate')), .43, 0.0),
       'trio_local':(lambda lane,r:num((r.get('local') or {}).get('trio_rate')), .25, 0.0),
       'trio_motor':(lambda lane,r:num((r.get('motor') or {}).get('trio_rate')), .18, 0.0),
       'trio_boat':(lambda lane,r:num((r.get('boat') or {}).get('trio_rate')), .08, 0.0),
       'original_lap':(lambda lane,r:num(ol.get(lane,{}).get('一周')), .04, 1.0),
       'original_turn':(lambda lane,r:num(ol.get(lane,{}).get('まわり足')), .07, 1.0),
       'exhibition_time':(lambda lane,r:num(ex.get(lane,{}).get('exhibition_time')), .06, 1.0),
       'exhibition_st':(lambda lane,r:clean_exhibition_st(lane), .06, 1.0),
    }
    second={}
    third={}
    used=[]
    for name,(fn,w,invert) in measures.items():
        d=differences(racers,fn,bool(invert))
        if not d:continue
        used.append(name)
        for lane,sc in d.items():
            third[lane]=third.get(lane,0)+w*sc
            if name in ('trio_national','trio_local','trio_motor','original_turn','exhibition_time','exhibition_st'):
                # Second-place ability involves a greater share of top-two racing ability.
                second[lane]=second.get(lane,0)+w*.5*sc
    # Extra top-two source where >=4 observations. Never infer absent stats.
    duo_defs=[('quinella_national',lambda r:num((r.get('national') or {}).get('quinella_rate')),.28),
              ('quinella_local',lambda r:num((r.get('local') or {}).get('quinella_rate')),.16)]
    for name,fn,w in duo_defs:
        d=differences(racers,lambda lane,r:fn(r))
        if not d:continue
        used.append(name)
        for lane,sc in d.items():second[lane]=second.get(lane,0)+w*sc
    return second,third,used

def valid_input(root,key,now,mod180):
    if not re.fullmatch(r'20\d{6}-\d{2}-\d{2}',key) or key[:8]<START:return None
    if key[:8]!=now.astimezone(JST).strftime('%Y%m%d'):return None
    snap_path=root/'data/site_prediction_snapshots'/f'{key}.json'
    race_path=root/'data/races'/f'{key}.json'
    if not snap_path.exists() or not race_path.exists():return None
    source=snap_path.read_bytes();snap=load_json(snap_path)
    # Explicit first-view freeze and last pre-result snapshot gate.
    if not snap or not mod180.cutoff_ok(snap,key,now):return None
    if snap.get('mode_policy')!=REQUIRED_POLICY:return None
    racebytes=race_path.read_bytes();race=load_json(race_path)
    if not race or race.get('race_key')!=key:return None
    meta=race.get('meta') or {}
    if meta.get('phase')!='PRE_RESULT' or any(meta.get(k) is not False for k in ('results_seen','unlock','scoring')):return None
    if any((race.get('validation') or {}).get(k) not in (False,None) for k in ('result','result_unlock_token')):return None
    d=utc(f'{key[:4]}-{key[4:6]}-{key[6:8]}T{snap.get("deadline")}:00+09:00')
    if not d or now>=d:return None
    scratch=load_json(root/'data/site_scratches_v182'/f'{key}.json')
    # Missing explicit scratch scan cannot prove six-boat validity.
    if not scratch or scratch.get('race_key')!=key or scratch.get('blocked') is not False:return None
    if scratch.get('source_date')!=key[:8]:return None
    t=utc(scratch.get('checked_at'))
    if not t or t>now or now-t>timedelta(minutes=16):return None
    if len(race.get('racers') or [])!=6:return None
    return snap,source,race,racebytes,scratch

def build(snap,source,race,racebytes,scratch,mod180):
    key=snap['race_key']
    raw=mod180.candidate_rows(snap)
    second,third,used=role_strength(race)
    if not used:return None
    # Preserve V180 head mass and alter only P(second,third | head).
    byhead={str(h):[] for h in range(1,7)}
    for r in raw:byhead[r['combo'][0]].append(r)
    scores={}
    for head,entries in byhead.items():
        mass=sum(r['score'] for r in entries)
        weighted={}
        for row in entries:
            h,s,t=(int(q) for q in row['combo'].split('-'))
            z=.65*second.get(s,0)+1.05*third.get(t,0)
            weighted[row['combo']]=row['score']*math.exp(max(-1.2,min(1.2,z)))
        den=sum(weighted.values())
        for row in entries:
            k=row['combo'];shifted=mass*weighted[k]/den
            scores[k]=.70*row['score']+.30*shifted
    rankings=[{'combo':k,'score':v} for k,v in scores.items()]
    rankings.sort(key=lambda r:(-r['score'],r['combo']))
    assert len(rankings)==120 and len({x['combo'] for x in rankings})==120
    assert abs(sum(x['score'] for x in rankings)-1)<1e-9
    v180=[r['combo'] for r in raw]
    v185=[r['combo'] for r in rankings]
    return {
        'schema_version':'boat-edge-v185-prospective-tail-role-shadow-v1',
        'scope':'SITE_REFERENCE_UNTOUCHED_FUTURE_RESEARCH_ONLY_NOT_FORMAL_FRESH',
        'race_key':key,'candidate_id':IDENT,'source_saved_at':snap['saved_at'],
        'source_first_saved_at':snap['first_saved_at'],
        'source_snapshot_sha256':SHA(source),'source_race_sha256':SHA(racebytes),
        'source_scratch_sha256':SHA(canonical({k:v for k,v in scratch.items() if k!='checked_at'})),
        'source_deadline':snap['deadline'],'source_policy':REQUIRED_POLICY,
        'predeclared_model':{'original_v180_weight':.70,'tail_role_weight':.30,'2nd_strength_coef':.65,'3rd_strength_coef':1.05,
            'metric_ranking':'within_race_rank_ge4_observed_no_imputation'},
        'source_features_used':used,
        'baseline_top3':snap['modes']['hit']['tickets'][:3] and [x['combo'] for x in snap['modes']['hit']['tickets'][:3]],
        'baseline_top5':[x['combo'] for x in snap['modes']['hit']['tickets'][:5]],
        'baseline_top10':[x['combo'] for x in snap['modes']['hit']['tickets']],
        'v180_top3':v180[:3],'v180_top5':v180[:5],'v180_top10':v180[:10],
        'candidate_top3':v185[:3],'candidate_top5':v185[:5],'candidate_top10':v185[:10],
        'candidate_top15':v185[:15],'candidate_top20':v185[:20],
        'candidate_ranked_120':rankings,
        'guards':{'results_seen':False,'unlock':False,'scoring':False},
        'approval':'RESEARCH_ONLY_NOT_PRODUCTION',
        'no_result_read':True,'no_odds_for_ranking':True
    }

def run(root,now,mod180):
    root=Path(root);folder=root/'data/site_tail_shadow_v185/predictions'
    accepted=existing=skipped=0
    for path in sorted((root/'data/site_prediction_snapshots').glob('20??????-??-??.json')):
        key=path.stem
        if key[:8]!=now.astimezone(JST).strftime('%Y%m%d') or key[:8]<START:continue
        out=folder/f'{key}.json'
        if out.exists():existing+=1;continue  # immutable, never rewrite
        args=valid_input(root,key,now,mod180)
        if not args:skipped+=1;continue
        result=build(*args,mod180)
        if not result:skipped+=1;continue
        assert canonical(result)==canonical(build(*args,mod180)), 'REPRODUCIBILITY_FAIL'
        folder.mkdir(parents=True,exist_ok=True)
        with out.open('xb') as f:f.write(canonical(result))
        accepted+=1
    return {'new_shadow':accepted,'already_immutable':existing,'not_yet_eligible':skipped,
       'production_weights_changed':False,'results_opened':False,'formal_fresh_touched':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',default='.');args=p.parse_args()
    sys.path.insert(0,str(Path(args.repo)/'scripts'))
    import site_v180_shadow as v180
    print('V185_FUTURE_ONLY '+json.dumps(run(args.repo,datetime.now(timezone.utc),v180),sort_keys=True))
