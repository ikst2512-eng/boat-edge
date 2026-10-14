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
POLICY_V1='PREDECLARED_HEAD_TAIL_COVERAGE_NO_ODDS_MULTIPLIER_BOOST'
POLICY_V2='PREDECLARED_HEAD_SECOND_COVERAGE_FROM_EXISTING_FROZEN_MODES_NO_NEW_ODDS_MULTIPLIER'
POLICY_V3='PREDECLARED_DISTINCT_HEAD_SECOND_TICKET_MEMBERSHIP_EXISTING_FROZEN_MODES'
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
    if ('RESULT_UNLOCK_TOKEN' not in g or
            any(g.get(k) is not False for k in ('results_seen','unlock','scoring'))
            or g['RESULT_UNLOCK_TOKEN'] is not None):
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


def head_second_coverage10(hit,hole):
    """One predeclared TopK head/second alternative from existing frozen modes.

    This changes ticket membership and Top3/Top5 positions, unlike the old
    seven-fixed-plus-three-tail experiment. Hole-mode input may itself be
    odds-aware; this algorithm does NOT add any new multiplier or train on
    outcomes. Research-only; promotion remains forbidden.
    """
    if len(hit)!=10 or not hole:return None
    out=[]
    def add(combo):
        if combo not in out and len(out)<10:out.append(combo)
    add(hit[0]);add(hit[1])
    lead_head=hit[0].split('-')[0]
    # Head omission is a measurable failure mode; use only an already
    # predeadline frozen alternative rather than a guessed head probability.
    alt=next((x for x in hole if x.split('-')[0]!=lead_head and x not in out),None)
    if alt:add(alt)
    add(hit[2])
    # Earliest predeclared different head+second prefix, before rank 5.
    used={(t.split('-')[0],t.split('-')[1]) for t in out}
    alt2=next((x for x in hole if (x.split('-')[0],x.split('-')[1]) not in used
               and x not in out),None)
    if alt2:add(alt2)
    for x in hit:add(x)
    for x in hole:add(x)
    return out if len(out)==10 else None


def head_second_distinct_coverage10(hit,balance,hole):
    """Result-unseen TopK hypothesis with a verifiably different ten-ticket set.

    No learned weights or same-day outcomes: only first-Git-frozen candidate
    ranks. Prefer a different head from the balance list, then hole; reject
    races with no observed distinct candidate rather than fabricate a tail.
    Existing V1/V2 frozen-policy functions remain byte-for-byte unchanged.
    """
    if len(hit)!=10 or len(balance)!=10 or len(hole)<10:return None
    lead=hit[0].split('-')[0]
    alternatives=list(dict.fromkeys(balance+hole))
    first=next((x for x in alternatives if x not in hit and x[0]!=lead),None)
    if first is None:return None
    out=[]
    def add(v):
        if v not in out and len(out)<10:out.append(v)
    add(hit[0]);add(hit[1]);add(first);add(hit[2])
    seen_pairs={tuple(c.split('-')[:2]) for c in out}
    second=next((x for x in alternatives if x not in hit and x not in out
                 and tuple(x.split('-')[:2]) not in seen_pairs),None)
    if second is not None:add(second)
    for x in hit:add(x)
    for x in alternatives:add(x)
    return out if (len(out)==10 and set(out)!=set(hit)
                   and out[:3]!=hit[:3] and out[:5]!=hit[:5]) else None


