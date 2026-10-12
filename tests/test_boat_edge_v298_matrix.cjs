'use strict';
/* V298: synthetic UI-only / 6艇横比較. Never reads formal, results or network. */
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const js=fs.readFileSync('assets/boat_edge_v206_quickview.js','utf8');
const css=fs.readFileSync('assets/boat_edge_v206_quickview.css','utf8');
const window={},document={readyState:'loading',addEventListener(){}};
vm.runInNewContext(js,{window,document,Date,Number,Math,Map,Set,JSON,queueMicrotask(){},setInterval(){},
 console:{warn(){}}},{filename:'boat_edge_v206_quickview.js'});
const api=window.BoatEdgeV206;
assert.equal(api.version,'V299-UI-ONLY');
assert.equal(api.displayOnly,true);
/* V338: a tap can only reveal a mounted, visible panel for the same selected race. */
const proofKey='20261013-02-05',pane={isConnected:true,hidden:false};
assert.equal(api.canRevealHead(proofKey,proofKey,2,2,pane),true);
assert.equal(api.canRevealHead(proofKey,'20261013-03-05',2,2,pane),false,'never jump to previous race');
assert.equal(api.canRevealHead(proofKey,proofKey,2,3,pane),false,'selection changed');
assert.equal(api.canRevealHead(proofKey,proofKey,2,2,{isConnected:true,hidden:true}),false,'hidden panel');
assert.equal(api.canRevealHead(proofKey,proofKey,2,2,{isConnected:false,hidden:false}),false,'detached panel');
assert.equal(api.canRevealHead('bad-race',proofKey,2,2,pane),false,'invalid key');
assert(js.includes('selectedLane=opening?lane:null'),'second tap must close selected racer');
assert(js.includes('panel.scrollIntoView?.'),'explicit tap reveals the head panel');
assert(js.includes("panel.focus?.({preventScroll:true})"),'keyboard and screen-reader focus');
assert(js.includes('選手名をタップすると'),'display clear selection instruction');

for(const label of ['基本','連対・機力','直前・展示','オリ展','展示タイム','展示進入','1周','まわり足','直線']){
 assert(js.includes(label),'missing sourced comparison field: '+label);
}
const rows=Array.from({length:6},(_,i)=>({
 lane:i+1,name:'選手'+(i+1),grade:'A1',
 national:{win_rate:[7.2,6.1,5.2,4.9,4.8,4.6][i],quinella_rate:50,trio_rate:60},
 local:{win_rate:5,quinella_rate:40},motor:{quinella_rate:30},
 time:6.8+i/10,st:.15+i/100,course:i+1,avg:.14+i/100,
 lap:36+i/10,turn:5.1+i/10,straight:7+i/10,f:false
}));
const before=JSON.stringify(rows);
const matrix=api.matrix(rows);
assert.equal((matrix.match(/data-be206-lane="[1-6]"/g)||[]).length,6);
assert(matrix.includes('比較項目'));
assert(matrix.indexOf('data-be206-lane="1"')<matrix.indexOf('data-be206-lane="6"'));
assert.equal(api.best(rows,'national.win_rate',.4,false),7.2);
assert.equal(api.best(rows,'course',1,false),null);
assert.equal(api.best(rows.slice(0,5),'national.win_rate',.4,false),null);
assert.equal(api.best([...rows.slice(1),rows[1]],'national.win_rate',.4,false),null);
const missing=JSON.parse(before);missing[5].national.win_rate=null;
assert.equal(api.best(missing,'national.win_rate',.4,false),null);
const ties=JSON.parse(before);ties[1].national.win_rate=7.0;
assert.equal(api.best(ties,'national.win_rate',.4,false),null);
const foul=JSON.parse(before);foul[2].f=true;
assert.equal(api.best(foul,'st',.03,true),null);
const html=api.matrix(rows.map((x,i)=>i===0?{...x,name:'<img src=x onerror=alert(1)>'}:x));
assert(!html.includes('<img'));assert(html.includes('&lt;img'));
assert.equal(JSON.stringify(rows),before);
assert(css.includes('.be206-matrix-scroll'));
assert(css.includes('overflow-x:auto'));
assert(css.includes('position:sticky'));
assert(css.includes('[hidden]'));
assert(js.includes("layout='lanes'"));
assert(js.includes('data-be206-layout="rows"'));
assert(!/(?:fetch\(|XMLHttpRequest|RESULT_UNLOCK_TOKEN|rankPredictions\(|loadRace\(|winning_combo|official_payout)/.test(js));
if(fs.existsSync('index.html')){
 const index=fs.readFileSync('index.html','utf8');
 assert(index.includes('boat_edge_v206_quickview.js?v=328'));
 assert(index.includes('boat_edge_v206_quickview.css?v=328'));
}
console.log('V298_SIX_LANE_MATRIX_STRICT_HIGHLIGHT_SYNTHETIC_PASS');

/* V328 race transition must hide prior tickets and head picks until a new list mounts. */
assert(js.includes('awaitingTicketList'),'V328 race transition must track pending list');
assert(js.includes("list!==lastTicketList"),'V328 must require a fresh list node');
assert(js.includes("!awaitingTicketList"),'V328 must block stale head picks');

// Keep the new display regression in the existing V307 UI gate; no workflow edits.
require('./test_boat_edge_v341_comparison_scroll.cjs');

