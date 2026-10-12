'use strict';
/* V306 cross-race display isolation. Pure DOM identity tests, no data access. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const js=fs.readFileSync('assets/boat_edge_v207_first_prediction.js','utf8');
const css=fs.readFileSync('assets/boat_edge_v304_topk_mobile.css','utf8');
const document={readyState:'loading',addEventListener(){}},window={};
vm.runInNewContext(js,{window,document,Number,Date,Math,Set,Map,JSON,Intl},{filename:'v306.js'});
const a=window.BoatEdgeV207;
assert.equal(a.version,'V306-DISPLAY-ONLY');
assert.equal(a.displayOnly,true);
const priorList={id:'prior'},newList={id:'new'};
const prior='20261013-02-05',next='20261013-02-06';
assert.equal(a.holdPreviousRace('',next,null,newList),false,'initial load is allowed');
assert.equal(a.holdPreviousRace(prior,prior,priorList,priorList),false,'same-race refresh is allowed');
assert.equal(a.holdPreviousRace(prior,next,priorList,priorList),true,'old list under new key is held');
assert.equal(a.holdPreviousRace(prior,next,priorList,null),true,'empty new list is held');
assert.equal(a.holdPreviousRace(prior,next,priorList,newList),false,'new list releases hold');
assert(js.includes('if(awaitingRaceList&&sourceList&&sourceList!==lastListNode)awaitingRaceList=false;'));
assert(js.includes("const ticketViewSynced=Boolean(sourceList&&!awaitingRaceList);"));
assert(js.includes("classList.toggle('be306-race-await',!ticketViewSynced)"));
assert(js.includes("classList.remove('be207-ready','be306-race-await')"));
assert(js.includes("!ticketViewSynced||!rowOK"));
assert(js.includes("!ticketViewSynced?'選択した新しいレースの買い目を照合中"));
assert(js.includes("!ticketViewSynced?'配分：新レースの値を照合中"));
assert(js.includes("!ticketViewSynced?'公式オッズ：新レースの証跡を照合中"));
assert(js.includes("ticketViewSynced?stage:'新レースの展開を照合中'"));
assert(js.includes("if(ticketViewSynced)modeButtons(p,modeHost)"));
assert(css.includes('html.be306-race-await #raceView #be108PredictionModes{display:none!important}'));
assert(!/(?:fetch\(|XMLHttpRequest|rankPredictions\(|RESULT_UNLOCK_TOKEN|winning_combo|official_payout)/.test(js));
if(fs.existsSync('index.html')){
 const html=fs.readFileSync('index.html','utf8');
 assert(html.includes('boat_edge_v207_first_prediction.js?v=208&amp;a24=1&amp;ui=306'));
 assert(html.includes('boat_edge_v304_topk_mobile.css?v=328'));
}
console.log('V306_RACE_SWITCH_STALE_TICKETS_SUPPRESSED_PASS');