def prepare(root,path,now,policy='legacy'):
    """Build fixed, same-budget comparators only from immutable mode tickets."""
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
    comparators={'hit10':hit,'balance10':balance,'scenario7plus3':challenger,
          'coverage15':expanded}
    comparison_policy=POLICY_V1
    if policy=='headsecond':
        proposed=head_second_coverage10(hit,hole)
        if proposed is None:return None,'head_second_not_ten'
        comparators['headsecond10']=proposed
        comparison_policy=POLICY_V2
    elif policy=='headsecond_distinct':
        proposed=head_second_distinct_coverage10(hit,balance,hole)
        if proposed is None:return None,'distinct_outside_current_top10_not_observed'
        comparators['headsecond10']=proposed
        comparison_policy=POLICY_V3
    elif policy!='legacy':
        return None,'unsupported_research_policy'
    return {'schema':SCHEMA,'scope':'PROSPECTIVE_SITE_SHADOW_NOT_FORMAL_FRESH',
      'race_key':key,'deadline_jst':cohort['deadline_jst'],
      'snapshot_saved_at':cohort['snapshot_saved_at'],'frozen_at':now.isoformat(),
      'v232_cohort_sha256':sha(path),'v232_first_git_commit':original['commit'],
      'v232_first_git_committed_at':original['at'].isoformat(),
      'comparators':comparators,
      'comparison_policy':comparison_policy,
      'actual_or_paper_purchase':False,'production_model_changed':False,
      'result_seen_at_freeze':False,'proven_improvement':False},None


