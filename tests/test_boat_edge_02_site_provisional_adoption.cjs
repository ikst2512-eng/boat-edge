'use strict';
// Pure no-network parity: the future-facing default mode must reproduce the
// exact V254 PRE_RESULT 10-ticket policy. Historical snapshots are not edited.
const fs=require('node:fs');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const src=fs.readFileSync('assets/boat_edge_v108.js','utf8');
const start=src.indexOf('function be254SelectedThirdTail10(');
const end=src.indexOf('function be122ModesFromTickets(',start);
assert(start>=0&&end>start,'V254 client selector missing');
const candidate=vm.runInNewContext(src.slice(start,end)+'\nbe254SelectedThirdTail10');
const hit=['1-2-3','1-2-4','1-3-2','1-4-2','2-1-3','2-3-1','3-1-2','1-3-4','1-4-3','3-2-1'];
const hole=['2-1-4','2-3-4','3-1-4','1-2-5','1-2-6','1-3-5','1-4-5','3-2-4','3-4-1','2-4-1',...hit];
const rows=a=>a.map((combo,i)=>({combo,p:20-i}));
const actual=candidate(rows(hit),rows(hole));
assert(actual&&actual.length===10);
const seen=new Set(hit),pairs=new Set(hit.slice(0,7).map(x=>x.slice(0,3)));
let expected=hit.slice(0,7);
for(const c of [...hole.filter(c=>!seen.has(c)&&pairs.has(c.slice(0,3))),...hit.slice(7)]){
 if(!expected.includes(c))expected.push(c);
 if(expected.length===10)break;
}
assert.deepEqual(Array.from(actual,x=>x.combo),expected);
assert.deepEqual(Array.from(actual.slice(0,7),x=>x.combo),hit.slice(0,7));
assert(new Set(actual.map(x=>x.combo)).size===10);
assert.equal(candidate(rows(hit),rows(hit.slice(0,9))),null);
assert.equal(candidate(rows([...hit.slice(0,9),hit[0]]),rows(hole)),null);
assert.equal(candidate(rows(hit),rows([...hole.slice(0,9),'1-2-3','1-2-3'])),null);
assert(src.includes("effectiveSnap?.default_display_mode==='tail'"));
assert(src.includes("mode==='tail'&&!selectedTail"));
assert(src.includes("if(previous!==null && previous!==undefined)return previous"));
assert(src.includes("writeLocal(perRaceModeKey,b.dataset.be108Mode)"));
console.log('V254_SITE_FORWARD_DEFAULT_PARITY_NO_RETROFIT_PASS');
