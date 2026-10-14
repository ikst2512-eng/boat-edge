'use strict';
/* V247 UI-only source-binding tests; no network or formal results. */
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const racer=fs.readFileSync('assets/boat_edge_v203_readable.js','utf8');
const prediction=fs.readFileSync('assets/boat_edge_v204_prediction.js','utf8');
function getJsApi(code){
 const window={};
 const document={readyState:'loading',addEventListener(){},querySelector(){return null},querySelectorAll(){return []}};
 vm.runInNewContext(code,{window,document,console,setInterval(){},setTimeout(){},queueMicrotask(){},Date});
 return window;
}
const source=getJsApi(racer).BoatEdgeV203;
assert.equal(typeof source.getRows,'function');
assert.match(racer,/scratchError='',fullStats=true,fullTable=false/);
assert.match(racer,/fullStats=true;fullTable=false;fetchScratch/);
assert.match(racer,/B2連/);assert.match(racer,/B3連/);
assert.match(racer,/全国2連/);assert.match(racer,/当地3連/);
assert.match(racer,/M2連/);assert.match(racer,/M3連/);
function fakeElement(fields){
 return {querySelector(selector){return (fields&&fields[selector])||null},querySelectorAll(selector){return (fields&&fields[selector])||[]}};
}
function fakeBoat(n,name,role){return fakeElement({'.n':{textContent:String(n)},'.r':{textContent:name},'.a':{textContent:role}})}
const steps=[
 fakeElement({'.flow-boat.attack,.flow-boat.hot':[fakeBoat(4,'攻め艇','スタート注意')]}),
 fakeElement({'.flow-boat.attack,.flow-boat.hot':[fakeBoat(1,'内艇','イン'),fakeBoat(4,'攻め艇','攻め')]}),
 fakeElement({'.flow-boat.attack,.flow-boat.hot':[fakeBoat(5,'展開艇','外側の受益')]})
];
const flow=fakeElement({'.flow-step':steps,'.flow-conclusion .v':{textContent:'既存の結論だけ表示'}});
const window={};
const document={readyState:'loading',addEventListener(){},querySelector(s){return s==='#scenarioFlow'?flow:null},querySelectorAll(){return []}};
vm.runInNewContext(prediction,{window,document,console,Date,queueMicrotask(){}});
const stage=window.BoatEdgeV204.flowStages();
assert.equal(stage.length,4);
assert.match(stage[0].value,/4号艇/);
assert.match(stage[1].value,/攻め艇/);
assert.match(stage[2].value,/5号艇/);
assert.equal(stage[3].value,'既存の結論だけ表示');
assert(!stage.some(x=>/\d+(?:\.\d+)?%/.test(x.value)));
const keys=['results.html','assets/boat_edge_v241_results.js','assets/boat_edge_v241_results.css'];
const worker=fs.readFileSync('.github/workflows/v241.yml','utf8');
for(const path of keys)assert(worker.includes("'"+path+"'"));
assert(worker.includes('V241_EXISTING_RESOURCE_MODIFIED_FAIL_CLOSED_'));
/* T02 regression: legacy V241 scheduled package must not clobber V360's
 * source-verified home 🎯 renderer; bundled scorer/tests remain strict. */
const allowStart=worker.indexOf("if name in ('index.html'");
const allowEnd=worker.indexOf(":\n                          print('V241_PRESERVE_INDEPENDENTLY_UPDATED_PUBLIC_UI'",allowStart);
assert(allowStart>=0&&allowEnd>allowStart,'V241 explicit public UI exemption must exist');
const allow=worker.slice(allowStart,allowEnd);
assert(allow.includes("'assets/boat_edge_v241_home.js'"),'current verified home UI must be preserved');
assert(worker.includes('V241_PUBLIC_HOME_JS_MISSING_NO_LEGACY_REINSTALL'),'missing current JS must not install stale V241 copy');
for(const sensitive of ['scripts/boat_edge_v241_results.py','scripts/boat_edge_v241_patch_home.py',
                        'tests/test_boat_edge_v241_results.py'])
  assert(!allow.includes("'"+sensitive+"'"),'scorer and source-bound regression code must remain fail-closed');
