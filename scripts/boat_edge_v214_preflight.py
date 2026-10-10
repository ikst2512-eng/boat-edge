#!/usr/bin/env python3
"""V214 pre-result-only diagnostics. Reads race schedule, frozen snapshots and source evidence, NEVER results."""
import datetime as dt, json, pathlib, argparse
from boat_edge_v214_shadow import check,due_for,load,save,JST,UTC
SCHEMA='BOAT_EDGE_V214_PRE_RESULT_DIAGNOSTIC_V1'
def audit(root,now):
    today=now.astimezone(JST).strftime('%Y%m%d')
    index=load(root/'data/today.json') or {}
    is_today=str(index.get('date','')).replace('-','')==today
    entries=[]; reasons={}
    if is_today:
        for venue in index.get('venues',[]):
            for race in venue.get('races',[]):
                key=race.get('race_key',''); due=due_for(key,race.get('deadline',''))
                if not due:continue
                left=(due-now).total_seconds()/60
                if not 2<=left<=15:continue
                p=root/'data/site_prediction_snapshots'/(key+'.json')
                if not p.is_file():reason='snapshot_missing'
                else:
                    accepted,reason=check(root,p,now)
                    if accepted:reason='verified_shadow_ready'
                reasons[reason]=reasons.get(reason,0)+1
                entries.append({'race_key':key,'venue':venue.get('venue'),'deadline':race.get('deadline'),
                                'minutes_left':round(left,1),'reason':reason})
    return {'schema':SCHEMA,'scope':'SITE_ONLY_PRE_RESULT_NO_RESULT_READ','date_jst':today,
            'schedule_source_today':is_today,'window_races':len(entries),'reason_counts':reasons,
            'recent_window':entries[:32],'last_observed_at':now.isoformat(),
            'not_a_purchase_or_formal_fresh_gate':True}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',default='.');ap.add_argument('--now')
    a=ap.parse_args();root=pathlib.Path(a.root).resolve()
    from boat_edge_v214_shadow import parse
    now=parse(a.now) if a.now else dt.datetime.now(UTC)
    if now is None:raise SystemExit('V214_INVALID_TIME')
    path=root/'data/site_paper_sim/preflight_v214_current.json';old=load(path) or {}
    item=audit(root,now)
    # Avoid constant Git commits outside race windows; preserve last useful diagnostic.
    if not old or item['window_races'] or old.get('window_races') or old.get('date_jst')!=item['date_jst'] or old.get('schedule_source_today')!=item['schedule_source_today']:
        if old!=item:save(path,item)
    print('V214_PREFLIGHT_PRE_RESULT_ONLY',json.dumps(item,ensure_ascii=False))
if __name__=='__main__':main()
