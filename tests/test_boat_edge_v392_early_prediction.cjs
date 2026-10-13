'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const js=fs.readFileSync('assets/boat_edge_v392_early_prediction.js','utf8');
const window={},document={readyState:'loading',addEventListener(){}};
vm.runInNewContext(js,{window,document,Date,console,setInterval(){}});
const api=window.BoatEdgeV392;
assert.equal(typeof api.cardSafety,'function');
assert.equal(typeof api.previewSafety,'function');
const KEY='20261015-14-01';
const NOW=new Date('2026-10-14T20:05:00+09:00').getTime();
const race={
 race_key:KEY,
 meta:{date:'2026-10-15',venue_code:'14',venue:'鳴門',race_no:1,
   deadline:'08:35',phase:'PRE_RESULT',results_seen:false,unlock:false,scoring:false},
 source_audit:{race_card:{status:'ok',fetched_at:'2026-10-14T20:00:00+09:00',sha256:'a'.repeat(64)}},
 racers:Array.from({length:6},(_,i)=>({
   lane:i+1,registration_no:String(5001+i),class:i===0?'A1':'B1',
   avg_st:.15+i/100,national:{win_rate:7-i*.4},
   local:{win_rate:5},motor:{quinella_rate:30+i},raw_text:'出走表'
 }))
};
const combos=[];
for(let a=1;a<=6;a++)for(let b=1;b<=6;b++)for(let c=1;c<=6;c++)
 if(new Set([a,b,c]).size===3)combos.push(a+'-'+b+'-'+c);
const rows=combos.map((combo,i)=>({rank:i+1,combo,relative_score:120-i}));
const cardInputs=r=>[...r.racers].sort((a,b)=>a.lane-b.lane).map(x=>
 [x.lane,x.registration_no,x.class,x.avg_st,x.national.win_rate,x.local.win_rate,x.motor.quinella_rate]);
const preview={
 schema:'BOAT_EDGE_V392_CARD_ONLY_PREVIEW_V1',model_id:'V392-CARD-HEURISTIC-UNCALIBRATED',
 prediction_kind:'EARLY_CARD_ONLY_REFERENCE_NOT_FINAL',race_key:KEY,
 source_date:'2026-10-15',deadline:'08:35',
 produced_at:'2026-10-14T20:01:00+09:00',
 source_card_fetched_at:'2026-10-14T20:00:00+09:00',
 source_card_sha256:'a'.repeat(64),card_fingerprint_sha256:'b'.repeat(64),
 racer_inputs_by_lane:cardInputs(race),head_candidate:1,
 ranked_120:rows,top3:combos.slice(0,3),top5:combos.slice(0,5),
 top10:combos.slice(0,10),
 guards:{results_seen:false,unlock:false,scoring:false},
 formal_fresh_claim:false,score_is_calibrated_probability:false,
 odds_used:false,betting_enabled:false,stake_yen:null
};
assert.equal(api.cardSafety(race,NOW).ok,true);
assert.equal(api.previewSafety(race,preview,NOW).ok,true);
assert.equal(api.previewSafety(race,preview,
 new Date('2026-10-15T08:35:00+09:00').getTime()).ok,false);
