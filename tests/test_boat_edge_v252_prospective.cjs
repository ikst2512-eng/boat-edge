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
// Aggregate summaries intentionally retain only the latest 25/20 examples.
// A clipped aggregate MUST fail closed. Build a clearly isolated synthetic
// regression fixture from the actually listed rows; never publish its counts.
function listedRowsFixture(source,keys,paired){
 const d=JSON.parse(JSON.stringify(source));
 if(d.examples.length===d.scored_total)return d;
 assert(d.examples.length<d.scored_total,'Unexpected excess example rows');
 d.scored_total=d.examples.length;
 for(const k of keys){
  const x=d.comparisons[k], n=d.scored_total;
  const hits=d.examples.filter(row=>row.outcomes[k]===true).length;
  x.races=n;x.hit_rate_percent=+(100*hits/n).toFixed(2);
  if(paired){
   x.hits=hits;
   x.paired_gain=d.examples.filter(row=>row.outcomes[k]===true&&row.outcomes.hit10===false).length;
   x.paired_loss=d.examples.filter(row=>row.outcomes[k]===false&&row.outcomes.hit10===true).length;
   x.changed_races=k==='hit10'?0:n;
  }else{x.hit=hits}
 }
 return d;
}
if(v236.examples.length!==v236.scored_total)assert.equal(api.check236(v236),null,'Clipped V236 must not be claimed fully verified');
if(v240.examples.length!==v240.scored_total)assert.equal(api.check240(v240),null,'Clipped V240 must not be claimed fully verified');
const fixture236=listedRowsFixture(v236,['hit10','balance10','scenario7plus3','coverage15'],false);
const fixture240=listedRowsFixture(v240,['hit10','pair_coverage10','second_coverage10'],true);
const a=api.check236(fixture236),b=api.check240(fixture240);
assert(a&&b,'Listed-row regression fixture must verify consistently');
assert.equal(a.n,fixture236.scored_total);
assert.equal(b.n,fixture240.scored_total);
assert.equal(a.rows.find(x=>x.key==='coverage15').points,15);
assert.equal(b.rows.find(x=>x.key==='hit10').points,10);
assert.equal(b.rows.find(x=>x.key==='pair_coverage10').points,10);
// The cohort grows automatically: only compare against frozen per-race outcomes,
// not a prior run's hardcoded win/loss counts.
for(const key of ['hit10','pair_coverage10','second_coverage10']){
 const row=b.rows.find(x=>x.key===key);
 assert(row,'Missing frozen comparator '+key);
 const expectedHits=fixture240.examples.filter(r=>r.outcomes[key]===true).length;
 const expectedGain=fixture240.examples.filter(r=>r.outcomes[key]===true&&r.outcomes.hit10===false).length;
 const expectedLoss=fixture240.examples.filter(r=>r.outcomes[key]===false&&r.outcomes.hit10===true).length;
 assert.equal(row.hits,expectedHits,key+' frozen hits');
 assert.equal(row.gain,expectedGain,key+' prospective paired gain');
 assert.equal(row.loss,expectedLoss,key+' prospective paired loss');
}
assert.equal(b.paired,true);
assert.equal(a.paired,false);
const mutate=(obj,fn)=>{const clone=JSON.parse(JSON.stringify(obj));fn(clone);return clone};
assert.equal(api.check240(mutate(fixture240,d=>d.accuracy_improvement_proven=true)),null);
assert.equal(api.check240(mutate(fixture240,d=>d.production_model_changed=true)),null);
assert.equal(api.check240(mutate(fixture240,d=>d.promotion_authorized=true)),null);
assert.equal(api.check240(mutate(fixture240,d=>d.scope='FORMAL_FRESH')),null);
assert.equal(api.check240(mutate(fixture240,d=>d.comparisons.hit10.hits++)),null);
assert.equal(api.check240(mutate(fixture240,d=>d.comparisons.hit10.hit_rate_percent=99)),null);
assert.equal(api.check240(mutate(fixture240,d=>d.comparisons.pair_coverage10.points=15)),null);
assert.equal(api.check240(mutate(fixture240,d=>d.comparisons.pair_coverage10.paired_gain=9)),null);
assert.equal(api.check240(mutate(fixture240,d=>d.examples[1].outcomes.pair_coverage10=!d.examples[1].outcomes.pair_coverage10)),null);
assert.equal(api.check240(mutate(fixture240,d=>d.examples[1].race_key=d.examples[0].race_key)),null);
assert.equal(api.check240(mutate(fixture240,d=>d.examples[0].outcomes.hit10='true')),null);
assert.equal(api.check236(mutate(fixture236,d=>d.comparisons.coverage15.hit++)),null);
assert.equal(api.check236(mutate(fixture236,d=>d.comparisons.coverage15.avg_points=10)),null);
assert.equal(api.check236(mutate(fixture236,d=>d.scope='FORMAL_FRESH')),null);
// Additional chronologically independent date must remain explicitly represented.
const allDays=[...new Set(fixture240.examples.map(x=>x.race_key.slice(0,8)))].sort();
const newest=allDays[allDays.length-1];
const nextDay=new Date(Date.UTC(Number(newest.slice(0,4)),Number(newest.slice(4,6))-1,Number(newest.slice(6,8))+1))
 .toISOString().slice(0,10).replace(/-/g,'');