assert(worker.includes("raise SystemExit('V241_PACKAGED_BYTES_INVALID_'+name)"));
assert(worker.includes("raise SystemExit('V241_EXISTING_RESOURCE_MODIFIED_FAIL_CLOSED_'+name)"));
console.log('V241_LEGACY_PACKAGED_UI_PRESERVE_SCORER_FAIL_CLOSED_PASS');
const resultJs=fs.readFileSync('assets/boat_edge_v241_results.js','utf8');
assert(resultJs.includes('!o.rows.every(verifiedRow)'));
assert(resultJs.includes("data-verification"));
const resultHtml=fs.readFileSync('results.html','utf8');
for(const word of ['検証済み的中','検証済み不的中','結果待ち','検証対象外'])assert(resultHtml.includes(word));
assert(!resultJs.includes('data/formal_'));
const nav=fs.readFileSync('assets/boat_edge_v166_refresh.js','utf8');
assert(nav.includes("b.textContent='↻ 更新'"));
assert(nav.includes("aria-label','現在のページのデータを更新"));
assert(nav.includes('window.BoatEdgeV166Refresh={refresh}'));
console.log('V247_FLOW_SIX_RACERS_VERIFIED_RESULTS_NAV_TESTS_PASS');
// V357: ensure five new fail-closed racer-card fixtures run in the existing V307 UI CI step.
require('./test_boat_edge_v357_card_source_integrity.cjs');
// V360: run verified-home-indicator regressions in the existing read-only UI CI.
require('./test_boat_edge_v360_home_result_safety.cjs');
// V361: enforce list-side result proof and official-link safety in V307 UI CI.
require('./test_boat_edge_v361_results_list_integrity.cjs');

// 03: selected mobile race content precedes lengthy GLOBAL operations proof.
// The health warning and its verification link must remain visible/accesssible.
const mobileRaceCss=fs.readFileSync('assets/boat_edge_v371_simple_ui.css','utf8');
const opsCss=mobileRaceCss.slice(mobileRaceCss.indexOf('/* 03 mobile race-first:'));
assert(opsCss.includes('body.be48-race-active #be220Ops #be259OpsProof'));
assert(opsCss.includes('body.be48-race-active #be220Ops #be220Info'));
assert(opsCss.includes('display:none!important'));
assert(opsCss.includes('#be220Ops #be220Status'));
assert(opsCss.includes('#be220Ops .be220-line a'));
assert(opsCss.includes('min-height:44px'));
assert(!opsCss.includes('body.be48-race-active #be220Ops{display:none'));
const opsJs=fs.readFileSync('assets/boat_edge_v220_site_ops.js','utf8');
assert(opsJs.includes('id="be220Status"'));
assert(opsJs.includes('aria-label="AI仮想運用と未見検証を見る"'));
console.log('BOAT_EDGE_03_MOBILE_RACE_FIRST_OPS_STATUS_PRESERVED_PASS');

// 03: data missing on a six-racer preview is not a measured 0.0%.
// Execute the production renderer, not a duplicate rate-format implementation.
const sixBoatSrc=fs.readFileSync('assets/boat_edge_final_v48.js','utf8');
const sixStart=sixBoatSrc.indexOf('function renderRacers(d){');
const sixEnd=sixBoatSrc.indexOf('function beforeMaps(d)',sixStart);
assert(sixStart>=0&&sixEnd>sixStart,'production six-boat renderer must be present');
const sixHost={innerHTML:''};
const sixCtx=vm.createContext({
  q:sel=>sel==='#be48Racers'?sixHost:null,
  lane:l=>'['+l+']',
  laneNo:(r,i)=>Number(r?.lane??i+1),
  value:v=>v===null||v===undefined||v===''?'—':v,
  esc:v=>String(v)
});
vm.runInContext(sixBoatSrc.slice(sixStart,sixEnd),sixCtx);
sixCtx.rows=[
 {lane:1,name:'Missing Both',motor:{quinella_rate:null},boat:{quinella_rate:''}},
 {lane:2,name:'Missing Motor',motor:{},boat:{quinella_rate:35.26}},
 {lane:3,name:'Measured Zero',motor:{quinella_rate:0},boat:{quinella_rate:0}},
 {lane:4,name:'No Motor/Boat',motor:null,boat:undefined},
 {lane:5,name:'Garbage',motor:{quinella_rate:'unknown'},boat:{quinella_rate:'NaN'}},
 {lane:6,name:'Standard',motor:{quinella_rate:27.75},boat:{quinella_rate:42.12}}
];
vm.runInContext('renderRacers({racers:rows})',sixCtx);
for(const textValue of ['Missing Both','Missing Motor','Measured Zero','No Motor/Boat','Garbage','Standard'])
 assert(sixHost.innerHTML.includes(textValue));
const sixCards=sixHost.innerHTML.match(/<article class="be48-racer">[\s\S]*?<\/article>/g)||[];
assert.equal(sixCards.length,6);
assert(sixCards[0].includes('M2<b>—</b>')&&sixCards[0].includes('B2<b>—</b>'));
assert(sixCards[1].includes('M2<b>—</b>')&&sixCards[1].includes('B2<b>35.3%</b>'));
assert(sixCards[2].includes('M2<b>0.0%</b>')&&sixCards[2].includes('B2<b>0.0%</b>'));
assert(sixCards[3].includes('M2<b>—</b>')&&sixCards[3].includes('B2<b>—</b>'));
assert(sixCards[4].includes('M2<b>—</b>')&&sixCards[4].includes('B2<b>—</b>'));
assert(sixCards[5].includes('M2<b>27.8%</b>')&&sixCards[5].includes('B2<b>42.1%</b>'));
console.log('BOAT_EDGE_03_SIX_BOAT_MISSING_RATE_NOT_ZERO_PASS');