assert.equal(api.cardSafety({...race,meta:{...race.meta,unlock:true}},NOW).ok,false);
assert.equal(api.cardSafety({...race,meta:{...race.meta,venue_code:'18'}},NOW).ok,false);
assert.equal(api.cardSafety({...race,racers:race.racers.slice(0,5)},NOW).ok,false);
assert.equal(api.cardSafety({...race,racers:race.racers.map((x,i)=>i===0?{...x,status:'欠場'}:x)},NOW).ok,false);
assert.equal(api.cardSafety({...race,scratch_audit:{blocked:true}},NOW).ok,false);
assert.equal(api.cardSafety({...race,source_audit:{race_card:{status:'missing'}}},NOW).ok,false);
assert.equal(api.previewSafety(race,{...preview,odds_used:true},NOW).ok,false);
assert.equal(api.previewSafety(race,{...preview,formal_fresh_claim:true},NOW).ok,false);
assert.equal(api.previewSafety(race,{...preview,source_date:'2026-10-14'},NOW).ok,false);
assert.equal(api.previewSafety(race,{...preview,source_card_sha256:'f'.repeat(64)},NOW).ok,false);
assert.equal(api.previewSafety(race,{...preview,source_card_fetched_at:'2026-10-14T19:59:00+09:00'},NOW).ok,false);
assert.equal(api.previewSafety({...race,source_audit:{race_card:{...race.source_audit.race_card,sha256:'b'.repeat(64)}}},preview,NOW).ok,false);
assert.equal(api.previewSafety(race,{...preview,racer_inputs_by_lane:[]},NOW).ok,false);
assert.equal(api.previewSafety(race,{...preview,top5:combos.slice(1,6)},NOW).ok,false);
assert.equal(api.previewSafety(race,{...preview,ranked_120:rows.slice(0,10)},NOW).ok,false);
assert.equal(api.previewSafety(race,{...preview,ranked_120:rows.map((x,i)=>i===1?{...x,combo:rows[0].combo}:x)},NOW).ok,false);
const html=fs.readFileSync('index.html','utf8');
const home=fs.readFileSync('assets/boat_edge_v108.js','utf8');
const workflow=fs.readFileSync('.github/workflows/auto-update.yml','utf8');
const nightly=fs.readFileSync('.github/workflows/v392-preday-cards.yml','utf8');
assert.match(html,/window\.BoatEdgeV392\?\.render\(d\)/);
assert.match(html,/boat_edge_v392_early_prediction\.js\?v=392/);
assert.match(home,/data\/site_early_calendar\//);
assert.match(home,/BOAT_EDGE_V392_NEXT_DAY_CARDS_V1/); // explicit future never treated as results
assert.match(workflow,/boat_edge_v392_card_preview\.py --mode today/);
assert.match(nightly,/boat_edge_v392_card_preview\.py --mode tomorrow/);
assert.match(nightly,/boat_edge_v392_card_preview\.py --mode today/);
assert.match(nightly,/push:\s*\n\s*branches: \[main\]/);
assert.match(nightly,/schedule:/);
assert.doesNotMatch(js,/site_results\/|formal_predictions\/|race\/result|race\/pay|fetch\(.+odds/);
/* Synthetic PRE_RESULT-only contract. No past or future results are read. */
document.querySelector = sel => sel.includes('data-be181-verification="site-sha-audit"')
  ? {dataset:{be181RaceKey:KEY}} : null;
assert.equal(api.finalFor(KEY),true);
assert.equal(api.finalFor('20261015-14-02'),false);
document.querySelector=()=>null;
assert.equal(api.finalFor(KEY),false);
assert.match(home,/be181VerifiedPreDeadlineFinal\(key,race\?\.meta\?\.deadline\)/);
assert.match(home,/window\.BoatEdgeV392\?\.hide\?\.\(\)/);
assert.match(js,/if\(finalFor\(r\.race_key\)\)\{hide\(\);return;\}/);

(async()=>{
 const crypto=require('node:crypto');
 const start=home.indexOf('async function be181VerifiedPreDeadlineFinal(');
 const end=home.indexOf('function be181InstallStyle()',start);
 const valStart=home.indexOf('function be181ValidFinal(');
 const valEnd=home.indexOf('async function be181ServerFinal(',valStart);
 assert.ok(start>0 && end>start && valStart>0 && valEnd>valStart);
 const code=home.slice(valStart,valEnd)+'\n'+home.slice(start,end);
 const due='2026-10-15T08:35:00+09:00';
 const at=Date.parse('2026-10-15T08:33:00+09:00');
 const record={
  race_key:KEY,prediction_kind:'SITE_REFERENCE_V122',
  snapshot_window:'FINAL_15M',deadline:'08:35',minutes_to_deadline:3.9,
  first_saved_at:'2026-10-15T08:31:01+09:00',
  saved_at:'2026-10-15T08:31:02+09:00',
  guards:{results_seen:false,unlock:false,scoring:false},
  modes:Object.fromEntries(['hit','balance','hole','narrow'].map(mode=>
   [mode,{tickets:[{combo:'1-2-3',p:20,stake_yen:1000},{combo:'1-3-2',p:10,stake_yen:1000}]}]))
 };
 const bytes=Buffer.from(JSON.stringify(record));
 const sha=crypto.createHash('sha256').update(bytes).digest('hex');
 const audit={race_key:KEY,pass:true,latest_snapshot_sha256:sha};
 const proof={
  schema:'BOAT_EDGE_V229_ATOMIC_PRE_RESULT_SOURCE_EVIDENCE_V1',
  scope:'SITE_REFERENCE_ONLY_NO_FORMAL_OR_RESULT_ACCESS',
  race_key:KEY,snapshot_sha256:sha,new_snapshot_created_this_run:true,
  results_seen:false,formal_fresh_unlock:false,scoring:false,
  snapshot_saved_at:record.saved_at
 };
 let frames=[bytes,audit,proof],broken=null;
 const fetch=async url=>{
  const i=/site_prediction_snapshots/.test(url)?0:
    /site_prediction_audit/.test(url)?1:2;
  if(i===broken)return {ok:false};
  return {ok:true,arrayBuffer:async()=>Uint8Array.from(frames[0]).buffer,
   json:async()=>frames[i]};
 };
 const context=vm.createContext({
  fetch,crypto:crypto.webcrypto,TextDecoder,Uint8Array,Date,Number,Array,
  Object,String,Set,JSON,
  be181KeyValid:key=>/^20\d{6}-\d{2}-\d{2}$/.test(key)
 });
 vm.runInContext(code,context);
 const verify=()=>vm.runInContext('be181VerifiedPreDeadlineFinal('+
   JSON.stringify(KEY)+','+JSON.stringify('08:35')+','+at+')',context);
 const pass=await verify();
 assert.equal(pass.race_key,KEY,'Verified snapshot must match selected race');
 assert.equal((await vm.runInContext('be181VerifiedPreDeadlineFinal('+
   JSON.stringify(KEY)+','+JSON.stringify('08:35')+','+
   Date.parse(due)+')',context)),null,'At/after deadline cannot newly promote');
 const makeChoice=flag=>vm.runInContext('be181ShowChoice('+
   JSON.stringify(KEY)+',2,false,'+JSON.stringify(pass)+',null,'+
   JSON.stringify({hit:[{combo:'4-5-6',p:1}]})+',"hit",'+flag+')',context);
 const selected=makeChoice('true');
 assert.equal(selected.source,'final');
 assert.equal(selected.rows[0].combo,'1-2-3');
 assert.equal(makeChoice('false').source,'latest');
 frames=[bytes,{...audit,latest_snapshot_sha256:'0'.repeat(64)},proof];
 assert.equal(await verify(),null,'Mismatched V125 SHA rejects final');
 frames=[bytes,{...audit,settlement:{}},proof];
 assert.equal(await verify(),null,'Result-bearing audit cannot be read as PRE_RESULT proof');
 frames=[bytes,audit,{...proof,snapshot_sha256:'a'.repeat(64)}];
 assert.equal(await verify(),null,'Mismatched V229 SHA rejects final');
 frames=[bytes,audit,{...proof,results_seen:true}];
 assert.equal(await verify(),null,'Result seen rejects final');
 frames=[bytes,audit,proof];broken=1;
 assert.equal(await verify(),null,'Missing audit rejects final');
 broken=null;
 assert.equal(await verify()!==null,true,'Valid verified final recovered');
 console.log('V392_SITE_FINAL_SHA_AUDIT_HANDOFF_FIXTURE_PASS');
 console.log('V392_NEXTDAY_CARD_PREVIEW_TOP3_TOP5_TOP10_SOURCE_BOUND_PASS');
})().catch(error=>{console.error(error);process.exitCode=1});
