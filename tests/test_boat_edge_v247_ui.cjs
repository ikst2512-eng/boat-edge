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
