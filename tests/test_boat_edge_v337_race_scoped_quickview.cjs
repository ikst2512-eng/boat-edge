'use strict';
/* V337: synthetic DOM only. No live network, result, stake or race fetches. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const js=fs.readFileSync('assets/boat_edge_v249_focus.js','utf8');
const html=fs.readFileSync('index.html','utf8');
const css=fs.readFileSync('assets/boat_edge_v249_focus.css','utf8');
assert.equal((html.match(/boat_edge_v249_focus\.js\?v=337/g)||[]).length,1);
assert.equal((html.match(/boat_edge_v249_focus\.css\?v=337/g)||[]).length,1);
assert(!/\bfetch\s*\(/.test(js),'quick nav may not fetch');
assert(!/innerHTML\s*=\s*.*textContent/.test(js),'receipt must be text-only');
const key='20261013-01-01',next='20261013-02-01';
const evidence={dataset:{},children:[],replaceChildren(){this.children=[]},appendChild(x){this.children.push(x)}};
const node={querySelector:s=>s==='.be249-evidence'?evidence:null};
const root={querySelector:s=>s==='.be181-freeze-banner'?{dataset:{be181Source:'final'}}:null};
const chip=(value,quality)=>({textContent:value,dataset:{quality}});
let currentReceipt=null;
const nodes={
 '#raceView .race-summary':{},
 '#raceTitle':{},
 '#be249Focus':node,
 '#raceView':root
};
const doc={
 readyState:'loading',
 querySelector(s){return s==='#be223Source'?currentReceipt:(nodes[s]||null)},
 createElement(){return {dataset:{},textContent:''}},
 addEventListener(){}
};
const state={race:{race_key:key}};
const window={};
vm.runInNewContext(js,{document:doc,window,state,JSON,String},{filename:'v337'});
window.BoatEdgeV249.refresh();
assert.equal(evidence.children.length,6);
assert(evidence.children.every(x=>x.dataset.kind==='unknown'));
assert.match(evidence.children[3].textContent,/未取得・未確認/);
const aud={
 '[data-be223-flag="scratch"]':chip('欠場・取消：取消信号なし','limited'),
 '[data-be223-ex="time"]':chip('展示タイム：08:20取得','ok'),
 '[data-be223-flag="odds"]':chip('3連単オッズ：08:22取得','ok'),
 '[data-be223-ex="boaters"]':chip('BOATERSオリ展：未取得','unknown'),
 '[data-be223-ex="biyori"]':chip('競艇日和オリ展：未取得','unknown')
};
currentReceipt={dataset:{raceKey:key},hidden:false,querySelector:s=>aud[s]||null};
window.BoatEdgeV249.refresh();
assert.match(evidence.children[0].textContent,/FINAL固定/);
assert.equal(evidence.children[2].dataset.kind,'verified');
assert.equal(evidence.children[3].dataset.kind,'verified');
assert.equal(evidence.children[4].dataset.kind,'unknown');
state.race.race_key=next;
window.BoatEdgeV249.refresh();
assert(evidence.children.every(x=>x.dataset.kind==='unknown'),'previous race evidence must never transfer');
assert.match(evidence.children[3].textContent,/未取得・未確認/);
currentReceipt.dataset.raceKey=next;
aud['[data-be223-flag="odds"]']=chip('3連単オッズ：古い','stale');
aud['[data-be223-flag="scratch"]']=chip('欠場・取消：停止','stop');
window.BoatEdgeV249.refresh();
assert.equal(evidence.children[1].dataset.kind,'stop');
assert.equal(evidence.children[3].dataset.kind,'stale');
currentReceipt.hidden=true;
window.BoatEdgeV249.refresh();
assert(evidence.children.every(x=>x.dataset.kind==='unknown'),'hidden receipt cannot certify');
assert(css.includes('data-kind="stop"'));
console.log('V337 RACE-SCOPED QUICK EVIDENCE PASS');