const day2=mutate(fixture240,d=>{
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
// V236 policy-specific headsecond10 is legal only on prospectively frozen V2/V3.
const v2Policy='PREDECLARED_HEAD_SECOND_COVERAGE_FROM_EXISTING_FROZEN_MODES_NO_NEW_ODDS_MULTIPLIER';
const v1='PREDECLARED_HEAD_TAIL_COVERAGE_NO_ODDS_MULTIPLIER_BOOST';
const v1Index=fullSource.lanes.v236.races.findIndex(r=>r.candidate_policy===v1);
assert(v1Index>=0);
const forwardProof=mutate(fullSource,d=>{
 const lane=d.lanes.v236,row=lane.races[v1Index];
 const hit10=row.categories.hit10;
 row.candidate_policy=v2Policy;row.categories.headsecond10='hit';
 const summary=lane.headsecond_by_frozen_policy[v2Policy];
 summary.matched_races++;
 summary.miss_categories.hit10[hit10]++;
 summary.miss_categories.headsecond10.hit++;
});
assert(api.fromFullMissProof(forwardProof),'Full cohort V2 row should remain displayable');
assert.equal(api.fromFullMissProof(mutate(forwardProof,d=>{
 d.lanes.v236.headsecond_by_frozen_policy[v2Policy].matched_races++;
})),null,'Corrupted V2 by-policy count must fail closed');
assert.equal(api.fromFullMissProof(mutate(fullSource,d=>{
 d.lanes.v236.races[v1Index].categories.headsecond10='hit';
})),null,'Legacy V1 mode cannot gain a post-hoc comparator');
assert(fullSource.lanes.v236.races_verified<=v236.scored_total);
assert(fullSource.lanes.v240.races_verified<=v240.scored_total);
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
// The real SITE-only cohort keeps growing. Use a *future relative to the
// newest verified race*, never a hardcoded date that eventually becomes old.
const proofDays=fullSource.lanes.v240.races.map(r=>r.date_jst).sort();
const latestProofDay=proofDays[proofDays.length-1];
const nextProofDay=new Date(Date.UTC(Number(latestProofDay.slice(0,4)),
 Number(latestProofDay.slice(4,6))-1,Number(latestProofDay.slice(6,8))+1))
 .toISOString().slice(0,10).replace(/-/g,'');
const multiday=mutate(fullSource,d=>{
 const lane=d.lanes.v240;
 const extra=JSON.parse(JSON.stringify(lane.races[0]));
 extra.race_key=nextProofDay+'-14-01';extra.date_jst=nextProofDay;
 lane.races.push(extra);lane.races_verified++;
 for(const key of Object.keys(extra.categories))lane.miss_categories[key][extra.categories[key]]++;
 d.site_verified_reference_races++;
});
const m=api.fromFullMissProof(multiday);
assert(m&&m.b.day.includes(nextProofDay),'Latest unseen day should be shown');
const truncated=mutate(fixture240,d=>{d.scored_total+=20;d.comparisons.hit10.races+=20;});
assert.equal(api.check240(truncated),null,'Never claim incomplete examples verify 100% of aggregate');

const html=fs.readFileSync('autopilot.html','utf8');
assert(html.includes('id="v252Evidence"'));
assert(html.includes('id="v252Equal"'));
assert(html.includes('id="v252Wide"'));
assert(html.includes('boat_edge_v252_prospective.js?v=257'));
assert.equal(requests,0);
console.log('V252_EQUAL_POINT_FORWARD_RESEARCH_GATES_PASS');
