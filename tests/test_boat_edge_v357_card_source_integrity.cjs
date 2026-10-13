'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const source=fs.readFileSync(path.join(__dirname,'..','assets/boat_edge_v203_readable.js'),'utf8');
const window={},document={readyState:'loading',addEventListener(){}};
vm.runInNewContext(source,{window,document,Date,Number,Math,Map,Set,JSON},{filename:'boat_edge_v203_readable.js'});
const api=window.BoatEdgeV203;
const sha='a'.repeat(64),stamp='2026-10-13T10:30:00+09:00';
const audit=(status='ok')=>({status,fetched_at:stamp,sha256:sha});
function data(){
 return {
  race_key:'20261013-06-01',
  racers:Array.from({length:6},(_,i)=>({lane:i+1,name:'艇'+(i+1),national:{win_rate:5.5}})),
  source_audit:{beforeinfo:audit(),original_exhibition:audit(),stt:audit()},
  beforeinfo:{
   racers:Array.from({length:6},(_,i)=>({lane:i+1,exhibition_time:6.5+i*0.01})),
   start_exhibition:Array.from({length:6},(_,i)=>({lane:i+1,course:i+1,st:0.10+i*0.01}))
  },
  original_exhibition:{labels:['一周','まわり足','直線'],boats:Array.from({length:6},(_,i)=>({lane:i+1,values:[37+i*0.1,5+i*0.1,8+i*0.1]}))},
  actual_entry:Array.from({length:6},(_,i)=>({lane:i+1,course:i+1,exhibition_st_raw:0.10+i*0.01}))
 };
}
test('V357 duplicate start lane cannot silently overwrite ST or course in racer cards',()=>{
 const r=data();
 r.beforeinfo.start_exhibition.push({lane:1,course:6,st:0.44});
 const rows=api.getRows(r);
 assert.equal(rows[0].st,null);
 assert.equal(rows[0].course,null);
 assert.equal(rows[1].course,2);
 assert.equal(rows[1].st,0.11);
});
test('V357 repeated course position among distinct boats is not presented as verified',()=>{
 const r=data();r.beforeinfo.start_exhibition[1].course=1;
 const rows=api.getRows(r);
 assert.equal(rows[0].course,null);
 assert.equal(rows[1].course,null);
 assert.equal(rows[2].course,3);
 assert.equal(rows[0].st,0.10);
});
test('V357 duplicated official and original exhibition source lanes are missing on conflict',()=>{
 const r=data();
 r.beforeinfo.racers.push({lane:1,exhibition_time:6.11});
 r.original_exhibition.boats.push({lane:1,values:[35,4,7]});
 const rows=api.getRows(r);
 assert.equal(rows[0].time,null);
 assert.equal(rows[0].lap,null);
 assert.equal(rows[0].turn,null);
 assert.equal(rows[1].lap,37.1);
 assert.equal(rows[1].time,6.51);
});
test('V357 STT fallback rejects ambiguous duplicate actual-entry lanes',()=>{
 const r=data();
 r.source_audit.beforeinfo=audit('missing');
 r.actual_entry.push({lane:1,course:6,exhibition_st_raw:0.01});
 const rows=api.getRows(r);
 assert.equal(rows[0].st,null);
 assert.equal(rows[0].course,null);
 assert.equal(rows[1].st,0.11);
});
test('V357 invalid course and booleans stay missing while measured zero remains valid',()=>{
 const r=data();
 r.beforeinfo.start_exhibition[0].course=2.5;
 r.beforeinfo.start_exhibition[1].st=false;
 r.beforeinfo.racers[2].exhibition_time=[];
 r.beforeinfo.start_exhibition[3].st=0;
 const rows=api.getRows(r);
 assert.equal(rows[0].course,null);
 assert.equal(rows[1].st,null);
 assert.equal(rows[2].time,null);
 assert.equal(rows[3].st,0);
});
