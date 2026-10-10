#!/usr/bin/env python3
"""V213 PRE-RESULT shadow-only qualification and POST-RESULT retrospective grading.
No actual/paper purchase is registered; independent from formal Fresh and V211 bankroll.
The 'freeze' phase NEVER reads result paths. 'settle' ONLY opens results for prior frozen entries.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import pathlib
import re

UTC=dt.timezone.utc
JST=dt.timezone(dt.timedelta(hours=9))
KEY=re.compile(r'^20\d{6}-\d\d-\d\d$')
COMBO=re.compile(r'^[1-6]-[1-6]-[1-6]$')
SCHEMA='BOAT_EDGE_V213_PROSPECTIVE_SHADOW_V1'

def load(path):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except (OSError,ValueError):return None

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')

def parse(s):
    try:
        a=dt.datetime.fromisoformat(str(s).replace('Z','+00:00'))
        return a.astimezone(UTC) if a.tzinfo else None
    except (TypeError,ValueError,OverflowError):return None

def due_for(key,clock):
    if not KEY.fullmatch(str(key)) or not re.fullmatch(r'\d\d:\d\d',str(clock)):return None
    try:return dt.datetime.strptime(key[:8]+clock,'%Y%m%d%H:%M').replace(tzinfo=JST).astimezone(UTC)
    except ValueError:return None

def hashraw(path):
    try:return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:return None

def check(root,path,now):
    key=path.stem
    if not KEY.fullmatch(key):return None,'race_key_invalid'
    s=load(path)
    if not isinstance(s,dict) or s.get('race_key')!=key:return None,'snapshot_invalid'
    if s.get('snapshot_window')!='FINAL_15M' or s.get('prediction_kind')!='SITE_REFERENCE_V122':return None,'snapshot_not_eligible'
    if any(s.get('guards',{}).get(k) is not False for k in ('results_seen','unlock','scoring')):return None,'pre_result_guard_failed'
    saved=parse(s.get('saved_at')); due=due_for(key,s.get('deadline'))
    if not saved or not due or saved>now or saved>=due:return None,'snapshot_time_invalid'
    until=(due-now).total_seconds()/60
    if not 2<=until<=15:return None,'outside_decision_window'
    if not 0<=(due-saved).total_seconds()/60<=16:return None,'not_final15'
    if not 0<=(now-saved).total_seconds()<=600:return None,'snapshot_stale'
    audit=load(root/'data/site_prediction_audit'/path.name) or {}
    digest=hashraw(path)
    if audit.get('pass') is not True or audit.get('latest_snapshot_sha256')!=digest:return None,'snapshot_audit_sha_failed'
    scratch=load(root/'data/site_scratches_v182'/path.name) or {}
    checktime=parse(scratch.get('checked_at'))
    if scratch.get('race_key')!=key or scratch.get('blocked') is not False:return None,'scratch_unknown_or_blocked'
    if scratch.get('race_card_source_status')!='ok' or not checktime or not 0<=(now-checktime).total_seconds()<=900:return None,'scratch_source_stale'
    # An odds hash WITHOUT its matching source file is not verified source-time odds.
    odds_path=root/'data/site_odds'/path.name
    o=load(odds_path) or {}
    oddtime=parse(o.get('fetched_at'))
    if not s.get('odds_sha256') or hashraw(odds_path)!=s.get('odds_sha256'):
        return None,'odds_sha_mismatch_or_missing'
    if o.get('race_key')!=key or o.get('phase')!='PRE_RESULT_PURCHASE_ONLY' or not oddtime or oddtime>saved:
        return None,'odds_time_or_source_invalid'
    if (saved-oddtime).total_seconds()>900:return None,'odds_source_stale'
    all_odds=o.get('trifecta_odds') or {}
    rows=(s.get('modes',{}).get('hit',{}) or {}).get('tickets') or []
    matched=[];seen=set()
    for item in rows:
        if not isinstance(item,dict):continue
        combo=item.get('combo');prob=item.get('p');odd=item.get('odds')
        if not isinstance(combo,str) or not COMBO.fullmatch(combo) or len(set(combo.split('-')))!=3 or combo in seen:continue
        seen.add(combo)
        if not isinstance(prob,(float,int)) or not isinstance(odd,(float,int)) or not math.isfinite(prob) or not math.isfinite(odd):continue
        if not 0<prob<100 or not 8<=odd<=25:continue
        original=all_odds.get(combo)
        if not isinstance(original,(float,int)) or abs(float(original)-float(odd))>0.05:continue
        # Raw probabilities are NOT calibrated. EV is a diagnostic ranking only, never a purchase signal.
        preliminary_ev=prob*odd/100
        if preliminary_ev>=1.15:matched.append({'combo':combo,'p_raw_percent':round(prob,4),'pre_result_odds':round(float(odd),2),'raw_ev_uncalibrated':round(preliminary_ev,4)})
    if not matched:return None,'no_raw_ev_candidate_8_25x'
    matched=sorted(matched,key=lambda x:(-x['raw_ev_uncalibrated'],x['combo']))[:3]
    return {'race_key':key,'deadline':s['deadline'],'deadline_at':due.isoformat(),
            'venue':s.get('venue','未取得'),'race_no':s.get('race_no'),
            'model_id':s['prediction_kind'],'snapshot_at':saved.isoformat(),
            'snapshot_sha256':digest,'odds_sha256':s['odds_sha256'],
            'scratch_checked_at':checktime.isoformat(),
            'freeze_at':now.isoformat(),'status':'shadow_pending',
            'no_real_or_paper_purchase':True,'tickets':matched,'shadow_cost_yen':100*len(matched)},None

def report(entries,scan=None):
    settled=[e for e in entries if e['status']=='shadow_settled']
    pending=sum(e['status']=='shadow_pending' for e in entries)
    cost=sum(e['shadow_cost_yen'] for e in settled)
    returns=sum(e.get('shadow_return_yen',0) for e in settled)
    hits=sum(e.get('shadow_return_yen',0)>0 for e in settled)
    return {'schema':SCHEMA,'scope':'PROSPECTIVE_ONLY_NOT_PAPER_PURCHASE_NOT_FORMAL_FRESH',
      'cash_stake_yen':0,'paper_bankroll_effect_yen':0,'paper_budget_per_day_yen':50000,
      'settled_races':len(settled),'pending_races':pending,'frozen_races':len(entries),
      'flat100_hypothetical_stake_yen':cost,'flat100_hypothetical_return_yen':returns,
      'flat100_observed_roi_percent':round(100*returns/cost,2) if cost else None,
      'shadow_hit_races':hits,'statistical_gate':'NOT_APPROVED_MIN_100_SETTLED_PROSPECTIVE',
      'performance_is_not_live_paper_roi':True,
      'last_scan':scan or {},'recent':list(reversed(entries[-40:]))}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('phase',choices=['freeze','settle','report'])
    ap.add_argument('--root',default='.')
    ap.add_argument('--now')
    a=ap.parse_args();root=pathlib.Path(a.root).resolve()
    now=parse(a.now) if a.now else dt.datetime.now(UTC)
    if not now:raise SystemExit('INVALID_TIME')
    base=root/'data/site_paper_sim'
    ledger=base/'shadow_v213_ledger.json'
    current=base/'shadow_v213_current.json'
    old=load(ledger) or {'schema':SCHEMA,'entries':[]}
    if old.get('schema')!=SCHEMA or not isinstance(old.get('entries'),list):raise SystemExit('SHADOW_LEDGER_INVALID')
    entries=old['entries']
    keys=[e.get('race_key') for e in entries]
    if len(keys)!=len(set(keys)):raise SystemExit('SHADOW_DUPLICATE_RACE')
    if a.phase=='freeze':
        today=now.astimezone(JST).strftime('%Y%m%d')
        skips={};reviewed=0;frozen=0
        for path in sorted((root/'data/site_prediction_snapshots').glob(today+'-??-??.json')):
            if path.stem in keys:continue
            info=load(path) or {};due=due_for(path.stem,info.get('deadline'))
            if not due or not 2<=(due-now).total_seconds()/60<=15:continue
            reviewed+=1
            record,reason=check(root,path,now)
            if record:entries.append(record);keys.append(path.stem);frozen+=1
            else:skips[reason]=skips.get(reason,0)+1
        scan={'window_races':reviewed,'new_shadow_frozen':frozen,'skip_reasons':skips,'as_of':now.isoformat()}
        if not ledger.exists() or frozen:save(ledger,old)
        new=report(entries,scan)
        if not current.exists() or frozen or reviewed or new.get('frozen_races')!=(load(current) or {}).get('frozen_races'):
            save(current,new)
        print('V213_SHADOW_FREEZE_RESULTS_UNREAD',json.dumps(scan,ensure_ascii=False))
    elif a.phase=='settle':
        new_count=0
        for item in entries:
            if item.get('status')!='shadow_pending':continue
            due=parse(item.get('deadline_at'));freeze=parse(item.get('freeze_at'))
            if not due or not freeze or not now>due+dt.timedelta(minutes=2):continue
            result=load(root/'data/site_results'/(item['race_key']+'.json')) or {}
            result_time=parse(result.get('fetched_at'))
            if result.get('race_key')!=item['race_key'] or result.get('status')!='confirmed' or not result_time or result_time<=freeze:continue
            win=result.get('trifecta');payout=result.get('trifecta_payout_yen_per_100')
            if not isinstance(win,str) or not COMBO.fullmatch(win) or not isinstance(payout,(int,float)) or payout<=0:continue
            earned=sum(round(payout) for t in item['tickets'] if t['combo']==win)
            item.update(status='shadow_settled',winning_combo=win,official_payout_per_100_yen=payout,
              shadow_return_yen=earned,settled_at=now.isoformat(),result_fetched_at=result_time.isoformat())
            new_count+=1
        if new_count:
            save(ledger,old);save(current,report(entries,(load(current) or {}).get('last_scan')))
        print('V213_SHADOW_SETTLE_ONLY_PREVIOUSLY_FROZEN',new_count)
    else:print(json.dumps(report(entries),ensure_ascii=False,indent=2))

if __name__=='__main__':main()
