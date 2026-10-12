'use strict';
/* BOAT EDGE 03: read-only published bundle contract; no network or results. */
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync('index.html','utf8');
const src=fs.readFileSync('assets/boat_edge_v207_first_prediction.js','utf8');
const matrix=fs.readFileSync('assets/boat_edge_v206_quickview.js','utf8');
const css=fs.readFileSync('assets/boat_edge_v304_topk_mobile.css','utf8');
const tests=[
 ['matrix-js',/boat_edge_v206_quickview\.js\?v=328/],
 ['matrix-css',/boat_edge_v206_quickview\.css\?v=328/],
 ['topk-js',/boat_edge_v207_first_prediction\.js\?v=208&amp;a24=1&amp;ui=306/],
 ['topk-css',/boat_edge_v304_topk_mobile\.css\?v=328/],
 ['safari-nav',/boat_edge_v249_focus\.js\?v=337/]
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

/* V332: published entrypoint must load the race-scoped source panel and preserve render order. */
const sourcePanel=fs.readFileSync('assets/boat_edge_v223_source_visibility.js','utf8');
const sourceAsset='boat_edge_v223_source_visibility.js?v=223&amp;rev=244&amp;patch=250&amp;source=282&amp;fix=329';
assert.equal(html.split(sourceAsset).length-1,1,'V332 source evidence asset must be included exactly once');
assert(html.indexOf('boat_edge_v108.js')<html.indexOf('boat_edge_v206_quickview.js'),'V332 prediction renderer must load before six-boat quickview');
assert(html.indexOf('boat_edge_v206_quickview.js')<html.indexOf('boat_edge_v223_source_visibility.js'),'V332 source evidence panel must load after quickview');
assert(sourcePanel.includes('prior.dataset.raceKey!==key)prior.hidden=true'),'V332 previous race evidence must hide before async fetch');
assert(sourcePanel.includes('node.hidden=false;'),'V332 refreshed evidence must become visible');
assert(sourcePanel.includes('if(node.parentElement!==host)host.prepend(node)'),'V332 source evidence must reparent after rerender');
console.log('V332_PUBLISHED_SOURCE_SCRIPT_ORDER_AND_RACE_GUARD_PASS');

// Track 03 V337: run the selected-race evidence fixture in the existing UI regression gate.
if(fs.existsSync('tests/test_boat_edge_v337_race_scoped_quickview.cjs')){
 require('./test_boat_edge_v337_race_scoped_quickview.cjs');
}
