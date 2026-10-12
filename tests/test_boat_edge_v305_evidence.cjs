'use strict';
/* V305: source-only race-scoped pre-result exhibition badges. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const src=fs.readFileSync('assets/boat_edge_v207_first_prediction.js','utf8');
const css=fs.readFileSync('assets/boat_edge_v304_topk_mobile.css','utf8');
const key='20261013-02-05';
const flags={
 time:{dataset:{quality:'ok'},textContent:'展示タイム：03:14取得'},
 original:{dataset:{quality:'stale'},textContent:'オリ展：古い 03:01'},
 boaters:{dataset:{quality:'unknown'},textContent:'BOATERSオリ展：未取得（独立照合なし）'},
 biyori:{dataset:{quality:'unknown'},textContent:'競艇日和オリ展：未取得（独立照合なし）'}
};
const panel={dataset:{raceKey:key},querySelector(s){
 const m=s.match(/^\[data-be223-ex="(time|original|boaters|biyori)"\]$/);
 return m?flags[m[1]]:null;
}};
const document={readyState:'loading',addEventListener(){},
 querySelector(s){return s==='#be223Source'?panel:null;}};
const window={};
vm.runInNewContext(src,{window,document,Number,Date,Math,Set,Map,JSON,Intl},{filename:'v305-exhibition.js'});
const a=window.BoatEdgeV207;
assert.equal(a.version,'V306-DISPLAY-ONLY');
const matched=a.evidenceFor(key);
assert.equal(matched.ready,true);
assert.equal(matched.items.length,4);
assert.equal(matched.items[0].label,'展示タイム');
assert.equal(matched.items[0].quality,'ok');
assert.equal(matched.items[1].quality,'stale');
assert.equal(matched.items[2].quality,'unknown');
assert.equal(matched.items[3].quality,'unknown');
assert(matched.items[2].text.includes('未取得'));
assert(!matched.items[2].text.includes('取得済み'));
assert.equal(a.evidenceFor('20261013-03-05').ready,false,'previous race evidence must not leak');
panel.dataset.raceKey='20261013-01-01';
assert.equal(a.evidenceFor(key).ready,false,'stale panel never certifies current race');
panel.dataset.raceKey=key;
delete flags.original.dataset.quality;
assert.equal(a.evidenceFor(key).items[1].quality,'unknown','missing proof is unknown');
flags.original.dataset.quality='unrecognised';
assert.equal(a.evidenceFor(key).items[1].quality,'unknown','unknown provider quality must not be upgraded');
assert(src.includes('data-be207="before"'));
assert(src.includes('data-tab="before"'));
assert(src.includes('BOATERS・競艇日和・オリ展CSVは別出典'));
assert(css.includes('.be305-evidence-items'));
assert(css.includes('[data-quality="ok"]'));
assert(!/(?:fetch\(|XMLHttpRequest|rankPredictions\(|RESULT_UNLOCK_TOKEN|winning_combo|official_payout)/.test(src));
if(fs.existsSync('index.html')){
 const html=fs.readFileSync('index.html','utf8');
 assert(html.includes('boat_edge_v304_topk_mobile.css?v=328'));
 assert(html.includes('boat_edge_v207_first_prediction.js?v=208&amp;a24=1&amp;ui=306'));
}
console.log('V305_RACE_SCOPED_EXHIBITION_PROVENANCE_FAIL_CLOSED_PASS');
