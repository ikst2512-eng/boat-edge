'use strict';
/* A23: deterministic six-racer source-only presentation regression. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const raw=fs.readFileSync('assets/boat_edge_v203_readable.js','utf8');
const ctx={
 window:{},
 document:{readyState:'loading',addEventListener(){}},
 Date,Number,Math,Map,Set,JSON,
 setInterval(){throw Error('no timers allowed during isolated render test')},
 fetch(){throw Error('no network expected')}
};
vm.runInNewContext(raw,ctx,{filename:'boat_edge_v203_readable.js'});
const api=ctx.window.BoatEdgeV203;
assert.equal(typeof api.quickSix,'function');
assert.equal(typeof api.strongest,'function');
const rows=[
 {lane:1,national:{win_rate:5.6},local:{win_rate:6.8},motor:{quinella_rate:45}},
 {lane:2,national:{win_rate:6.0},local:{win_rate:5.6},motor:{quinella_rate:53}},
 {lane:3,national:{win_rate:4.8},local:{win_rate:5.3},motor:{quinella_rate:39}},
 {lane:4,national:{win_rate:5.2},local:{win_rate:5.0},motor:{quinella_rate:37}},
 {lane:5,national:{win_rate:4.6},local:{win_rate:4.9},motor:{quinella_rate:41}},
 {lane:6,national:{win_rate:5.4},local:{win_rate:4.8},motor:{quinella_rate:38}}
];
const copy=JSON.stringify(rows);
const local=api.strongest(rows,x=>x.local.win_rate,.3);
const motor=api.strongest(rows,x=>x.motor.quinella_rate,3);
assert.equal(local,6.8);
assert.equal(motor,53);
const out=api.quickSix(rows,local,motor);
assert.equal((out.match(/data-be258-lane="[1-6]"/g)||[]).length,6);
for(let i=1;i<=6;i++)assert(out.includes('data-be258-lane="'+i+'"'));
assert(out.indexOf('data-be258-lane="1"')<out.indexOf('data-be258-lane="6"'));
assert.match(out,/全国勝率/);
assert.match(out,/当地勝率/);
assert.match(out,/モーター2連/);
assert.equal((out.match(/class=" be203-red"/g)||[]).length,2,'only two complete unique standout metrics');
assert.equal(JSON.stringify(rows),copy,'display must not alter any racer data');
assert.equal(api.quickSix(rows.slice(0,5),local,motor),'','no falsely labeled six-boat summary');
assert.equal(api.quickSix([...rows.slice(0,5),rows[0]],local,motor),'','duplicate lane prohibited');
const missing=JSON.parse(copy);missing[1].motor.quinella_rate=null;
const safeMotor=api.strongest(missing,x=>x.motor.quinella_rate,3);
assert.equal(safeMotor,null,'six-of-six source requirement');
const safe=api.quickSix(missing,local,safeMotor);
assert(safe.includes('－</strong>'),'missing motor is unknown, not a zero or zero percent');
assert(!safe.includes('－%</strong>'));
assert.equal((safe.match(/class=" be203-red"/g)||[]).length,1);
const css=fs.readFileSync('assets/boat_edge_v203_readable.css','utf8');
const html=fs.readFileSync('index.html','utf8');
assert(css.includes('BOAT_EDGE_A23_SIX_RACER_COMPARE_20261012'));
assert(css.includes('grid-template-columns:repeat(3,minmax(0,1fr))'));
assert(html.includes('boat_edge_v203_readable.css?v=203&amp;rev=244&amp;patch=247&amp;patch2=250&amp;a23=1'));
console.log('A23_SIX_RACER_SOURCE_ONLY_PASS: six sorted boats, six-of-six highlights, missing values, no model edits');
