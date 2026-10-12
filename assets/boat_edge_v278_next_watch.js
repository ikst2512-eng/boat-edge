/* V278: read-only next pre-deadline watch hint from source-checked V215 data.
   Does not create predictions, fetch results, or claim live official beforeinfo. */
(()=>{'use strict';
 if(window.BoatEdgeV278Watch)return;
 const key=/^(20\d{6})-(\d{2})-(0[1-9]|1[0-2])$/;
 const hhmm=/^([01]\d|2[0-3]):[0-5]\d$/;
 const day=/^20\d{6}$/;
 function nextHint(doc,expectedDay,now=new Date()){
  if(!doc||doc.schema!=='BOAT_EDGE_V215_PRE_RESULT_READINESS_V1'||
     doc.scope!=='PRE_RESULT_SITE_DIAGNOSTIC_NOT_FORMAL_FRESH'||
     !day.test(expectedDay||'')||doc.day_jst!==expectedDay||
     !Number.isSafeInteger(doc.scheduled_races)||doc.scheduled_races<1||
     !Number.isFinite(now?.getTime?.()))return null;
  const x=doc.next_race||{},m=key.exec(x.race_key||'');
  if(!m||m[1]!==expectedDay||typeof x.venue!=='string'||
     !x.venue.trim()||x.venue.length>30||
     !hhmm.test(x.watch_start||'')||!hhmm.test(x.deadline||'')||
     x.watch_start>=x.deadline)return null;
  const date=expectedDay.slice(0,4)+'-'+expectedDay.slice(4,6)+'-'+expectedDay.slice(6,8);
  const deadline=new Date(date+'T'+x.deadline+':00+09:00');
  const watch=new Date(date+'T'+x.watch_start+':00+09:00');
  if(!Number.isFinite(deadline.getTime())||!Number.isFinite(watch.getTime())||
     now.getTime()>=deadline.getTime())return null;
  return {
   label:'次の監視予定（保存済み予定）: '+x.venue.trim()+' '+Number(m[3])+'R'
      +' / 監視目安 '+x.watch_start+' / 締切 '+x.deadline+'（日本時間）',
   race_key:x.race_key,
   watch_start:x.watch_start,deadline:x.deadline
  };
 }
 window.BoatEdgeV278Watch={nextHint};
})();
