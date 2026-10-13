'use strict';
/* V371 CSS-only presentation contract. No actual races, network or results. */
const assert=require('node:assert/strict'),fs=require('node:fs'),test=require('node:test');
const css=fs.readFileSync('assets/boat_edge_v371_simple_ui.css','utf8');
const index=fs.readFileSync('index.html','utf8');
const js=fs.readFileSync('assets/boat_edge_v206_quickview.js','utf8');
test('V371 style is loaded after all earlier CSS without deleting source or predictor code',()=>{
 const newer='boat_edge_v371_simple_ui.css?v=371';
 const old='boat_edge_v304_topk_mobile.css?v=328&amp;layout=338';
 assert.equal(index.split(newer).length-1,1);
 assert(index.indexOf(old)>0&&index.indexOf(newer)>index.indexOf(old));
 assert(css.includes('#homeView:has(#be108Hub .be108-shell)'),'legacy home is hidden only after race hub mounts');
 assert(css.includes('#homeView #be108Hub .be108-venue-grid'));
 assert(css.includes('#raceView #raceTabs'));
 assert(css.includes('#raceView #be207Top .be207-ticket'));
 assert(css.includes('#raceView #be206Quick .be206-table'));
 assert(css.includes('be208-details-on'),'source explanation still available in detailed view');
});
test('V371 six-lane rows have a full-width accessible 44px mobile control',()=>{
 assert(js.includes("const preferredLayout=()=>window.matchMedia?.('(max-width: 650px)')?.matches?'rows':'lanes'"));
 assert(js.includes('layout=preferredLayout()'));
 assert(js.includes('if(raceChanged)layout=preferredLayout()'));
 assert(/#raceView #be206Quick \.be206-layout-switch button\{min-height:44px\}/.test(css));
 assert(/#raceView #be206Quick \[data-be206-head-close\]\{min-height:44px;min-width:44px\}/.test(css));
 assert(/@media\(max-width:760px\)/.test(css));
 assert(/@media\(max-width:360px\)/.test(css));
});
test('V371 never suppresses scratch stops, selected-race guard, stakes or authenticated hit checks',()=>{
 for(const critical of ['.be207-condition','.be207-budget','.be207-odds','.be207-explain']){
  assert(css.includes(critical),'critical visible selector missing: '+critical);
 }
 for(const forbidden of ['#be251Outcome{display:none','#be207Top .be207-condition{display:none','#raceView #be206Quick .be206-headpanel{display:none']){
  assert(!css.includes(forbidden),'blocked/verified user information hidden');
 }
 assert(index.includes('boat_edge_v241_home.js'));
 assert(index.includes('boat_edge_v251_race_result.js'));
});
console.log('V371_SIMPLE_RACE_FIRST_UI_CONTRACT_PASS');
