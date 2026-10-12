'use strict';
/* V254: isolated display-only assertions. Never fetch result/payout/combined endpoints. */
const assert=require('assert'),fs=require('fs'),vm=require('vm');
const src=fs.readFileSync('assets/boat_edge_v108.js','utf8');
const start=src.indexOf('async function oddsFor(key){');
const end=src.indexOf('\nasync function resultFor(key){',start);
assert(start>0&&end>start,'V108 odds display function must exist');
const extracted=src.slice(start,end);
const key='20261012-03-03',deadline='12:08';
const odds={};
for(let a=1;a<=6;a++)for(let b=1;b<=6;b++)for(let c=1;c<=6;c++)
 if(a!==b&&a!==c&&b!==c)odds[a+'-'+b+'-'+c]=12.4;
assert.equal(Object.keys(odds).length,120);
const packet={
 schema_version:'boat-edge-site-odds-v71',race_key:key,
 source_url:'https://www.boatrace.jp/owpc/pc/race/odds3t?hd=20261012&jcd=03&rno=3',
 results_seen:false,scoring:false,phase:'PRE_RESULT_PURCHASE_ONLY',
 fetched_at:'2026-10-12T12:02:00+09:00',deadline,available_count:120,trifecta_odds:odds
};
const ctx={packet:structuredClone(packet),activeRace:{race_key:key,meta:{deadline}},
 clock:Date.parse('2026-10-12T12:07:00+09:00'),Date:null,Number,JSON,Object,Math,String,Set,Map};
ctx.Date=class extends Date {static now(){return ctx.clock}};
const harness=`
'use strict';
const be166OddsMeta=new Map();
const be166OddsPrice=v=>(v!==null&&v!==undefined&&v!==''&&Number.isFinite(Number(v))&&Number(v)>0)?Number(v):null;
function raceOf(){return activeRace;}
async function J(){return packet;}
${extracted}
globalThis.unit={oddsFor,meta:be166OddsMeta};`;
vm.runInNewContext(harness,ctx,{filename:'v254-odds-harness.js'});
const read=async()=>Object.keys(await ctx.unit.oddsFor(key)).length;
(async()=>{
 assert.equal(await read(),120,'valid predeadline 120 combinations available');
 assert.equal(ctx.unit.meta.get(key).status,'fresh');
 ctx.packet={...structuredClone(packet),source_url:'https://www.boatrace.jp.evil.test/owpc/pc/race/odds3t?bad=1'};
 assert.equal(await read(),0,'nonofficial domain must never display prices');
 assert.equal(ctx.unit.meta.get(key).status,'invalid');
 ctx.packet={...structuredClone(packet),source_url:'https://www.boatrace.jp/owpc/pc/race/odds3t?hd=20261012&jcd=03&rno=4'};
 assert.equal(await read(),0,'official URL for a different race must never display');
 ctx.packet={...structuredClone(packet),deadline:'12:09'};
 assert.equal(await read(),0,'race-clock mismatch must fail closed');
 ctx.packet={...structuredClone(packet),results_seen:true};
 assert.equal(await read(),0,'result-phase flag must never pass');
 ctx.packet=structuredClone(packet);
 ctx.clock=Date.parse('2026-10-12T12:08:00+09:00');
 assert.equal(await read(),0,'cutoff exact second must hide live odds');
 assert.equal(ctx.unit.meta.get(key).status,'past_deadline');
 ctx.clock=Date.parse('2026-10-12T12:08:01+09:00');
 assert.equal(await read(),0,'postdeadline cached odds must remain hidden');
 ctx.clock=Date.parse('2026-10-12T12:07:00+09:00');
 ctx.packet={...structuredClone(packet),fetched_at:'2026-10-12T11:50:00+09:00'};
 assert.equal(await read(),0,'stale odds must not display');
 assert.equal(ctx.unit.meta.get(key).status,'stale');
 ctx.packet={...structuredClone(packet),trifecta_odds:{...odds,'1-2-3':0}};
 assert.equal(await read(),0,'invalid combination price must fail closed');
 console.log('V254_ODDS_DISPLAY_PASS: 120, source, race deadline, result flag, cutoff, stale, zero');
})().catch(e=>{console.error(e);process.exitCode=1});
