#!/usr/bin/env python3
"""V215 site-only pre-result readiness. No result files, settlement or formal unlock.
Store prospective, date-scoped race-window diagnostics without retroactive reconstruction.
"""
import argparse
import datetime as dt
import json
import pathlib
from boat_edge_v214_shadow import load, save, due_for, check, parse, UTC, JST

SCHEMA='BOAT_EDGE_V215_PRE_RESULT_READINESS_V1'
HIST_SCHEMA='BOAT_EDGE_V215_DIAGNOSTIC_HISTORY_V1'


def source_gaps(root, key, now):
    """Observed pre-result source gaps; not proof that a prediction engine failed.

    This is strictly a diagnostic companion to the immutable shadow eligibility check.
    No result or payout file is opened, and absent evidence never becomes a PASS.
    """
    race=load(root/'data/races'/(key+'.json'))
    if not isinstance(race,dict):
        return ['race_file_missing']
    gaps=[]
    racers=race.get('racers') or []
    if len(racers)!=6:gaps.append('six_racers_unverified')
    audit=race.get('source_audit') or {}
    for source,max_age,label in [('race_card',16,'race_card'),('beforeinfo',15,'beforeinfo')]:
        record=audit.get(source) or {}
        if record.get('status')!='ok':
            gaps.append(label+'_not_ok')
        else:
            stamp=parse(record.get('fetched_at'))
            if stamp is None or not 0<=(now-stamp).total_seconds()<=max_age*60:
                gaps.append(label+'_stale')
    scratch=load(root/'data/site_scratches_v182'/(key+'.json')) or {}
    if scratch.get('race_key')!=key or scratch.get('blocked') is not False:
        gaps.append('scratch_missing_or_blocked')
    else:
        stamp=parse(scratch.get('checked_at'))
        if scratch.get('race_card_source_status')!='ok' or stamp is None or not 0<=(now-stamp).total_seconds()<=900:
            gaps.append('scratch_stale')
    odds=load(root/'data/site_odds'/(key+'.json')) or {}
    if odds.get('race_key')!=key or odds.get('phase')!='PRE_RESULT_PURCHASE_ONLY':
        gaps.append('pre_result_odds_unverified')
    else:
        stamp=parse(odds.get('fetched_at'))
        if stamp is None or not 0<=(now-stamp).total_seconds()<=900:
            gaps.append('pre_result_odds_stale')
    return gaps


def audit(root, now):
    now=now.astimezone(UTC)
    today=now.astimezone(JST).strftime('%Y%m%d')
    source=load(root/'data/today.json') or {}
    is_today=str(source.get('date') or '').replace('-','')==today
    races=[]
    if is_today:
        for venue in source.get('venues') or []:
            for race in venue.get('races') or []:
                key=race.get('race_key'); due=due_for(key,race.get('deadline'))
                if not due or not str(key).startswith(today+'-'):continue
                races.append((due,key,venue.get('venue','―'),str(race.get('deadline'))))
    races.sort()
    window=[]; forecast=[]; reasons={}; provisional={}
    for due,key,venue,hm in races:
        left=(due-now).total_seconds()/60
        if left<-1:continue
        if 2<=left<=15:
            snap=root/'data/site_prediction_snapshots'/(key+'.json')
            if not snap.is_file():reason='snapshot_missing'
            else:
                eligible,reason=check(root,snap,now)
                if eligible:reason='verified_shadow_ready'
                if not reason:reason='eligibility_unknown'
            reasons[reason]=reasons.get(reason,0)+1
            gaps=source_gaps(root,key,now)
            window.append({'race_key':key,'venue':venue,'deadline':hm,'minutes_left':round(left,1),
                           'reason':reason,'source_gaps':gaps})
        if 0<=left<=90 and len(forecast)<8:
            race=load(root/'data/races'/(key+'.json')) or {}
            card=(race.get('source_audit') or {}).get('race_card') or {}
            before=(race.get('source_audit') or {}).get('beforeinfo') or {}
            prediction=root/'data/site_prediction_snapshots'/(key+'.json')
            scratch=load(root/'data/site_scratches_v182'/(key+'.json')) or {}
            if 0<=left<=15:
                provisional['race_card_ok']=provisional.get('race_card_ok',0)+(card.get('status')=='ok')
                provisional['beforeinfo_ok']=provisional.get('beforeinfo_ok',0)+(before.get('status')=='ok')
                provisional['snapshot_exists']=provisional.get('snapshot_exists',0)+prediction.is_file()
            forecast.append({'race_key':key,'venue':venue,'deadline':hm,
                  'watch_start':(due-dt.timedelta(minutes=15)).astimezone(JST).strftime('%H:%M'),
                  'race_card_status':card.get('status','unknown'),
                  'beforeinfo_status':before.get('status','unknown'),
                  'snapshot_exists':prediction.is_file(),
                  'scratch_status':'blocked' if scratch.get('blocked') is True else 'uncertified' if scratch.get('blocked') is False else 'missing'})
    next_race=next(((due,key,venue,hm) for due,key,venue,hm in races if due>now),None)
    next_watch_start=(next_race[0]-dt.timedelta(minutes=15)).astimezone(JST).strftime('%H:%M') if next_race else None
    return {'schema':SCHEMA,'scope':'PRE_RESULT_SITE_DIAGNOSTIC_NOT_FORMAL_FRESH',
            'day_jst':today,'schedule_source_today':is_today,'scheduled_races':len(races),
            'window_races':len(window),'reason_counts':reasons,'current_window':window[:32],
            'next_race':{'race_key':next_race[1],'venue':next_race[2],'deadline':next_race[3],
                         'watch_start':next_watch_start} if next_race else None,
            'upcoming':forecast,'source_counts_in_window':provisional,
            'checked_at':now.isoformat(),'not_a_purchase_or_proven_accuracy':True}


