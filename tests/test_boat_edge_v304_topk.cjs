'use strict';
/* Fixture-only UI test: no data/network, no formal results, no prediction engine. */
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const js=fs.readFileSync('assets/boat_edge_v207_first_prediction.js','utf8');
const css=fs.readFileSync('assets/boat_edge_v304_topk_mobile.css','utf8');
const window={},document={readyState:'loading',addEventListener(){}};
vm.runInNewContext(js,{window,document,Number,Date,Math,Set,Map,JSON,Intl},{filename:'v304.js'});
const api=window.BoatEdgeV207;
assert.equal(api.version,'V306-DISPLAY-ONLY');
const list=Array.from({length:10},(_,i)=>[1,2,3,4,5,6].flatMap(a=>[1,2,3,4,5,6]
  .filter(b=>b!==a).map(b=>[a,b,[1,2,3,4,5,6].find(c=>c!==a&&c!==b)].join('-')))[i]);
const row=(combo,view,raw)=>({
 dataset:{be257View:view},
 querySelector(q){return q==='b'?{textContent:combo}:q==='.be140-ticket-money'?{textContent:raw}:null}
});
const ten=list.map(c=>row(c,'reference','現在の参考配分 500円'));
assert.equal(api.validTickets(ten),true);
assert.equal(api.ticketClarity(list).top10.includes('上位10点'),true);
assert.equal(api.ticketClarity(list.slice(0,3)).top10.includes('未確認'),true);
assert.equal(api.validTickets([ten[0],ten[0]]),false);
assert.equal(api.validTickets([row('1-1-2','reference','現在の参考配分 500円')]),false);
assert.equal(api.validTickets([]),false);
assert.equal(api.validTickets(Array(121).fill(ten[0])),false);
assert.equal(api.shownStake(ten[0],false),500);
assert.equal(api.shownStake(ten[0],true),null);
assert.equal(api.shownStake(row('1-2-3','frozen','締切前の保存配分 300円'),true),300);
assert.equal(api.shownStake(row('1-2-3','frozen','締切前の配分記録なし'),true),null);
assert.equal(api.shownStake(row('1-2-3','reference','配分 10000円'),false),null);
assert.equal(api.shownStake(row('1-2-3','unknown','現在の参考配分 1000円'),false),null);
assert.equal(api.shownStake(row('1-2-3','reference','現在の参考配分 不明'),false),null);
assert(js.includes('data-be207="ten"'));
assert(js.includes("const count=showAll?rows.length:showTen?10:showFive?5:3;"));
assert(js.includes("proof?.quality==='verified'"));
assert(js.includes("const pendingScratch=!settled&&st.kind!=='partial'"));
assert(js.includes('relative+\'（未校正）\''));
assert(!js.includes("prob+' 予測'"));
assert(js.includes('元画面の参考配分合計'));
assert(js.includes('stake!==null&&verifiedPrice&&payout!==null'));
assert(js.includes('画面 V306'));
assert(css.includes('min-height:44px'));
assert(css.includes('grid-template-columns:repeat(3,minmax(0,1fr))'));
assert(css.includes('#be251Outcome .be251-money'));
if(fs.existsSync('index.html')){
 const html=fs.readFileSync('index.html','utf8');
 assert(html.includes('boat_edge_v304_topk_mobile.css?v=306'));
 assert(html.includes('boat_edge_v207_first_prediction.js?v=208&amp;a24=1&amp;ui=306'));
}
/* V306: the existing readonly V307 runner invokes this file; execute related
 * presentation-only fixtures on native Node too, without editing workflows. */
if(typeof process!=='undefined'&&process?.versions?.node){
 const {execFileSync}=require('node:child_process');
 for(const [file,signature] of [
  ['tests/test_boat_edge_v305_evidence.cjs','V305_RACE_SCOPED_EXHIBITION_PROVENANCE_FAIL_CLOSED_PASS'],
  ['tests/test_boat_edge_v306_race_switch.cjs','V306_RACE_SWITCH_STALE_TICKETS_SUPPRESSED_PASS']
 ]){
  assert(fs.existsSync(file),'required UI regression missing: '+file);
  const output=execFileSync(process.execPath,[file],{encoding:'utf8',timeout:15000,stdio:['ignore','pipe','pipe']});
  assert(output.includes(signature),'related UI regression not proven: '+file);
  console.log(output.trim());
 }
}
/* V313 is a read-only release bundle smoke check, invoked from the already
 * approved V307 candidate test entry point without workflow changes. */
if(typeof process!=='undefined'&&process?.versions?.node){
 const {execFileSync}=require('node:child_process');
 const smoke='tests/test_boat_edge_v313_release_smoke.cjs';
 assert(fs.existsSync(smoke),'V313 release smoke fixture missing');
 const result=execFileSync(process.execPath,[smoke],{encoding:'utf8',timeout:15000,stdio:['ignore','pipe','pipe']});
 assert(result.includes('V313_MAIN_BUNDLE_UI_READONLY_CONTRACT_PASS'),'V313 release smoke not proven');
 console.log(result.trim());
}
/* V317 regression: evidence-detail tap area is at least 44px on Safari. */
assert(/#be207Top \.be305-evidence-head button\s*\{[^}]*min-height:44px[^}]*min-width:44px/.test(css),'V317 exhibition detail button 44px target');
console.log('V317_SAFARI_EVIDENCE_TAP_TARGET_PASS');
/* V320: six-boat comparison tab updates must iterate all matching buttons. */
const sixBoatJS=fs.readFileSync('assets/boat_edge_v206_quickview.js','utf8');
assert(sixBoatJS.includes("$$('.be206-switch button',box).forEach"),'V320 all metric buttons update');
assert(sixBoatJS.includes("$$('.be206-layout-switch button',box).forEach"),'V320 all layout buttons update');
assert(!/(^|[^$])\$\('\.be206-switch button',box\)\.forEach/m.test(sixBoatJS),'V320 no single-node iteration');
assert(!/(^|[^$])\$\('\.be206-layout-switch button',box\)\.forEach/m.test(sixBoatJS),'V320 no single-node layout iteration');
console.log('V320_SIX_BOAT_TAB_RENDER_ITERATION_PASS');
console.log('V304_TOPK_STAKES_ODDS_GUARD_MOBILE_SYNTHETIC_PASS');
