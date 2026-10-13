'use strict';
/* V360: synthetic site-only home banner tests. No real results or Formal Fresh access. */
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('assets/boat_edge_v241_home.js','utf8');
const SHA='a'.repeat(64),COMMIT='b'.repeat(40);
const outcome=(hit=true)=>({hit,stake_yen:10000,hypothetical_return_yen:hit?12000:0,hypothetical_profit_yen:hit?2000:-10000});
function documentFixture(){
 const row={race_key:'20261013-06-01',date_jst:'20261013',post_result_verified:true,
  precommitted_sha256:SHA,first_frozen_commit:COMMIT,venue:'浜名湖',round:1,
  winning_combo:'1-2-3',head_prediction:'1',head_hit:true,top10_hit:true,
  official_payout_per_100_yen:120,mode_outcomes:{hit:outcome(),balance:outcome(false),hole:outcome(false),narrow:outcome(false)}};
 return {schema:'BOAT_EDGE_V241_VERIFIED_SITE_RESULTS_V1',
  scope:'VERIFIED_POST_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH',
  formal_result_access:false,production_model_changed:false,
  real_or_paper_wagers_placed:0,settled_verified_races:1,top10_hits:1,head_hits:1,rows:[row]};
}
function boot(report){
 const results={innerHTML:'',textContent:''},status={textContent:''};
 const doc={getElementById:id=>id==='be241HomeResults'?results:id==='be241HomeResultsStatus'?status:null};
 const window={};
 vm.runInNewContext(source,{window,document:doc,fetch:async()=>({ok:true,json:async()=>report}),
  Date,Number,Set,String,JSON},{filename:'boat_edge_v241_home.js'});
 return {api:window.BoatEdgeV241Home,results,status,settle:()=>new Promise(resolve=>setImmediate(resolve))};
}
test('V360 only verified site-only row may carry home 🎯; no formal scoring claim',async()=>{
 const doc=documentFixture(),v=boot(doc);
 assert.equal(v.api.verifiedReport(doc),true);
 await v.settle();
 assert.match(v.results.innerHTML,/🎯 的中/);
 assert.match(v.status.textContent,/サイト参考予想の厳格検証 1R/);
 assert.doesNotMatch(v.results.innerHTML,/正式Fresh/);
});
test('V360 wrong per-row hit, missing commit or production flag stops all home hit banners',async()=>{
 for(const mutant of [
  d=>{d.rows[0].mode_outcomes.hit.hit=false;},
  d=>{d.rows[0].post_result_verified=false;},
  d=>{d.rows[0].first_frozen_commit='invalid';},
  d=>{d.production_model_changed=true;},
  d=>{d.formal_result_access=true;},
  d=>{d.scope='FORMAL_FRESH';},
  d=>{d.real_or_paper_wagers_placed=1;}
 ]){
  const doc=documentFixture();mutant(doc);
  const ui=boot(doc);
  assert.equal(ui.api.verifiedReport(doc),false);
  await ui.settle();
  assert.doesNotMatch(ui.results.innerHTML,/🎯/);
  assert.match(ui.results.textContent,/確認できる結果データはまだありません/);
 }
});
test('V360 fabricated counts, duplicate keys, and invalid finished combo are rejected',async()=>{
 for(const mutant of [
  d=>{d.top10_hits=2;},d=>{d.head_hits=0;},
  d=>{d.rows[0].winning_combo='1-1-3';},
  d=>{d.rows.push({...d.rows[0]});d.settled_verified_races=2;d.top10_hits=2;d.head_hits=2;}
 ]){
  const doc=documentFixture();mutant(doc);
  const ui=boot(doc);assert.equal(ui.api.verifiedReport(doc),false);await ui.settle();
  assert.doesNotMatch(ui.results.innerHTML,/🎯/);
 }
});
test('V360 source text is escaped and only approved numbers appear',async()=>{
 const d=documentFixture();d.rows[0].venue='<script>alert(1)</script>';
 const ui=boot(d);await ui.settle();
 assert.match(ui.results.innerHTML,/&lt;script&gt;/);
 assert.doesNotMatch(ui.results.innerHTML,/<script>/);
});
