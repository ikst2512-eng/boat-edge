'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const listeners={};let requests=0;
const document={readyState:'loading',addEventListener(type,fn){listeners[type]=fn},getElementById(){return null}};
const context={window:{},document,fetch:()=>{requests++;throw Error('No network while verifying')},Date,Number,Math,Set,console};
vm.runInNewContext(fs.readFileSync('assets/boat_edge_v252_prospective.js','utf8'),context,{filename:'v252'});
const api=context.window.BoatEdgeV252;
assert(api&&typeof api.check236==='function'&&typeof api.check240==='function');
const v236=JSON.parse(fs.readFileSync('data/site_autopilot/v236_score_current.json','utf8'));
const v240=JSON.parse(fs.readFileSync('data/site_autopilot/v240_score_current.json','utf8'));
const a=api.check236(v236),b=api.check240(v240);
assert(a&&b,'Expected to verify frozen source-only experiment summaries');
assert.equal(a.n,v236.scored_total);
assert.equal(b.n,v240.scored_total);
assert.equal(a.rows.find(x=>x.key==='coverage15').points,15);
assert.equal(b.rows.find(x=>x.key==='hit10').points,10);
assert.equal(b.rows.find(x=>x.key==='pair_coverage10').points,10);
// The cohort grows automatically: only compare against frozen per-race outcomes,
// not a prior run's hardcoded win/loss counts.
for(const key of ['hit10','pair_coverage10','second_coverage10']){
 const row=b.rows.find(x=>x.key===key);
 assert(row,'Missing frozen comparator '+key);
 const expectedHits=v240.examples.filter(r=>r.outcomes[key]===true).length;
 const expectedGain=v240.examples.filter(r=>r.outcomes[key]===true&&r.outcomes.hit10===false).length;
 const expectedLoss=v240.examples.filter(r=>r.outcomes[key]===false&&r.outcomes.hit10===true).length;
 assert.equal(row.hits,expectedHits,key+' frozen hits');
 assert.equal(row.gain,expectedGain,key+' prospective paired gain');
 assert.equal(row.loss,expectedLoss,key+' prospective paired loss');
}
assert.equal(b.paired,true);
assert.equal(a.paired,false);
const mutate=(obj,fn)=>{const clone=JSON.parse(JSON.stringify(obj));fn(clone);return clone};
assert.equal(api.check240(mutate(v240,d=>d.accuracy_improvement_proven=true)),null);
assert.equal(api.check240(mutate(v240,d=>d.production_model_changed=true)),null);
assert.equal(api.check240(mutate(v240,d=>d.promotion_authorized=true)),null);
assert.equal(api.check240(mutate(v240,d=>d.scope='FORMAL_FRESH')),null);
assert.equal(api.check240(mutate(v240,d=>d.comparisons.hit10.hits++)),null);
assert.equal(api.check240(mutate(v240,d=>d.comparisons.hit10.hit_rate_percent=99)),null);
assert.equal(api.check240(mutate(v240,d=>d.comparisons.pair_coverage10.points=15)),null);
assert.equal(api.check240(mutate(v240,d=>d.comparisons.pair_coverage10.paired_gain=9)),null);
assert.equal(api.check240(mutate(v240,d=>d.examples[1].outcomes.pair_coverage10=!d.examples[1].outcomes.pair_coverage10)),null);
assert.equal(api.check240(mutate(v240,d=>d.examples[1].race_key=d.examples[0].race_key)),null);
assert.equal(api.check240(mutate(v240,d=>d.examples[0].outcomes.hit10='true')),null);
assert.equal(api.check236(mutate(v236,d=>d.comparisons.coverage15.hit++)),null);
assert.equal(api.check236(mutate(v236,d=>d.comparisons.coverage15.avg_points=10)),null);
assert.equal(api.check236(mutate(v236,d=>d.scope='FORMAL_FRESH')),null);
// Additional chronologically independent date must remain explicitly represented.
const allDays=[...new Set(v240.examples.map(x=>x.race_key.slice(0,8)))].sort();
const newest=allDays[allDays.length-1];
const nextDay=new Date(Date.UTC(Number(newest.slice(0,4)),Number(newest.slice(4,6))-1,Number(newest.slice(6,8))+1))
 .toISOString().slice(0,10).replace(/-/g,'');
