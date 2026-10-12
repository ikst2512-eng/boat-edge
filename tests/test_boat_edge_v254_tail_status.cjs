'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const window={};
const document={readyState:'loading',addEventListener(){}};
vm.runInNewContext(fs.readFileSync('assets/boat_edge_v254_tail_status.js','utf8'),{
 window,document,Date,Number,console,setInterval(){}
},{filename:'v254-tail-status'});
const api=window.BoatEdgeV254;
const pre={
 schema:'BOAT_EDGE_V254_FUTURE_THIRD_TAIL_PRE_SUMMARY_V1',
 scope:'PRE_RESULT_FUTURE_SITE_RESEARCH_NOT_FORMAL_FRESH',
 result_access:false,production_model_changed:false,
 accuracy_improvement_proven:false,model_promotion_authorized:false,
 day_jst:'20261013',frozen_today:8,third_tail_novel_races_today:5,third_tail_novel_tickets_today:9
};
const score={
 schema:'BOAT_EDGE_V254_FUTURE_THIRD_TAIL_SCORE_SUMMARY_V1',
 scope:'POST_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH',
 formal_result_access:false,production_model_changed:false,
 accuracy_improvement_proven:false,model_promotion_authorized:false,
 real_or_paper_wagers_placed:0,scored_total:6,
 affected_races:5,
 comparisons:{hit10:{hits:2,races:6,points:10},
  third_tail10:{hits:3,races:6,points:10,paired_gain:2,paired_loss:1}},
 examples:[],
};
const alter=(x,fn)=>{const obj=JSON.parse(JSON.stringify(x));fn(obj);return obj};
assert.equal(api.validPre(pre),true);
assert.equal(api.validPre(alter(pre,x=>x.result_access=true)),false);
assert.equal(api.validPre(alter(pre,x=>x.accuracy_improvement_proven=true)),false);
assert.equal(api.validPre(alter(pre,x=>x.third_tail_novel_tickets_today=99)),false);
assert.equal(api.validPre(alter(pre,x=>x.day_jst='2026101')),false);
assert.equal(api.validScore(score),true);
assert.equal(api.validScore(alter(score,x=>x.scope='FORMAL_FRESH')),false);
assert.equal(api.validScore(alter(score,x=>x.production_model_changed=true)),false);
assert.equal(api.validScore(alter(score,x=>x.comparisons.third_tail10.points=15)),false);
assert.equal(api.validScore(alter(score,x=>x.comparisons.third_tail10.hits=6)),false);
assert.equal(api.validScore(alter(score,x=>x.affected_races=2)),false);
// The new fields audit prospective source throughput, not hypothetical hits.
const proofPre={...pre,
 source_cohorts_today:10,future_window_cohorts_seen:3,
 unfrozen_future_window_at_start:2,new_frozen_this_run:1,
 rejected_current_run:{SOURCE_GIT_PROVENANCE_UNVERIFIED:1}};
assert.equal(api.validPre(proofPre),true);
assert.equal(api.validPre(alter(proofPre,x=>x.source_cohorts_today=7)),false);
assert.equal(api.validPre(alter(proofPre,x=>x.future_window_cohorts_seen=11)),false);
assert.equal(api.validPre(alter(proofPre,x=>x.unfrozen_future_window_at_start=4)),false);
assert.equal(api.validPre(alter(proofPre,x=>x.new_frozen_this_run=3)),false);
assert.equal(api.validPre(alter(proofPre,x=>x.rejected_current_run.FAILURE=-1)),false);
assert.equal(api.validPre(alter(proofPre,x=>{delete x.source_cohorts_today})),false);
assert(fs.readFileSync('autopilot.html','utf8').includes('boat_edge_v254_tail_status.js?v=257'));
console.log('V254_FUTURE_ONLY_RESEARCH_STATUS_FAIL_CLOSED_PASS');
