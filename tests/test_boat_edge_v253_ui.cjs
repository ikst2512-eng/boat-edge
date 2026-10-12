'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const window={};
const doc={readyState:'loading',addEventListener(){}};
vm.runInNewContext(fs.readFileSync('assets/boat_edge_v253_misses.js','utf8'),{
 window,document:doc,Date,Number,Set,console,setInterval(){}
},{filename:'v253'});
const validate=window.BoatEdgeV253.validated;
const data=JSON.parse(fs.readFileSync('data/site_autopilot/v253_miss_diagnostics_current.json','utf8'));
const valid=validate(data);
assert(valid,'V253 data contract failed');
for(const lane of ['v236','v240']){
 assert(valid[lane].races_verified>0);
 for(const [k,counts] of Object.entries(valid[lane].miss_categories)){
  assert.equal(Object.values(counts).reduce((a,b)=>a+b,0),valid[lane].races_verified,k);
 }
}
const alter=(fn)=>{const x=JSON.parse(JSON.stringify(data));fn(x);return validate(x)};
assert.equal(alter(x=>x.formal_result_access=true),null);
assert.equal(alter(x=>x.production_model_changed=true),null);
assert.equal(alter(x=>x.accuracy_improvement_proven=true),null);
assert.equal(alter(x=>x.lanes.v236.races_verified++),null);
assert.equal(alter(x=>x.lanes.v240.miss_categories.hit10.hit++),null);
assert.equal(alter(x=>x.lanes.v236.races[0].winning_combo='7-5-2'),null);
assert.equal(alter(x=>x.lanes.v236.races[0].categories.hit10='fabricated'),null);
assert.equal(alter(x=>x.lanes.v240.races[0].race_key=x.lanes.v240.races[1].race_key),null);
const html=fs.readFileSync('autopilot.html','utf8');
assert(html.includes('id="v253Misses"'));
assert(html.includes('boat_edge_v253_misses.js?v=253'));
console.log('V253_MOBILE_EVIDENCE_TAXONOMY_VALIDATION_PASS');
