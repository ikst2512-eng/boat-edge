'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const window={};
vm.runInNewContext(fs.readFileSync('assets/boat_edge_v278_next_watch.js','utf8'),{
 window,Date,Number,console
},{filename:'v278-watch'});
const nextHint=window.BoatEdgeV278Watch?.nextHint;
assert.equal(typeof nextHint,'function');
const source={
 schema:'BOAT_EDGE_V215_PRE_RESULT_READINESS_V1',
 scope:'PRE_RESULT_SITE_DIAGNOSTIC_NOT_FORMAL_FRESH',
 day_jst:'20261013',scheduled_races:132,
 next_race:{race_key:'20261013-14-01',venue:'鳴門',watch_start:'08:20',deadline:'08:35'}
};
const clone=()=>JSON.parse(JSON.stringify(source));
const before=new Date('2026-10-12T16:18:00Z');
const obj=nextHint(source,'20261013',before);
assert(obj && obj.race_key==='20261013-14-01');
assert(obj.label.includes('鳴門 1R') && obj.label.includes('08:20') && obj.label.includes('08:35'));
assert(obj.label.includes('保存済み予定'),'Must not claim official data actually published');
assert.equal(nextHint(source,'20261012',before),null,'Do not display next-day source on prior day');
assert.equal(nextHint(source,'20261013',new Date('2026-10-12T23:35:00Z')),null,'Expire at cutoff');
assert.equal(nextHint(source,'20261013',new Date('2026-10-13T01:00:00Z')),null,'No outdated planned race');
const alter=(fn)=>{const x=clone();fn(x);return nextHint(x,'20261013',before)};
assert.equal(alter(x=>x.scope='FORMAL_FRESH'),null);
assert.equal(alter(x=>x.day_jst='20261012'),null);
assert.equal(alter(x=>x.next_race.race_key='20261012-14-01'),null);
assert.equal(alter(x=>x.next_race.race_key='20261013-14-13'),null);
assert.equal(alter(x=>x.next_race.race_key='20261013-14-00'),null);
assert.equal(alter(x=>x.next_race.deadline='unverified'),null);
assert.equal(alter(x=>x.next_race.watch_start='09:00'),null);
assert.equal(alter(x=>x.next_race.venue=''),null);
assert.equal(alter(x=>x.scheduled_races=0),null);
assert.equal(alter(x=>x.scheduled_races='132'),null);
assert.equal(nextHint(null,'20261013',before),null);
assert.equal(nextHint(source,'20261013',{getTime(){return NaN}}),null);
const html=fs.readFileSync('autopilot.html','utf8');
assert(html.includes('boat_edge_v278_next_watch.js?v=278'));
assert(html.includes('BoatEdgeV278Watch?.nextHint?.(rd,a.day_jst)'));
assert(html.includes('次の監視予定は未確認'));
assert(html.indexOf('boat_edge_v278_next_watch.js?v=278')<html.indexOf("(function(){'use strict';"));
const actual=JSON.parse(fs.readFileSync('data/site_paper_sim/readiness_v215_current.json','utf8'));
if(actual.next_race&&actual.schema===source.schema){
 const morning=new Date(actual.day_jst.slice(0,4)+'-'+actual.day_jst.slice(4,6)+'-'+actual.day_jst.slice(6,8)+'T00:00:00+09:00');
 const v=nextHint(actual,actual.day_jst,morning);
 // A current real fixture can omit watch or deadline; never fabricate it.
 if(v)assert(v.race_key===actual.next_race.race_key);
}
console.log('V278_SOURCE_DATED_NEXT_WATCH_AND_EXPIRY_FAIL_CLOSED_PASS');
