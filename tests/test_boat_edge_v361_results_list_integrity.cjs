'use strict';
/* V361 read-only, synthetic site-reference results-list verification; no real result reads. */
const assert=require('node:assert/strict'),test=require('node:test'),vm=require('node:vm'),fs=require('node:fs');
const code=fs.readFileSync('assets/boat_edge_v241_results.js','utf8');
const nodes=new Map();
const doc={
 getElementById(k){if(!nodes.has(k))nodes.set(k,{value:'hit',textContent:'',innerHTML:'',addEventListener(){}});return nodes.get(k);},
 querySelectorAll(){return []}
};
const window={};
vm.runInNewContext(code,{window,document:doc,Set,Intl,Date,Number,JSON,
 fetch:async()=>{throw Error('OFFLINE_FIXTURE_NO_RESULTS_ACCESS')}},{filename:'v361.js'});
const api=window.BoatEdgeV241ResultsUI;
const one=(hit=true)=>({hit,stake_yen:10000,tickets:10,hypothetical_return_yen:hit?18000:0,hypothetical_profit_yen:hit?8000:-10000});
function fixture(){
 const row={race_key:'20261013-06-01',date_jst:'20261013',post_result_verified:true,
  winning_combo:'1-2-3',head_prediction:'1',head_hit:true,top10_hit:true,
  first_frozen_commit:'a'.repeat(40),precommitted_sha256:'b'.repeat(64),
  official_payout_per_100_yen:180,round:1,venue:'浜名湖',
  result_source:'https://www.boatrace.jp/owpc/pc/race/raceresult?hd=20261013&jcd=06&rno=1',
  mode_outcomes:{hit:one(true),balance:one(false),hole:one(false),narrow:one(false)}};
 return {schema:'BOAT_EDGE_V241_VERIFIED_SITE_RESULTS_V1',
  scope:'VERIFIED_POST_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH',
  formal_result_access:false,production_model_changed:false,real_or_paper_wagers_placed:0,
  settled_verified_races:1,top10_hits:1,head_hits:1,date_latest:'20261013',rows:[row]};
}
test('V361 valid saved site-only result stays visible, with separate head/Top10 counts',()=>{
 const d=fixture();
 assert.equal(api.verifiedRow(d.rows[0]),true);
 assert.equal(api.verifiedReport(d),true);
 const info=api.sampleInfo(d);
 assert(info&&info.head===1&&info.top===1);
 assert.match(info.label,/サイト参考予想のみ/);
});
test('V361 forged score or missing immutable freeze must not appear in results list',()=>{
 for(const mutate of [
  d=>{d.rows[0].post_result_verified=false;},
  d=>{d.rows[0].precommitted_sha256='invalid';},
  d=>{d.rows[0].first_frozen_commit=null;},
  d=>{d.rows[0].mode_outcomes.hit.hit=false;},
  d=>{d.rows[0].mode_outcomes.narrow.stake_yen=0;},
  d=>{d.rows[0].mode_outcomes.hole.hypothetical_profit_yen=999;},
  d=>{d.rows[0].head_hit=false;},
  d=>{d.rows[0].winning_combo='1-1-3';},
  d=>{d.production_model_changed=true;},
  d=>{d.scope='FORMAL_FRESH_APPROVED_PRE_RESULT';},
  d=>{d.rows.push({...d.rows[0]});d.settled_verified_races=2;d.head_hits=2;d.top10_hits=2;}
 ]){
  const d=fixture();mutate(d);
  assert.equal(api.verifiedReport(d),false);
  assert.equal(api.sampleInfo(d),null);
 }
});
test('V361 official result link is restricted to official HTTPS page',()=>{
 const d=fixture(),row=d.rows[0];
 assert.match(api.officialLink(row),/https:\/\/www\.boatrace\.jp/);
 for(const url of ['javascript:alert(1)','https://attacker.invalid/boatrace','http://www.boatrace.jp/owpc/pc/race/raceresult','https://www.boatrace.jp.attacker.invalid/owpc/pc/race/raceresult?x=1']){
  assert.doesNotMatch(api.officialLink({...row,result_source:url}),/href=/);
 }
});
