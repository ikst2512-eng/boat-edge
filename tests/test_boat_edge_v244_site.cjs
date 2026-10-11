'use strict';
/* V244 prospective safety: test read-only UI logic, no network and no formal results. */
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const at=Date.parse('2026-10-12T08:20:00+09:00');
function load(path,extend={}){
 const code=fs.readFileSync(path,'utf8');
 const window={...extend};
 const doc={readyState:'loading',addEventListener(){},querySelector(){return null},querySelectorAll(){return []}};
 const ctx={window,document:doc,Date,console,setTimeout(){},setInterval(){},queueMicrotask(){},fetch:async()=>{throw Error('offline test')},
   ...extend};
 vm.runInNewContext(code,ctx,{filename:path});
 return window;
}
// A04: FIRST/FINAL comes ONLY from existing banner evidence. LATEST never marked frozen.
const predicted=load('assets/boat_edge_v204_prediction.js');
const freeze=predicted.BoatEdgeV204.freezeEvidence;
const container=(kind,detail)=>({querySelector(sel){
 if(sel==='.be181-freeze-banner')return kind?{dataset:{be181Source:kind}}:null;
 if(sel==='.be181-freeze-banner > small')return detail?{textContent:detail}:null;
 return null;
}});
assert.equal(freeze(container('final','08:25保存')).locked,true);
assert.equal(freeze(container('first','初回固定')).locked,true);
assert.equal(freeze(container('latest','')).locked,false);
assert.equal(freeze(container(null,'')).kind,'unknown');
assert.match(freeze(container(null,'')).label,/未確認/);
// A05: six-of-six and real winning gap required. No relative leader from missing or ties.
const racers=load('assets/boat_edge_v203_readable.js').BoatEdgeV203;
const strong=racers.strongest;
const vals=[3.4,4.2,5.1,4.5,4.6,4.3].map(v=>({v}));
assert.equal(strong(vals,x=>x.v,.3),5.1);
assert.equal(strong(vals,x=>x.v,.6),null);
assert.equal(strong(vals.slice(0,5),x=>x.v,.3),null);
assert.equal(strong([3.4,4.2,5.1,null,4.6,4.3].map(v=>({v})),x=>x.v,.3),null);
assert.equal(strong([3.4,4.2,5.1,5.1,4.6,4.3].map(v=>({v})),x=>x.v,.3),null);
// A06: independently sourced SHA evidence only; CSV source must never be passed off as BOATERS.
const source=load('assets/boat_edge_v223_source_visibility.js',{BoatEdgeV222Odds:{validate:()=>({quality:'fresh'})}}).BoatEdgeV223Source;
const race={race_key:'20261012-02-01',meta:{deadline:'08:35',phase:'PRE_RESULT',results_seen:false,unlock:false,scoring:false},
 racers:Array.from({length:6},(_,i)=>({lane:i+1})),source_audit:{}};
const missing=source.inspect(race,null,null,at);
assert.equal(missing.rows.length,8);
assert.equal(missing.rows[6][1],'unknown');
assert.equal(missing.rows[7][1],'unknown');
const good={status:'ok',sha256:'a'.repeat(64),fetched_at:'2026-10-12T08:12:00+09:00',source:'https://boaters-boatrace.com/venue'};
const day={status:'ok',sha256:'b'.repeat(64),fetched_at:'2026-10-12T08:13:00+09:00',source:'https://kyoteibiyori.com/stats'};
race.source_audit={original_exhibition:{...good,source:'https://boatracecsv.github.io/data/previews/original_exhibition/2026/10/12.csv'}};
assert.equal(source.inspect(race,null,null,at).rows[6][1],'unknown');
race.source_audit.boaters_original_exhibition=good;
race.source_audit.keiteibiyori_original_exhibition=day;
let rows=source.inspect(race,null,null,at).rows;
assert.equal(rows[6][1],'ok');assert.equal(rows[7][1],'ok');
race.source_audit.boaters_original_exhibition={...good,source:'https://boatracecsv.github.io/mislabel'};
assert.equal(source.inspect(race,null,null,at).rows[6][1],'unknown');
race.source_audit.boaters_original_exhibition={...good,fetched_at:'2026-10-12T08:40:00+09:00'};
assert.equal(source.inspect(race,null,null,at).rows[6][1],'unknown');
race.source_audit.boaters_original_exhibition={...good,fetched_at:'2026-10-12T07:00:00+09:00'};
assert.equal(source.inspect(race,null,null,at).rows[6][1],'stale');
// A07: no synthetic 50k or budget proof if a saved finance field is absent or inconsistent.
const paper=load('assets/boat_edge_v211_paper.js').BoatEdgeV211PaperEvidence.paperEvidence;
const sample={mode:'PAPER_ONLY',strategy_status:'CALIBRATION_GATE',scan:{skipped_by_reason:{not_calibrated:12}},
 money:{day:'20261012',virtual_only:true,daily_budget_yen:50000,today_spent_yen:0,today_remaining_yen:50000,today_paper_races:0}};
let x=paper(sample,Date.parse('2026-10-12T09:30:00+09:00'));
assert.equal(x.verified,true);assert.equal(x.current,true);assert.equal(x.spent,0);
assert.match(x.message,/50,000円/);assert.match(x.message,/見送り理由/);
assert.equal(paper({...sample,money:{...sample.money,today_remaining_yen:51000}},at).verified,false);
assert.equal(paper({...sample,money:{...sample.money,virtual_only:false}},at).verified,false);
assert.equal(paper({...sample,money:{...sample.money,today_spent_yen:undefined}},at).verified,false);
assert.equal(paper({...sample,money:{...sample.money,day:'20261011'}},at).current,false);
console.log('V244_A04_A05_A06_A07_EVIDENCE_ONLY_RUNTIME_TESTS_PASS');
