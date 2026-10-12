'use strict';
/* V322 UI-only race evidence host reparent; no actual network or result reads. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const src=fs.readFileSync('assets/boat_edge_v223_source_visibility.js','utf8');
class Clock extends Date {static now(){return Date.parse('2026-10-13T08:25:00+09:00');}}
const key='20261013-23-01';
const race={race_key:key,meta:{phase:'PRE_RESULT',deadline:'08:35',results_seen:false,unlock:false,scoring:false},source_audit:{}};
const fields=new Map();
const field=k=>{if(!fields.has(k))fields.set(k,{dataset:{},textContent:'',replaceChildren(){this.items=[];},append(...items){this.items=(this.items||[]).concat(items);}});return fields.get(k);};
const node={id:'be223Source',dataset:{raceKey:'20261013-01-01'},hidden:false,open:true,querySelector:field};
let moved=0;
const host={contains(x){return moved>0&&x===node;},prepend(x){assert.equal(x,node);moved++;}};
const doc={readyState:'loading',visibilityState:'visible',addEventListener(){},
 querySelector(k){if(k==='#raceView.active')return {};
  if(k==='#raceView .race-summary')return host;
  if(k==='#be223Source')return node;return null;},
 createElement(){return {dataset:{},className:'',textContent:'',append(){}};}};
const win={};
vm.runInNewContext(src,{window:win,document:doc,state:{race},fetch:async()=>({ok:false}),Date:Clock,Promise,console,setTimeout(){},setInterval(){}},{filename:'v322.js'});
const pending=win.BoatEdgeV223Source.refresh();
assert.equal(node.hidden,true,'old race receipt hidden before fetch completes');
pending.then(()=>{
 assert.equal(moved,1,'evidence panel reattached into active summary');
 assert.equal(node.dataset.raceKey,key,'evidence now scoped to selected race');
 assert.match(field('.be223-state').textContent,/締切/,'new race receipt has selected-race inspection summary');
 assert.equal(node.hidden,false,'only the refreshed panel is revealed');
 assert.equal(node.open,false,'race change resets details expansion');
 console.log('V322_RACE_EVIDENCE_REPARENT_FAIL_CLOSED_PASS');
}).catch(e=>{console.error(e);process.exitCode=1;});
