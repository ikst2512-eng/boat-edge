'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const now=Date.parse('2026-10-13T08:25:00+09:00');
const win={},doc={readyState:'loading',addEventListener(){}};
vm.runInNewContext(fs.readFileSync('assets/boat_edge_v223_source_visibility.js','utf8'),
  {window:win,document:doc,Date,console,setTimeout(){},setInterval(){}});
const a=win.BoatEdgeV223Source;
assert.ok(a&&typeof a.inspect==='function'&&typeof a.exhibitionFlags==='function');
const when='2026-10-13T08:22:00+09:00';
const met={deadline:'08:35',phase:'PRE_RESULT',results_seen:false,unlock:false,scoring:false};
const source={status:'ok',fetched_at:when};
const boats6=Array.from({length:6},(_,i)=>({lane:i+1,values:i<5?[36+i/10]:[]}));
const entrants=Array.from({length:6},(_,i)=>({course:i+1,exhibition_st:i<5?0.12:undefined}));
const racers=Array.from({length:6},(_,i)=>({lane:i+1,exhibition_time:i<5?6.9:undefined}));
const race={race_key:'20261013-14-01',meta:met,actual_entry:entrants,
  beforeinfo:{racers,start_exhibition:Array.from({length:6},(_,i)=>({lane:i+1}))},
  original_exhibition:{labels:['1周'],boats:boats6},
  source_audit:{beforeinfo:source,stt:source,tkz:source,original_exhibition:source}};
const by=(r,label)=>a.inspect(r,null,null,now).rows.find(x=>x[0]===label);
assert.equal(by(race,'展示タイム')[1],'unknown','5/6 must not claim full verified');
assert.equal(by(race,'展示ST・進入')[1],'unknown','five of six ST must not certify');
assert.equal(by(race,'オリ展')[1],'unknown','five of six metric boats must not certify');
const full={...race,
  beforeinfo:{...race.beforeinfo,racers:racers.map((x,i)=>({...x,exhibition_time:6.9+i/100}))},
  actual_entry:entrants.map((x,i)=>({...x,exhibition_st:0.12+i/100})),
  original_exhibition:{...race.original_exhibition,boats:boats6.map((x,i)=>({...x,values:[36+i/10]}))}};
assert.equal(by(full,'展示タイム')[1],'ok');
assert.equal(by(full,'オリ展')[1],'ok');
assert.equal(by(full,'展示ST・進入')[1],'ok');
let flags=a.exhibitionFlags(a.inspect(full,null,null,now));
assert.equal(flags.length,4);
assert.equal(flags[0].quality,'ok');
assert.equal(flags[1].quality,'ok');
assert.equal(flags[2].quality,'unknown');
assert.equal(flags[3].quality,'unknown');
const provider={status:'ok',fetched_at:when,
 source:'https://boaters-boatrace.com/example',sha256:'a'.repeat(64)};
const third={...full,source_audit:{...full.source_audit,boaters_original_exhibition:provider}};
flags=a.exhibitionFlags(a.inspect(third,null,null,now));
assert.equal(flags[2].quality,'ok');
assert.match(flags[2].text,/数値一致は別確認/);
assert.equal(flags[3].quality,'unknown');
assert.equal(a.exhibitionFlags(a.inspect(null,null,null,now))[0].quality,'unknown');
const html=fs.readFileSync('index.html','utf8');
assert(html.includes('boat_edge_v223_source_visibility.js?v=223&amp;rev=244&amp;patch=250&amp;source=282'));
assert(html.includes('boat_edge_v223_source_visibility.css?v=223&amp;rev=244&amp;source=282'));
assert(fs.readFileSync('assets/boat_edge_v223_source_visibility.css','utf8').includes('.be223-exhibition-flags'));
console.log('V282_SIX_BOAT_EXHIBITION_SOURCE_PROOF_PASS');
