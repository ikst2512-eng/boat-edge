'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('assets/boat_edge_v204_prediction.js','utf8');
const listeners={};
const document={readyState:'loading',addEventListener(name,fn){listeners[name]=fn;}};
const window={};
vm.runInNewContext(source,{window,document,console,Date,queueMicrotask(){},setInterval(){}});
const x=window.BoatEdgeV204;
assert.ok(x&&typeof x.topKExplanation==='function');
const rows=['1-2-3','1-3-2','2-1-3','2-3-1','3-1-2','3-2-1','1-2-4','1-4-2','2-1-4','2-4-1'].map(combo=>({
  querySelector(sel){return sel==='b'?{textContent:combo}:null;}
}));
const before=x.topKExplanation(rows);
assert.match(before.caution,/p_raw_percent/);
assert.match(before.caution,/相対重み/);
assert.match(before.caution,/120通り/);
assert.match(before.caution,/的中確率：未校正/);
assert.match(before.caution,/Top3\/5\/10/);
assert.match(before.top3,/1-2-3/);
assert.match(before.top10,/2-4-1/);
assert.match(before.head,/1号艇/);
const html=fs.readFileSync('index.html','utf8');
assert.match(html,/boat_edge_v204_prediction\.js\?v=204&amp;rev=244&amp;patch=247&amp;patch2=248&amp;patch3=250&amp;weights=279/);
assert.equal((html.match(/boat_edge_v204_prediction\.js/g)||[]).length,1);
console.log('V279_RELATIVE_WEIGHTS_DISPLAY_ONLY_PASS');
