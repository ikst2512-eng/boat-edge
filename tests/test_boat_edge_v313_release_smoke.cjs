'use strict';
/* BOAT EDGE 03: read-only published bundle contract; no network or results. */
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync('index.html','utf8');
const src=fs.readFileSync('assets/boat_edge_v207_first_prediction.js','utf8');
const matrix=fs.readFileSync('assets/boat_edge_v206_quickview.js','utf8');
const css=fs.readFileSync('assets/boat_edge_v304_topk_mobile.css','utf8');
const tests=[
 ['matrix-js',/boat_edge_v206_quickview\.js\?v=299/],
 ['matrix-css',/boat_edge_v206_quickview\.css\?v=299/],
 ['topk-js',/boat_edge_v207_first_prediction\.js\?v=208&amp;a24=1&amp;ui=306/],
 ['topk-css',/boat_edge_v304_topk_mobile\.css\?v=319/],
 ['safari-nav',/boat_edge_v249_focus\.js\?v=297/]
];
for(const [name,rx] of tests){
 assert(rx.test(html),'missing main asset '+name);
 assert.equal((html.match(new RegExp(rx.source,'g'))||[]).length,1,'duplicate asset '+name);
}
assert(html.indexOf('class="be241-home-shortcuts"')>html.indexOf('<main id="homeView"'));
const window={},document={readyState:'loading',addEventListener(){}};
vm.runInNewContext(src,{window,document,Number,Date,Math,Set,Map,JSON,Intl});
assert.equal(window.BoatEdgeV207.version,'V306-DISPLAY-ONLY');
assert.equal(window.BoatEdgeV207.displayOnly,true);
assert(src.includes('data-be207="ten"'));
assert(src.includes('data-be207="before"'));
assert(src.includes('holdPreviousRace'));
assert(src.includes('BOATERS・競艇日和・オリ展CSVは別出典'));
assert(matrix.includes("V299-UI-ONLY"));
assert(matrix.includes('headTickets'));
assert(css.includes('be306-race-await'));
assert(css.includes('min-height:44px'));
assert(!/(?:fetch\(|XMLHttpRequest|RESULT_UNLOCK_TOKEN)/.test(src));
console.log('V313_MAIN_BUNDLE_UI_READONLY_CONTRACT_PASS');
