'use strict';
/* V266 same-race, same-point paired misses, never retroactive predictions. */
const assert=require('assert'),fs=require('fs'),vm=require('vm');
const code=fs.readFileSync('assets/boat_edge_v253_misses.js','utf8');
const window={},document={readyState:'loading',addEventListener:()=>{},getElementById:()=>null};
vm.runInNewContext(code,{window,document,Set,Math,Number,Object,Array,Date});
const {paired}=window.BoatEdgeV253;
const row=(control,candidate)=>({categories:{hit10:control?'hit':'third_absent_given_head_second',
 pair_coverage10:candidate?'hit':'second_absent_given_head',
 second_coverage10:candidate?'hit':'head_absent'}});
const lane={races:[row(true,true),row(true,true),row(true,false),row(false,true),
 row(false,false),row(false,false)]};
let r=paired(lane,'pair_coverage10');
assert.equal(r.races,6);assert.equal(r.gain,1);assert.equal(r.loss,1);
assert.equal(r.both,2);assert.equal(r.neither,2);assert.equal(r.discordant,2);
assert.equal(r.p_value,1);
r=paired({races:[row(false,true),row(false,true),row(false,true),row(false,true),row(false,true)]},'pair_coverage10');
assert.equal(r.gain,5);assert.equal(r.loss,0);assert.equal(r.p_value,0.0625);
r=paired({races:[row(true,true),row(true,true)]},'pair_coverage10');
assert.equal(r.discordant,0);assert.equal(r.p_value,1);
assert.equal(paired(null,'pair_coverage10'),null);
assert.equal(paired(lane,'missing_mode'),null);
assert(!code.includes('data/formal_predictions/'));
assert(!code.includes('data/site_results/'));
console.log('V266_PAIRED_SAME_RACE_MISS_EXACT_TEST_PASS');
