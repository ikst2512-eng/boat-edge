'use strict';
/* V250 UI evidence regressions. No fetch, no collector, no formal results. */
const fs=require('fs'),vm=require('vm'),assert=require('assert');
function load(path,query){
 const elements=new Map();
 const doc={readyState:'loading',hidden:false,visibilityState:'visible',
  addEventListener(){},querySelector(s){return query?.(s)||null},
  querySelectorAll(){return []},
  createElement(){return {style:{},dataset:{},setAttribute(){},textContent:''}},
  getElementById(id){if(!elements.has(id))elements.set(id,{
    textContent:'',innerHTML:'',addEventListener(){},classList:{toggle(){}},
    value:'hit'
  });return elements.get(id);}
 };
 const window={};
 const context={window,document:doc,Date,Intl,console,Math,Number,Set,Map,
   setTimeout(){},setInterval(){},queueMicrotask(){},fetch:async()=>{throw Error('offline test')}};
 vm.runInNewContext(fs.readFileSync(path,'utf8'),context,{filename:path});
 return window;
}
const stamp=(s,quality)=>({dataset:{quality},textContent:s});
function oddBox(key,status,detail){
 const row={querySelector(s){
  return s==='span:first-child'?{textContent:'3連単オッズ'}:
   s==='span:last-child'?stamp(detail,status):null;
 }};
 return {dataset:{raceKey:key},querySelectorAll(s){return s==='.be223-row'?[row]:[]}};
}
const key='20261012-02-05';
let box=oddBox(key,'ok','10:40取得（リアルタイムではない）');
const p=load('assets/boat_edge_v204_prediction.js',s=>s==='#be223Source'?box:null).BoatEdgeV204;
assert.equal(p.oddsProof({race_key:key}).quality,'verified');
assert.match(p.oddsProof({race_key:key}).label,/10:40/);
assert.equal(p.oddsProof({race_key:'20261012-02-06'}).quality,'unknown');
box=oddBox(key,'stale','古い 10:12');
assert.equal(p.oddsProof({race_key:key}).quality,'stale');
box=oddBox(key,'unknown','未取得');
assert.equal(p.oddsProof({race_key:key}).quality,'unknown');
assert(fs.readFileSync('assets/boat_edge_v223_source_visibility.js','utf8').includes('node.dataset.raceKey=key'));
assert(fs.readFileSync('assets/boat_edge_v204_prediction.js','utf8').includes('be250-odds-proof'));
const r=load('assets/boat_edge_v241_results.js').BoatEdgeV241ResultsUI.sampleInfo;
const site=JSON.parse(fs.readFileSync('data/site_autopilot/v241_results_current.json','utf8'));
const sample=r(site);
assert(sample&&sample.total===site.rows.length);
assert(sample.top===site.top10_hits&&sample.head===site.head_hits);
assert.match(sample.label,/サイト参考予想のみ/);
assert.match(sample.label,/正式Fresh/);
assert.equal(r({...site,head_hits:site.head_hits+1}),null);
assert.equal(r({...site,date_latest:'20200101'}),null);
assert.equal(r({...site,rows:site.rows.slice(1)}),null);
const racer=load('assets/boat_edge_v203_readable.js').BoatEdgeV203;
const rows=[37.1,37.3,37.4,37.8,38.1,38.4].map((n,i)=>({
 lane:i+1,lap:n,turn:5+i*.1,straight:7+i*.04
}));
const source={race_key:key,meta:{deadline:'11:00',results_seen:false,unlock:false,scoring:false},
 source_audit:{original_exhibition:{status:'ok',fetched_at:'2026-10-12T10:25:00+09:00',sha256:'a'.repeat(64)}}};
const gaps=racer.exhibitionGaps(source,rows);
assert(gaps&&Math.abs(gaps.lap[2]-.2)<.000001);
assert(Math.abs(gaps.straight[1]-0)<.000001);
assert.equal(racer.exhibitionGaps(source,rows.slice(1)),null);
assert.equal(racer.exhibitionGaps(source,rows.map((r,i)=>i===3?{...r,lap:null}:r))?.lap,undefined);
assert.equal(racer.exhibitionGaps({...source,meta:{...source.meta,results_seen:true}},rows),null);
assert.equal(racer.exhibitionGaps({...source,source_audit:{original_exhibition:{...source.source_audit.original_exhibition,fetched_at:'2026-10-12T11:10:00+09:00'}}},rows),null);
assert.equal(racer.exhibitionGaps({...source,source_audit:{original_exhibition:{...source.source_audit.original_exhibition,sha256:'x'}}},rows),null);
const paper=load('assets/boat_edge_v211_paper.js').BoatEdgeV211PaperEvidence;
const proof={verified:true,day:'20261012',current:true};
const t=Date.parse('2026-10-12T11:20:00+09:00');
const scan={as_of:'2026-10-12T10:59:00+09:00',skipped_by_reason:{odds_missing:3,scratch_stale:2}};
const skipped=paper.skipEvidence(scan,proof,t);
assert.equal(skipped.verified,true);assert.equal(skipped.rows.length,2);
assert.equal(skipped.rows[0][0],'odds_missing');
assert.equal(paper.skipEvidence({...scan,skipped_by_reason:{missing:'2'}},proof,t).verified,false);
assert.equal(paper.skipEvidence({...scan,as_of:'2026-10-11T20:00:00+09:00'},proof,t).verified,false);
assert.equal(paper.skipEvidence({...scan,as_of:'2026-10-12T12:00:00+09:00'},proof,t).verified,false);
assert.match(paper.skipEvidence({...scan,skipped_by_reason:{}},proof,t).message,/未記録/);
console.log('V250_A17_A18_A19_A20_SOURCE_ONLY_TESTS_PASS');