const day2=mutate(v240,d=>{
 const newRace=JSON.parse(JSON.stringify(d.examples[0]));
 newRace.race_key=nextDay+'-14-01';d.examples.push(newRace);
 d.scored_total++;for(const [k,x] of Object.entries(d.comparisons)){
  x.races++;if(newRace.outcomes[k])x.hits++;
  x.hit_rate_percent=+(100*x.hits/x.races).toFixed(2);
  if(k==='hit10')x.changed_races=0;
  else x.changed_races++;
  if(k!=='hit10'){
   if(newRace.outcomes[k]&&!newRace.outcomes.hit10)x.paired_gain++;
   if(!newRace.outcomes[k]&&newRace.outcomes.hit10)x.paired_loss++;
  }
 }
});
const crossDay=api.check240(day2);
assert(crossDay&&crossDay.day===allDays[0]+'〜'+nextDay);
// Full SHA-attested source V253 stays verifiable when V236/V240 aggregate
// summaries clip examples to their latest 25/20 rows.
const fullSource=JSON.parse(fs.readFileSync('data/site_autopilot/v253_miss_diagnostics_current.json','utf8'));
const full=api.fromFullMissProof(fullSource);
assert(full?.a&&full?.b,'Need complete V253 provenance-backed cohort');
assert.equal(full.a.n,fullSource.lanes.v236.races_verified);
assert.equal(full.b.n,fullSource.lanes.v240.races_verified);
for(const [lane,block] of [['v236',full.a],['v240',full.b]]){
 const source=fullSource.lanes[lane];
 for(const row of block.rows){
  assert.equal(row.hits,source.races.filter(r=>r.categories[row.key]==='hit').length);
  assert.equal(row.gain,source.races.filter(r=>r.categories[row.key]==='hit'&&r.categories.hit10!=='hit').length);
  assert.equal(row.loss,source.races.filter(r=>r.categories[row.key]!=='hit'&&r.categories.hit10==='hit').length);
 }
}
assert.equal(api.fromFullMissProof(mutate(fullSource,d=>d.formal_result_access=true)),null);
assert.equal(api.fromFullMissProof(mutate(fullSource,d=>d.production_model_changed=true)),null);
assert.equal(api.fromFullMissProof(mutate(fullSource,d=>d.lanes.v236.miss_categories.hit10.hit++)),null);
assert.equal(api.fromFullMissProof(mutate(fullSource,d=>d.lanes.v240.races[0].categories.hit10='invented')),null);
assert.equal(api.fromFullMissProof(mutate(fullSource,d=>d.lanes.v240.races[0].race_key=d.lanes.v240.races[1].race_key)),null);
const multiday=mutate(fullSource,d=>{
 const lane=d.lanes.v240;
 const extra=JSON.parse(JSON.stringify(lane.races[0]));
 extra.race_key='20261013-14-01';extra.date_jst='20261013';
 lane.races.push(extra);lane.races_verified++;
 for(const key of Object.keys(extra.categories))lane.miss_categories[key][extra.categories[key]]++;
 d.site_verified_reference_races++;
});
const m=api.fromFullMissProof(multiday);
assert(m&&m.b.day.includes('20261013'),'Latest unseen day should be shown');
const truncated=mutate(v240,d=>{d.scored_total+=20;d.comparisons.hit10.races+=20;});
assert.equal(api.check240(truncated),null,'Never claim incomplete examples verify 100% of aggregate');

const html=fs.readFileSync('autopilot.html','utf8');
assert(html.includes('id="v252Evidence"'));
assert(html.includes('id="v252Equal"'));
assert(html.includes('id="v252Wide"'));
assert(html.includes('boat_edge_v252_prospective.js?v=257'));
assert.equal(requests,0);
console.log('V252_EQUAL_POINT_FORWARD_RESEARCH_GATES_PASS');