def run(root,now):
    state=root/'data/site_paper_sim/readiness_v215_current.json'
    cur=audit(root,now)
    history_file=root/'data/site_paper_sim/readiness_history_v215'/(cur['day_jst']+'.json')
    old=load(state) or {}
    hist=load(history_file) or {'schema':HIST_SCHEMA,'day_jst':cur['day_jst'],'observations':{}}
    if hist.get('schema')!=HIST_SCHEMA or hist.get('day_jst')!=cur['day_jst']:
        hist={'schema':HIST_SCHEMA,'day_jst':cur['day_jst'],'observations':{}}
    seen=hist['observations']
    changed=False
    for item in cur['current_window']:
        key=item['race_key']
        old_entry=seen.get(key)
        row={'race_key':key,'venue':item['venue'],'deadline':item['deadline'],
             'first_seen_at':old_entry['first_seen_at'] if old_entry else cur['checked_at'],
             'last_seen_at':cur['checked_at'],
             'reason':item['reason'],
             'reasons_seen':sorted(set((old_entry or {}).get('reasons_seen',[])+[item['reason']])),
             'source_gaps':item.get('source_gaps',[]),
             'source_gaps_seen':sorted(set((old_entry or {}).get('source_gaps_seen',[])+item.get('source_gaps',[]))),
             'observed_checks':int((old_entry or {}).get('observed_checks',0))+1}
        seen[key]=row;changed=True
    # No backfill or result queries. A completed window's final observed diagnostics persist.
    if changed or not history_file.exists() or (load(history_file) or {}).get('day_jst')!=cur['day_jst']:
        save(history_file,hist)
    cur['day_observed_races']=len(seen)
    cur['day_verified_races']=sum('verified_shadow_ready' in x.get('reasons_seen',[]) for x in seen.values())
    counts={}
    for x in seen.values():counts[x['reason']]=counts.get(x['reason'],0)+1
    cur['day_latest_reasons']=counts
    # No 5-minute commits before race windows; only future race identity, readiness, or gate status changes.
    compare_keys=['day_jst','schedule_source_today','scheduled_races','window_races','reason_counts',
        'current_window','next_race','upcoming','source_counts_in_window','day_observed_races',
        'day_verified_races','day_latest_reasons']
    meaningful=not old or changed or any(old.get(k)!=cur.get(k) for k in compare_keys)
    if meaningful:save(state,cur)
    print('V215_READINESS_NO_RESULT_READ',json.dumps({
       'date':cur['day_jst'],'scheduled':cur['scheduled_races'],
       'in_window':cur['window_races'],'day_observed':len(seen),
       'next':cur['next_race'],'reasons':cur['reason_counts'],
       'state_written':meaningful},ensure_ascii=False))
    return cur

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',default='.');p.add_argument('--now')
    args=p.parse_args();now=parse(args.now) if args.now else dt.datetime.now(UTC)
    if now is None:raise SystemExit('V215_INVALID_NOW')
    run(pathlib.Path(args.root).resolve(),now)
if __name__=='__main__':main()
