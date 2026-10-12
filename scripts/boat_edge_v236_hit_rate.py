#!/usr/bin/env python3
"""V236 site-only, hit-rate-first forward shadow A/B. Formal Fresh never scored.

Freeze phase reads ONLY prospectively committed V232 cohorts and formal guards;
score phase reads ONLY previously published V236 frozen rows and confirmed SITE results.
No production model changes; no bankroll changes; no payout/odds targeting.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse,parse_qs

UTC=dt.timezone.utc
JST=dt.timezone(dt.timedelta(hours=9))
KEY=re.compile(r'^20\d{6}-\d{2}-\d{2}$')
COMBO=re.compile(r'^[1-6]-[1-6]-[1-6]$')
SCHEMA='BOAT_EDGE_V236_HITRATE_FORWARD_SHADOW_V1'
SCORE_SCHEMA='BOAT_EDGE_V236_HITRATE_SCORE_V1'
PATH='data/site_autopilot'


def load(p):
    try:
        o=json.loads(p.read_text(encoding='utf-8'))
        return o if isinstance(o,dict) else None
    except (OSError,UnicodeError,ValueError):return None


def save_once(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:
        f.write(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n')


def save_changed(path,obj,comparable_keys):
    old=load(path) or {}
    if path.is_file() and all(old.get(k)==obj.get(k) for k in comparable_keys):return False
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    return True


def parse(s):
    try:
        x=dt.datetime.fromisoformat(str(s).replace('Z','+00:00'))
        return x.astimezone(UTC) if x.tzinfo else None
    except (TypeError,ValueError,OverflowError):return None


def sha(p):
    try:return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:return None


def due(key,s):
    if not KEY.fullmatch(str(key)):return None
    date,venue,race=key.split('-')
    value=parse(s)
    if not value or not 1<=int(venue)<=24 or not 1<=int(race)<=12:return None
    return value if value.astimezone(JST).strftime('%Y%m%d')==date else None


def combo_ok(s):return isinstance(s,str) and COMBO.fullmatch(s) is not None and len(set(s.split('-')))==3


def git_first(root,path):
    """Initial added commit & exact bytes. Not a claim about source outside GitHub."""
    rel=path.relative_to(root).as_posix()
    try:
        hashes=subprocess.check_output(['git','log','--diff-filter=A','--reverse','--format=%H','--',rel],cwd=root,text=True,stderr=subprocess.DEVNULL).splitlines()
        if not hashes:return None
        h=hashes[0]
        time=subprocess.check_output(['git','show','-s','--format=%cI',h],cwd=root,text=True,stderr=subprocess.DEVNULL).strip()
        original=subprocess.check_output(['git','show',f'{h}:{rel}'],cwd=root,stderr=subprocess.DEVNULL)
        return {'commit':h,'at':parse(time),'sha256':hashlib.sha256(original).hexdigest()}
    except (OSError,subprocess.CalledProcessError,ValueError):return None


def formal_closed(root):
    status=load(root/'data/formal_status.json') or {}
    g=status.get('guards') or {}
    if any(g.get(k) is not False for k in ('results_seen','unlock','scoring')) or g.get('RESULT_UNLOCK_TOKEN') is not None:
        raise RuntimeError('V236_FORMAL_GATE_MUST_BE_CLOSED')
    races=(status.get('formalFirst100') or {}).get('races')
    if type(races) is not int or races!=0:
        raise RuntimeError('V236_FORMAL_COHORT_NOT_CONFIRMED_EMPTY')


def unique_extend(seed,extra,count):
    out=list(seed)
    for combo in extra:
        if combo not in out:out.append(combo)
        if len(out)>=count:break
    return out[:count]


def prepare(root,path,now):
    """Build fixed, same-budget coverage alternatives only from frozen ticket identities."""
    formal_closed(root)
    cohort=load(path) or {}
    key=path.stem
    deadline=due(key,cohort.get('deadline_jst'))
    if not deadline or (deadline-now).total_seconds()<90 or (deadline-now).total_seconds()>900:
        return None,'outside_forward_window'
    at=parse(cohort.get('evidence_committed_at'))
    saved=parse(cohort.get('snapshot_saved_at'))
    if not at or not saved or saved>at or at>now or at>=deadline:return None,'cohort_timestamp_unproven'
    original=git_first(root,path)
    if not original or not original['at'] or not (saved<=original['at']<=now<deadline) or original['sha256']!=sha(path):
        return None,'original_cohort_not_committed_unchanged_before_deadline'
    if (cohort.get('schema')!='BOAT_EDGE_V232_SITE_PROSPECTIVE_ACCURACY_COHORT_V1'
            or cohort.get('scope')!='SITE_REFERENCE_UNSEEN_PRE_RESULT_ONLY_NOT_FORMAL_FRESH'
            or cohort.get('race_key')!=key or cohort.get('model_id')!='SITE_REFERENCE_V122'
            or cohort.get('formal_results_seen') is not False or cohort.get('formal_gate_unlocked') is not False
            or cohort.get('paper_purchases_authorized') is not False or cohort.get('real_purchases_authorized') is not False):
        return None,'cohort_guard_or_schema_invalid'
    frozen=cohort.get('frozen_mode_tickets') or {}
    if not isinstance(frozen,dict):return None,'mode_missing'
    hit=[r.get('combo') for r in frozen.get('hit',[]) if isinstance(r,dict)]
    balance=[r.get('combo') for r in frozen.get('balance',[]) if isinstance(r,dict)]
    hole=[r.get('combo') for r in frozen.get('hole',[]) if isinstance(r,dict)]
    if (len(hit)!=10 or len(balance)!=10 or len(hole)<10 or any(not combo_ok(c) for c in hit+balance+hole)
            or len(set(hit))!=10 or len(set(balance))!=10 or len(set(hole))!=len(hole)):
        return None,'ticket_sources_incomplete'
    if hit!=cohort.get('top10'):return None,'frozen_hit_top10_changed'
    # PRE-DECLARED comparators. Never optimize based on same-day results.
    challenger=unique_extend(hit[:7],hole,10)
    expanded=unique_extend(hit,hole,15)
    if len(challenger)!=10:return None,'challenger_not_ten'
    return {'schema':SCHEMA,'scope':'PROSPECTIVE_SITE_SHADOW_NOT_FORMAL_FRESH',
      'race_key':key,'deadline_jst':cohort['deadline_jst'],
      'snapshot_saved_at':cohort['snapshot_saved_at'],'frozen_at':now.isoformat(),
      'v232_cohort_sha256':sha(path),'v232_first_git_commit':original['commit'],
      'v232_first_git_committed_at':original['at'].isoformat(),
      'comparators':{'hit10':hit,'balance10':balance,'scenario7plus3':challenger,
          'coverage15':expanded},
      'comparison_policy':'PREDECLARED_HEAD_TAIL_COVERAGE_NO_ODDS_MULTIPLIER_BOOST',
      'actual_or_paper_purchase':False,'production_model_changed':False,
      'result_seen_at_freeze':False,'proven_improvement':False},None


def freeze(root,now):
    formal_closed(root)
    day=now.astimezone(JST).strftime('%Y%m%d')
    dest=root/PATH/'v236_frozen';excluded={};n=0;seen=0
    for p in sorted((root/PATH/'v232_cohort').glob(day+'-??-??.json')):
        out=dest/p.name
        if out.exists():continue
        seen+=1;obj,reason=prepare(root,p,now)
        if obj:
            save_once(out,obj);n+=1
        else:excluded[reason]=excluded.get(reason,0)+1
    all_paths=list(dest.glob(day+'-??-??.json')) if dest.exists() else []
    s={'schema':'BOAT_EDGE_V236_HITRATE_PRE_RESULT_SUMMARY_V1','day_jst':day,
       'frozen_today':len(all_paths),'new_frozen_this_run':n,'rejected_current_window':excluded,
       'comparators':['hit10','balance10','scenario7plus3','coverage15'],
       'target':'TOP10_HIT_RATE_NOT_10_TO_20X_PRICE_BAND',
       'production_model_changed':False,'real_or_paper_purchases':0,'accuracy_improvement_proven':False}
    saved=save_changed(root/PATH/'v236_pre_current.json',s,['day_jst','frozen_today','rejected_current_window'])
    print('V236_PRE_RESULT_FROZEN_NO_RESULT_READ',json.dumps({'new':n,'frozen_today':len(all_paths),'checked':seen,'excluded':excluded,'state_written':saved},sort_keys=True))
    return s


def confirmed_result(result,key,deadline,now=None):
    if not result or result.get('race_key')!=key or result.get('status')!='confirmed':return False
    if result.get('schema_version')!='boat-edge-site-result-v109':return False
    resulttime=parse(result.get('fetched_at'))
    if not resulttime or resulttime<=deadline:return False
    if now is not None and resulttime>now:return False
    combo=result.get('trifecta')
    if not combo_ok(combo):return False
    finish=result.get('finish_order')
    if not isinstance(finish,list) or len(finish)<3 or any(type(x) is not int for x in finish[:3]):return False
    if '-'.join(map(str,finish[:3]))!=combo:return False
    money=result.get('trifecta_payout_yen_per_100')
    if type(money) not in (int,float) or not math.isfinite(money) or not 100<=money<=100000000:return False
    source=result.get('source')
    if not isinstance(source,str):return False
    url=urlparse(source)
    if url.scheme!='https' or url.netloc!='www.boatrace.jp' or url.path!='/owpc/pc/race/raceresult':return False
    fields=parse_qs(url.query,keep_blank_values=True)
    date,venue,race=key.split('-')
    if fields!={'hd':[date],'jcd':[venue],'rno':[str(int(race))]} or url.fragment:return False
    return True


def score_row(root,path,now):
    formal_closed(root)
    row=load(path) or {};key=path.stem
    deadline=due(key,row.get('deadline_jst'))
    if not deadline or now<=deadline+dt.timedelta(minutes=1):return None,'race_not_over'
    frozen_commit=git_first(root,path)
    if not frozen_commit or frozen_commit['sha256']!=sha(path) or not frozen_commit['at'] or not frozen_commit['at']<deadline<=now:
        return None,'shadow_not_git_frozen_before_deadline'
    cohort_path=root/PATH/'v232_cohort'/path.name
    if sha(cohort_path)!=row.get('v232_cohort_sha256'):return None,'cohort_sha_mutated'
    original=git_first(root,cohort_path)
    if (not original or original['commit']!=row.get('v232_first_git_commit')
            or not original['at'] or original['at']>=deadline or original['sha256']!=sha(cohort_path)):
        return None,'source_git_provenance_invalid'
    # Reproduce only the already-frozen PRE_RESULT ticket definitions. Validate
    # scope, times and equal-point comparators BEFORE opening any outcome file.
    frozen_at=parse(row.get('frozen_at'))
    if not frozen_at or frozen_at>frozen_commit['at']:return None,'candidate_freeze_time_invalid'
    expected,reason=prepare(root,cohort_path,frozen_at)
    if reason or any(row.get(k)!=v for k,v in expected.items()):
        return None,'candidate_not_matching_predeclared_source'
    lists=row.get('comparators') or {}
    if set(lists)!=set(['hit10','balance10','scenario7plus3','coverage15']):return None,'candidate_schema_modified'
    if any(not isinstance(v,list) or len(v)<10 or len(v)>15 or any(not combo_ok(x) for x in v) or len(set(v))!=len(v) for v in lists.values()):
        return None,'candidate_ticket_invalid'
    result=load(root/'data/site_results'/path.name)
    if not confirmed_result(result,key,deadline,now):return None,'site_official_result_unconfirmed'
    winning=result['trifecta'];hits={name:winning in tickets for name,tickets in lists.items()}
    return {'schema':SCORE_SCHEMA,'scope':'POST_RESULT_SITE_ONLY_NOT_FORMAL_FRESH',
      'race_key':key,'official_result':winning,'official_result_source':result['source'],
      'result_sha256':sha(root/'data/site_results'/path.name),
      'frozen_candidate_sha256':sha(path),
      'candidate_first_git_commit':frozen_commit['commit'],
      'candidate_first_git_committed_at':frozen_commit['at'].isoformat(),
      'outcomes':hits,'ticket_counts':{x:len(v) for x,v in lists.items()},
      'production_accuracy_improvement_proven':False,
      'real_or_paper_purchase':False,'model_promotion_authorized':False},None


def score(root,now):
    formal_closed(root)
    folder=root/PATH/'v236_frozen';dest=root/PATH/'v236_scored'
    excluded={};count=0
    for p in sorted(folder.glob('20??????-??-??.json')) if folder.exists() else []:
        if (dest/p.name).exists():continue
        obj,reason=score_row(root,p,now)
        if obj:
            save_once(dest/p.name,obj);count+=1
        else:excluded[reason]=excluded.get(reason,0)+1
    settled=[load(p) for p in sorted(dest.glob('20??????-??-??.json'))] if dest.exists() else []
    settled=[x for x in settled if x and x.get('schema')==SCORE_SCHEMA]
    fields=['hit10','balance10','scenario7plus3','coverage15']
    s={'schema':'BOAT_EDGE_V236_HITRATE_SCORE_SUMMARY_V1',
       'scope':'POST_RESULT_SAME_COHORT_COMPARISON_NOT_FORMAL_FRESH',
       'scored_total':len(settled),'new_scored_this_run':count,
       'comparisons':{m:{'hit':sum(x['outcomes'][m] for x in settled),'races':len(settled),
          'hit_rate_percent':round(sum(x['outcomes'][m] for x in settled)/len(settled)*100,2) if settled else None,
          'avg_points':round(sum(x['ticket_counts'][m] for x in settled)/len(settled),2) if settled else None} for m in fields},
       'rejected_or_pending_this_run':excluded,'production_model_changed':False,
       'promotion_authorized':False,'real_or_paper_purchase':False,
       'status':'DESCRIPTIVE_FORWARD_SHADOW_NO_TUNING_NO_PROMOTION',
       'examples':[{'race_key':x['race_key'],'winning':x['official_result'],'outcomes':x['outcomes']} for x in settled[-25:]]}
    changed=save_changed(root/PATH/'v236_score_current.json',s,['scored_total','comparisons','rejected_or_pending_this_run'])
    print('V236_SITE_RESULT_PAIRED_HITRATE',json.dumps({'new':count,'total':len(settled),'comparisons':s['comparisons'],'pending':excluded,'state_written':changed},ensure_ascii=False,sort_keys=True))
    return s


def main():
    p=argparse.ArgumentParser()
    p.add_argument('phase',choices=['freeze','score'])
    p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--now')
    args=p.parse_args();now=parse(args.now) if args.now else dt.datetime.now(UTC)
    if now is None:raise SystemExit('V236_INVALID_CLOCK')
    if args.phase=='freeze':freeze(args.root.resolve(),now)
    else:score(args.root.resolve(),now)


if __name__=='__main__':main()