def freeze(root,now):
    formal_closed(root)
    day=now.astimezone(JST).strftime('%Y%m%d')
    dest=root/PATH/'v236_frozen';excluded={};n=0;seen=0
    for p in sorted((root/PATH/'v232_cohort').glob(day+'-??-??.json')):
        out=dest/p.name
        if out.exists():continue
        seen+=1;obj,reason=prepare(root,p,now,policy='headsecond_distinct')
        if obj:
            save_once(out,obj);n+=1
        else:excluded[reason]=excluded.get(reason,0)+1
    all_paths=list(dest.glob(day+'-??-??.json')) if dest.exists() else []
    s={'schema':'BOAT_EDGE_V236_HITRATE_PRE_RESULT_SUMMARY_V1','day_jst':day,
       'frozen_today':len(all_paths),'new_frozen_this_run':n,'rejected_current_window':excluded,
       'comparators':['hit10','balance10','scenario7plus3','coverage15','headsecond10'],
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
    # Git commit timestamps have only whole-second precision. A PRE_RESULT
    # freeze captured within that same second can appear up to 999ms later.
    # Keep both instants strictly before the race deadline, and reject any
    # inversion greater than one second. The Git first-add SHA check above
    # remains mandatory; this is not permission to backfill a candidate.
    if (not frozen_at or frozen_at>=deadline or
            frozen_at>frozen_commit['at']+dt.timedelta(seconds=1)):
        return None,'candidate_freeze_time_invalid'
    policy=row.get('comparison_policy')
    if policy not in (POLICY_V1,POLICY_V2,POLICY_V3):return None,'unknown_prospective_research_policy'
    strategy=('headsecond' if policy==POLICY_V2 else
              'headsecond_distinct' if policy==POLICY_V3 else 'legacy')
    expected,reason=prepare(root,cohort_path,frozen_at,policy=strategy)
    if reason or any(row.get(k)!=v for k,v in expected.items()):
        return None,'candidate_not_matching_predeclared_source'
    lists=row.get('comparators') or {}
    names={'hit10','balance10','scenario7plus3','coverage15'}
    if policy in (POLICY_V2,POLICY_V3):names.add('headsecond10')
    if not isinstance(lists,dict) or set(lists)!=names:return None,'candidate_schema_modified'
    if any(not isinstance(v,list) or len(v)<10 or len(v)>15 or any(not combo_ok(x) for x in v) or len(set(v))!=len(v) for v in lists.values()):
        return None,'candidate_ticket_invalid'
    result=load(root/'data/site_results'/path.name)
    if not confirmed_result(result,key,deadline,now):return None,'site_official_result_unconfirmed'
    winning=result['trifecta'];hits={name:winning in tickets for name,tickets in lists.items()}
    record={'schema':SCORE_SCHEMA,'scope':'POST_RESULT_SITE_ONLY_NOT_FORMAL_FRESH',
      'race_key':key,'official_result':winning,'official_result_source':result['source'],
      'result_sha256':sha(root/'data/site_results'/path.name),
      'frozen_candidate_sha256':sha(path),
      'candidate_first_git_commit':frozen_commit['commit'],
      'candidate_first_git_committed_at':frozen_commit['at'].isoformat(),
      'outcomes':hits,'ticket_counts':{x:len(v) for x,v in lists.items()},
      'production_accuracy_improvement_proven':False,
      'real_or_paper_purchase':False,'model_promotion_authorized':False}
    if policy in (POLICY_V2,POLICY_V3):
        record['candidate_policy']=policy
        # The first 3/5/10 predictions were ranked and frozen BEFORE results.
        # Scoring those frozen prefixes uses no fitted/post-result re-ranking.
        record['prefix_outcomes']={
            mode:{str(k):winning in lists[mode][:k] for k in (3,5,10)}
            for mode in ('hit10','headsecond10')}
    return record,None


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
    # Distinct policies must NEVER be pooled as if they were one candidate.
    # Old scored V2 rows may lack candidate_policy; their stored frozen policy
    # is V2 and is preserved by treating this legacy tag as V2 only.
    def paired_summary(rows):
        gains=sum(x['outcomes']['headsecond10'] and not x['outcomes']['hit10'] for x in rows)
        losses=sum(not x['outcomes']['headsecond10'] and x['outcomes']['hit10'] for x in rows)
        discord=gains+losses
        paired_p=(min(1.,2*sum(math.comb(discord,j) for j in range(min(gains,losses)+1))/(2**discord))
                  if discord else None)
        topk={}
        for k in (3,5,10):
            value=str(k)
            pairs=[(x['prefix_outcomes']['hit10'][value],
                    x['prefix_outcomes']['headsecond10'][value]) for x in rows]
            plus=sum(c and not b for b,c in pairs)
            minus=sum(b and not c for b,c in pairs)
            n=plus+minus
            p=(min(1.,2*sum(math.comb(n,j) for j in range(min(plus,minus)+1))/(2**n))
               if n else None)
            topk[value]={'races':len(pairs),'current_hits':sum(b for b,c in pairs),
                'candidate_hits':sum(c for b,c in pairs),'gains':plus,'losses':minus,
                'paired_exact_p_two_sided':p}
        return {'races':len(rows),'current_hit10_hits':sum(x['outcomes']['hit10'] for x in rows),
                'candidate_hit10_hits':sum(x['outcomes']['headsecond10'] for x in rows),
                'gains':gains,'losses':losses,'paired_exact_p_two_sided':paired_p,
                'ranked_top3_top5_top10':topk,'promotion_authorized':False}
    v2=[x for x in settled if 'headsecond10' in x.get('outcomes',{})
        and x.get('candidate_policy',POLICY_V2)==POLICY_V2]
    v3=[x for x in settled if x.get('candidate_policy')==POLICY_V3
        and 'headsecond10' in x.get('outcomes',{})]
    v2_summary=paired_summary(v2)
    v3_summary=paired_summary(v3)
    s={'schema':'BOAT_EDGE_V236_HITRATE_SCORE_SUMMARY_V1',
       'scope':'POST_RESULT_SAME_COHORT_COMPARISON_NOT_FORMAL_FRESH',
       'scored_total':len(settled),'new_scored_this_run':count,
       'comparisons':{m:{'hit':sum(x['outcomes'][m] for x in settled),'races':len(settled),
          'hit_rate_percent':round(sum(x['outcomes'][m] for x in settled)/len(settled)*100,2) if settled else None,
          'avg_points':round(sum(x['ticket_counts'][m] for x in settled)/len(settled),2) if settled else None} for m in fields},
       'headsecond10_matched_prospective_only':v2_summary,
       'headsecond10_distinct_matched_prospective_only':v3_summary,
       'rejected_or_pending_this_run':excluded,'production_model_changed':False,
       'promotion_authorized':False,'real_or_paper_purchase':False,
       'status':'DESCRIPTIVE_FORWARD_SHADOW_NO_TUNING_NO_PROMOTION',
       'examples':[{'race_key':x['race_key'],'winning':x['official_result'],'outcomes':x['outcomes']} for x in settled[-25:]]}
    changed=save_changed(root/PATH/'v236_score_current.json',s,['scored_total','comparisons','headsecond10_matched_prospective_only','headsecond10_distinct_matched_prospective_only','rejected_or_pending_this_run'])
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
