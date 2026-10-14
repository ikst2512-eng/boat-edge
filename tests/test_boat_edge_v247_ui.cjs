'use strict';
/* V247 UI-only source-binding tests; no network or formal results. */
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const racer=fs.readFileSync('assets/boat_edge_v203_readable.js','utf8');
const prediction=fs.readFileSync('assets/boat_edge_v204_prediction.js','utf8');
function getJsApi(code){
 const window={};
 const document={readyState:'loading',addEventListener(){},querySelector(){return null},querySelectorAll(){return []}};
 vm.runInNewContext(code,{window,document,console,setInterval(){},setTimeout(){},queueMicrotask(){},Date});
 return window;
}
const source=getJsApi(racer).BoatEdgeV203;
assert.equal(typeof source.getRows,'function');
assert.match(racer,/scratchError='',fullStats=true,fullTable=false/);
assert.match(racer,/fullStats=true;fullTable=false;fetchScratch/);
assert.match(racer,/B2連/);assert.match(racer,/B3連/);
assert.match(racer,/全国2連/);assert.match(racer,/当地3連/);
assert.match(racer,/M2連/);assert.match(racer,/M3連/);
function fakeElement(fields){
 return {querySelector(selector){return (fields&&fields[selector])||null},querySelectorAll(selector){return (fields&&fields[selector])||[]}};
}
function fakeBoat(n,name,role){return fakeElement({'.n':{textContent:String(n)},'.r':{textContent:name},'.a':{textContent:role}})}
const steps=[
 fakeElement({'.flow-boat.attack,.flow-boat.hot':[fakeBoat(4,'攻め艇','スタート注意')]}),
 fakeElement({'.flow-boat.attack,.flow-boat.hot':[fakeBoat(1,'内艇','イン'),fakeBoat(4,'攻め艇','攻め')]}),
 fakeElement({'.flow-boat.attack,.flow-boat.hot':[fakeBoat(5,'展開艇','外側の受益')]})
];
const flow=fakeElement({'.flow-step':steps,'.flow-conclusion .v':{textContent:'既存の結論だけ表示'}});
const window={};
const document={readyState:'loading',addEventListener(){},querySelector(s){return s==='#scenarioFlow'?flow:null},querySelectorAll(){return []}};
vm.runInNewContext(prediction,{window,document,console,Date,queueMicrotask(){}});
const stage=window.BoatEdgeV204.flowStages();
assert.equal(stage.length,4);
assert.match(stage[0].value,/4号艇/);
assert.match(stage[1].value,/攻め艇/);
assert.match(stage[2].value,/5号艇/);
assert.equal(stage[3].value,'既存の結論だけ表示');
assert(!stage.some(x=>/\d+(?:\.\d+)?%/.test(x.value)));
const keys=['results.html','assets/boat_edge_v241_results.js','assets/boat_edge_v241_results.css'];
const worker=fs.readFileSync('.github/workflows/v241.yml','utf8');
for(const path of keys)assert(worker.includes("'"+path+"'"));
assert(worker.includes('V241_EXISTING_RESOURCE_MODIFIED_FAIL_CLOSED_'));
/* T02 regression: legacy V241 scheduled package must not clobber V360's
 * source-verified home 🎯 renderer; bundled scorer/tests remain strict. */
const allowStart=worker.indexOf("if name in ('index.html'");
const allowEnd=worker.indexOf(":\n                          print('V241_PRESERVE_INDEPENDENTLY_UPDATED_PUBLIC_UI'",allowStart);
assert(allowStart>=0&&allowEnd>allowStart,'V241 explicit public UI exemption must exist');
const allow=worker.slice(allowStart,allowEnd);
assert(allow.includes("'assets/boat_edge_v241_home.js'"),'current verified home UI must be preserved');
assert(worker.includes('V241_PUBLIC_HOME_JS_MISSING_NO_LEGACY_REINSTALL'),'missing current JS must not install stale V241 copy');
for(const sensitive of ['scripts/boat_edge_v241_results.py','scripts/boat_edge_v241_patch_home.py',
                        'tests/test_boat_edge_v241_results.py'])
  assert(!allow.includes("'"+sensitive+"'"),'scorer and source-bound regression code must remain fail-closed');
assert(worker.includes("raise SystemExit('V241_PACKAGED_BYTES_INVALID_'+name)"));
assert(worker.includes("raise SystemExit('V241_EXISTING_RESOURCE_MODIFIED_FAIL_CLOSED_'+name)"));
console.log('V241_LEGACY_PACKAGED_UI_PRESERVE_SCORER_FAIL_CLOSED_PASS');
const resultJs=fs.readFileSync('assets/boat_edge_v241_results.js','utf8');
assert(resultJs.includes('!o.rows.every(verifiedRow)'));
assert(resultJs.includes("data-verification"));
const resultHtml=fs.readFileSync('results.html','utf8');
for(const word of ['検証済み的中','検証済み不的中','結果待ち','検証対象外'])assert(resultHtml.includes(word));
assert(!resultJs.includes('data/formal_'));
const nav=fs.readFileSync('assets/boat_edge_v166_refresh.js','utf8');
assert(nav.includes("b.textContent='↻ 更新'"));
assert(nav.includes("aria-label','現在のページのデータを更新"));
assert(nav.includes('window.BoatEdgeV166Refresh={refresh}'));
console.log('V247_FLOW_SIX_RACERS_VERIFIED_RESULTS_NAV_TESTS_PASS');
// V357: ensure five new fail-closed racer-card fixtures run in the existing V307 UI CI step.
require('./test_boat_edge_v357_card_source_integrity.cjs');
// V360: run verified-home-indicator regressions in the existing read-only UI CI.
require('./test_boat_edge_v360_home_result_safety.cjs');
// V361: enforce list-side result proof and official-link safety in V307 UI CI.
require('./test_boat_edge_v361_results_list_integrity.cjs');

// 03: selected mobile race content precedes lengthy GLOBAL operations proof.
// The health warning and its verification link must remain visible/accesssible.
const mobileRaceCss=fs.readFileSync('assets/boat_edge_v371_simple_ui.css','utf8');
const opsCss=mobileRaceCss.slice(mobileRaceCss.indexOf('/* 03 mobile race-first:'));
assert(opsCss.includes('body.be48-race-active #be220Ops #be259OpsProof'));
assert(opsCss.includes('body.be48-race-active #be220Ops #be220Info'));
assert(opsCss.includes('display:none!important'));
assert(opsCss.includes('#be220Ops #be220Status'));
assert(opsCss.includes('#be220Ops .be220-line a'));
assert(opsCss.includes('min-height:44px'));
assert(!opsCss.includes('body.be48-race-active #be220Ops{display:none'));
const opsJs=fs.readFileSync('assets/boat_edge_v220_site_ops.js','utf8');
assert(opsJs.includes('id="be220Status"'));
assert(opsJs.includes('aria-label="AI仮想運用と未見検証を見る"'));
console.log('BOAT_EDGE_03_MOBILE_RACE_FIRST_OPS_STATUS_PRESERVED_PASS');

// 03: data missing on a six-racer preview is not a measured 0.0%.
// Execute the production renderer, not a duplicate rate-format implementation.
const sixBoatSrc=fs.readFileSync('assets/boat_edge_final_v48.js','utf8');
const sixStart=sixBoatSrc.indexOf('function renderRacers(d){');
const sixEnd=sixBoatSrc.indexOf('function beforeMaps(d)',sixStart);
assert(sixStart>=0&&sixEnd>sixStart,'production six-boat renderer must be present');
const sixHost={innerHTML:''};
const sixCtx=vm.createContext({
  q:sel=>sel==='#be48Racers'?sixHost:null,
  lane:l=>'['+l+']',
  laneNo:(r,i)=>Number(r?.lane??i+1),
  value:v=>v===null||v===undefined||v===''?'—':v,
  esc:v=>String(v)
});
vm.runInContext(sixBoatSrc.slice(sixStart,sixEnd),sixCtx);
sixCtx.rows=[
 {lane:1,name:'Missing Both',motor:{quinella_rate:null},boat:{quinella_rate:''}},
 {lane:2,name:'Missing Motor',motor:{},boat:{quinella_rate:35.26}},
 {lane:3,name:'Measured Zero',motor:{quinella_rate:0},boat:{quinella_rate:0}},
 {lane:4,name:'No Motor/Boat',motor:null,boat:undefined},
 {lane:5,name:'Garbage',motor:{quinella_rate:'unknown'},boat:{quinella_rate:'NaN'}},
 {lane:6,name:'Standard',motor:{quinella_rate:27.75},boat:{quinella_rate:42.12}}
];
vm.runInContext('renderRacers({racers:rows})',sixCtx);
for(const textValue of ['Missing Both','Missing Motor','Measured Zero','No Motor/Boat','Garbage','Standard'])
 assert(sixHost.innerHTML.includes(textValue));
const sixCards=sixHost.innerHTML.match(/<article class="be48-racer">[\s\S]*?<\/article>/g)||[];
assert.equal(sixCards.length,6);
assert(sixCards[0].includes('M2<b>—</b>')&&sixCards[0].includes('B2<b>—</b>'));
assert(sixCards[1].includes('M2<b>—</b>')&&sixCards[1].includes('B2<b>35.3%</b>'));
assert(sixCards[2].includes('M2<b>0.0%</b>')&&sixCards[2].includes('B2<b>0.0%</b>'));
assert(sixCards[3].includes('M2<b>—</b>')&&sixCards[3].includes('B2<b>—</b>'));
assert(sixCards[4].includes('M2<b>—</b>')&&sixCards[4].includes('B2<b>—</b>'));
assert(sixCards[5].includes('M2<b>27.8%</b>')&&sixCards[5].includes('B2<b>42.1%</b>'));
console.log('BOAT_EDGE_03_SIX_BOAT_MISSING_RATE_NOT_ZERO_PASS');

// 03: the legacy compact beforeinfo must not bypass PRE_RESULT source evidence
// or silently overwrite duplicated start/exhibition entries.
const beforeSrc=fs.readFileSync('assets/boat_edge_final_v48.js','utf8');
const beforeStart=beforeSrc.indexOf('function sourceReady(d,kind){');
const beforeEnd=beforeSrc.indexOf('function compactDetails(d){',beforeStart);
assert(beforeStart>0&&beforeEnd>beforeStart,'beforeinfo guard source must exist');
const beforeHost={innerHTML:''};
const beforeCtx=vm.createContext({
 q:s=>s==='#be48Before'?beforeHost:null,
 lane:l=>'['+l+']',esc:v=>String(v),
 value:v=>v===null||v===undefined||v===''?'—':v,
 Date,Map,Set,Number,String
});
vm.runInContext(beforeSrc.slice(beforeStart,beforeEnd),beforeCtx);
const mkAudit=(t='2026-10-14T08:22:00+09:00')=>({
 status:'ok',sha256:'b'.repeat(64),fetched_at:t
});
const bRace={
 race_key:'20261014-14-01',
 meta:{date:'2026-10-14',venue_code:'14',race_no:1,deadline:'08:35',
  phase:'PRE_RESULT',results_seen:false,unlock:false,scoring:false},
 racers:Array.from({length:6},(_,i)=>({lane:i+1,name:'選手'+(i+1)})),
 beforeinfo:{
  racers:Array.from({length:6},(_,i)=>({lane:i+1,exhibition_time:6.8+i/100,tilt:0})),
  start_exhibition:Array.from({length:6},(_,i)=>({lane:i+1,st:i===0?'.12':i===1?'F.02':'.15',course:i+1}))
 },
 source_audit:{beforeinfo:mkAudit(),stt:{status:'missing'}},actual_entry:[]
};
beforeCtx.sample=bRace;
const renderBefore=()=>vm.runInContext('renderBeforeCompact(sample)',beforeCtx);
renderBefore();
assert(beforeHost.innerHTML.includes('展示進入（枠→コース・保存値）'));
assert(!beforeHost.innerHTML.includes('実進入'));
assert(beforeHost.innerHTML.includes('.12'));
assert(beforeHost.innerHTML.includes('F.02'));
assert(beforeHost.innerHTML.includes('6.8'));
assert(beforeHost.innerHTML.includes('締切前の取得証跡を照合した保存値'));
const withRace=(patch)=>{beforeCtx.sample={...bRace,...patch};renderBefore();return beforeHost.innerHTML;};
let htmlBefore=withRace({source_audit:{beforeinfo:{status:'missing'},stt:{status:'missing'}}});
assert(!htmlBefore.includes('.12')&&!htmlBefore.includes('6.8'));
assert(htmlBefore.includes('数値を非表示'));
htmlBefore=withRace({source_audit:{beforeinfo:mkAudit('2026-10-14T08:36:00+09:00'),stt:{status:'missing'}}});
assert(!htmlBefore.includes('.12')&&!htmlBefore.includes('6.8'),'post deadline evidence cannot show displayed measurements');
htmlBefore=withRace({meta:{...bRace.meta,results_seen:true}});
assert(!htmlBefore.includes('.12')&&!htmlBefore.includes('6.8'),'opened result guard cannot drive PRE_RESULT compact display');
htmlBefore=withRace({beforeinfo:{...bRace.beforeinfo,
 start_exhibition:[...bRace.beforeinfo.start_exhibition,{lane:1,st:'.99',course:6}],
 racers:[...bRace.beforeinfo.racers,{lane:2,exhibition_time:1.11,tilt:9}]
}});
assert(!htmlBefore.includes('.99')&&!htmlBefore.includes('1.11'));
const duplicates=htmlBefore.split('<div class="be48-brow">').slice(1).map(x=>x.split('</div>')[0]);
assert.equal(duplicates.length,6);
assert(duplicates[0].includes('<span>—</span>'),'duplicate start lane must be missing');
assert(duplicates[1].includes('<span>F.02</span><span>—</span><span>—</span>'),'duplicate racer time/tilt must be missing');
console.log('BOAT_EDGE_03_BEFOREINFO_SOURCE_BOUND_PRE_RESULT_COMPACT_PASS');

// 03 regression: a syntactically valid but wrong race file must never render.
const selectedRaceHtml=fs.readFileSync('index.html','utf8');
const identityStart=selectedRaceHtml.indexOf('function be03RaceSourceIdentity(file,jcd,race){');
const identityEnd=selectedRaceHtml.indexOf('async function refreshFormalStatus(){',identityStart);
assert(identityStart>0&&identityEnd>identityStart);
const guardContext=vm.createContext({
  Date,Set,Map,Promise,be03RaceRequestSerial:0,be03RaceLoadNotice:()=>{},
  state:{currentVenue:'14',race:{race_key:'20261014-14-01'}},
  document:{
    querySelector:()=>null,
    getElementById:s=>s==='raceView'?{classList:{add(){},remove(){}}}:s==='live'?{setAttribute(){}}:null
  },
  fetch:async()=>({ok:true,json:async()=>guardContext.payload}),
  be182FetchScratch:async r=>{guardContext.scratchCalls++;return r;},
  refreshFormalStatus:async()=>{},loadFormalOverlay:async()=>null,
  mergeFormalOverlay:r=>r,
  renderRace:r=>{guardContext.rendered.push(r.race_key);guardContext.state.race=r;},
  showToast:()=>{},console:{warn:()=>{}}
});
guardContext.payload={
 race_key:'20261014-14-03',
 meta:{date:'2026-10-14',venue_code:'14',race_no:3,
  phase:'PRE_RESULT',results_seen:false,unlock:false,scoring:false},
 racers:Array.from({length:6},(_,i)=>({lane:i+1}))
};
guardContext.rendered=[];guardContext.scratchCalls=0;
vm.runInContext(selectedRaceHtml.slice(identityStart,identityEnd),guardContext);
const loadFixture=(path='data/races/20261014-14-03.json',venue='14')=>
 vm.runInContext('loadRace('+JSON.stringify(path)+','+JSON.stringify(venue)+')',guardContext);
(async()=>{
 await loadFixture();
 assert.deepEqual(guardContext.rendered,['20261014-14-03']);
 assert.equal(guardContext.scratchCalls,1);
 guardContext.rendered.length=0;guardContext.scratchCalls=0;
 const baseline=guardContext.state.race;
 guardContext.payload={...baseline,race_key:'20261014-14-02'};
 await loadFixture();
 assert.equal(guardContext.rendered.length,0);
 assert.equal(guardContext.scratchCalls,0,'wrong race cannot reach scratch/overlay');
 assert.equal(guardContext.state.race,baseline,'invalid card cannot replace selected race');
 guardContext.payload={...baseline,meta:{...baseline.meta,race_no:4}};
 await loadFixture();assert.equal(guardContext.rendered.length,0);
 guardContext.payload=baseline;
 await loadFixture('data/races/20261014-14-03.json','06');
 assert.equal(guardContext.rendered.length,0,'wrong venue must stop');
 await loadFixture('data/races/20261014-14-02.json','14');
 assert.equal(guardContext.rendered.length,0,'filename must match contents');
 await loadFixture('../data/races/20261014-14-03.json','14');
 assert.equal(guardContext.rendered.length,0,'unexpected file path must stop');
 console.log('BOAT_EDGE_03_SELECTED_RACE_SOURCE_IDENTITY_FAIL_CLOSED_PASS');
})().catch(e=>{console.error(e);process.exitCode=1});

// 03: index.html pct() already formats world values with %.
// 0.5% is NOT 50%, and missing readings remain unverified.
const worldSrc=fs.readFileSync('assets/boat_edge_final_v48.js','utf8');
const normStart=worldSrc.indexOf('function normPct(v){');
const normEnd=worldSrc.indexOf('function renderRacers(d){',normStart);
assert(normStart>0&&normEnd>normStart);
const examples=['99.5%','0.5%','0.2%','1%','0%','－','未取得','-5%','105%'];
const fakeWorlds=examples.map(original=>{
 const prob={textContent:original},title={textContent:''};
 return {prob,title,querySelector:s=>s==='h3'?title:s==='.world-prob'?prob:null,
   querySelectorAll:()=>[],classList:{add(){}}};
});
const pctCtx=vm.createContext({
 Number,String,Math,
 qa:s=>s==='#worlds .world'?fakeWorlds:[],
 lane:n=>'艇'+n,
 document:{createElement:()=>({})}
});
vm.runInContext(worldSrc.slice(normStart,normEnd),pctCtx);
vm.runInContext('decorateWorlds()',pctCtx);
assert.deepEqual(fakeWorlds.map(w=>w.prob.textContent),examples,
 'sub-1% percentages must not be multiplied by 100');
assert.equal(fakeWorlds[1].title.textContent,'イン逃げ不成立');
assert.equal(vm.runInContext('normPct(0.5)',pctCtx),0.5);
assert.equal(vm.runInContext('normPct(null)',pctCtx),null);
assert.equal(vm.runInContext('normPct("")',pctCtx),null);
assert.equal(vm.runInContext('normPct(105)',pctCtx),null);
console.log('BOAT_EDGE_03_WORLD_PERCENT_BELOW_ONE_DISPLAY_PRESERVED_PASS');


// 03 live-refresh regression: source audit SHA, racer and prediction changes
// must be reflected without a new race selection or post-result access.
(async()=>{
 const html=fs.readFileSync('index.html','utf8');
 const identityStart=html.indexOf('function be03RaceSourceIdentity(file,jcd,race){');
 const identityEnd=html.indexOf('async function loadRace(file, jcd){',identityStart);
 const start=html.indexOf('function be03PassiveRefreshNotice(key,reason){');
 const end=html.indexOf('async function refreshAll(force=false){',start);
 assert(identityStart>0&&identityEnd>identityStart&&start>0&&end>start);
 const raceKey='20261014-14-09';
 const original={
   race_key:raceKey,
   meta:{date:'2026-10-14',venue_code:'14',race_no:9,
      phase:'PRE_RESULT',results_seen:false,unlock:false,scoring:false,
      updated_at:'2026-10-14T15:30:00+09:00'},
   racers:Array.from({length:6},(_,i)=>({lane:i+1,name:'選手'+(i+1)})),
   beforeinfo:{racers:[],start_exhibition:[]},
   actual_entry:[],original_exhibition:{boats:[]},
   source_audit:{beforeinfo:{status:'ok',sha256:'a'.repeat(64),
       fetched_at:'2026-10-14T15:25:00+09:00'}},
   derived:{top10:['1-2-3']}, odds:{}
 };
 let published=original,rendered=[],scratches=0,overlays=0;
 const fixed=Date.parse('2026-10-14T16:21:00+09:00');
 class Clock extends Date{static now(){return fixed;}}
 const ctx=vm.createContext({
   Date:Clock,Promise,Number,String,JSON,
   state:{race:original},
   document:{visibilityState:'visible',
     getElementById:()=>({classList:{contains:name=>name==='active'}})},
   fetch:async()=>({ok:true,json:async()=>published}),
   be182FetchScratch:async r=>{scratches++;return r;},
   loadFormalOverlay:async()=>{overlays++;return null;},
   mergeFormalOverlay:r=>r,
   renderRace:r=>{rendered.push(r);ctx.state.race=r;}
 });
 vm.runInContext(html.slice(identityStart,identityEnd)+String.fromCharCode(10)+html.slice(start,end),ctx);
 const refresh=()=>vm.runInContext('be162RefreshVisibleRace()',ctx);
 published={...original,source_audit:{
   beforeinfo:{...original.source_audit.beforeinfo,
     fetched_at:'2026-10-14T15:31:00+09:00',sha256:'b'.repeat(64)}}};
 await refresh();
 assert.equal(rendered.length,1,'SHA-only update must redraw selected race');
 assert.equal(ctx.state.race.source_audit.beforeinfo.sha256,'b'.repeat(64));
 await refresh();assert.equal(rendered.length,1,'identical source must not redraw');
 published={...ctx.state.race,derived:{top10:['1-2-4']}};
 await refresh();assert.equal(rendered.length,2,'forecast-only update must redraw');
 published={...ctx.state.race,racers:original.racers.map((r,i)=>
    i===0?{...r,name:'更新された選手'}:r)};
 await refresh();assert.equal(rendered.length,3,'six-boat card-only change must redraw');
 published={...ctx.state.race,source_audit:{
   ...ctx.state.race.source_audit,stt:{status:'ok',sha256:'c'.repeat(64)}}};
 await refresh();assert.equal(rendered.length,4,'STT receipt-only change must redraw');
 published={...ctx.state.race,meta:{...ctx.state.race.meta,phase:'RESULT'}};
 await refresh();assert.equal(rendered.length,4,'non-PRE_RESULT source must not redraw');
 published={...ctx.state.race,meta:{...ctx.state.race.meta,race_no:8}};
 await refresh();assert.equal(rendered.length,4,'metadata mismatched race must stop');
 published={...ctx.state.race,race_key:'20261014-14-08'};
 await refresh();assert.equal(rendered.length,4,'different race file must stop');
 assert.equal(scratches,5,'invalid identity and result-open data do not trigger scratch fetch');
 assert.equal(overlays,4,'unchanged source and unsafe sources never trigger overlay');
 console.log('BOAT_EDGE_03_LIVE_PRE_RESULT_SOURCE_RECEIPT_AND_PREDICTION_REFRESH_PASS');
})().catch(e=>{console.error(e);process.exitCode=1});


/* 03: exercise actual passive-refresh UI on bounded synthetic PRE_RESULT. */
(async()=>{
 const html=fs.readFileSync('index.html','utf8');
 const a=html.indexOf('function be03RaceSourceIdentity(file,jcd,race){');
 const b=html.indexOf('async function loadRace(file, jcd){',a);
 const c=html.indexOf('function be03PassiveRefreshNotice(key,reason){');
 const d=html.indexOf('async function refreshAll(force=false){',c);
 assert(a>0&&b>a&&c>0&&d>c);
 let note=null,reply=null,redraw=0,scratch=0,overlay=0;
 const key='20261014-14-09';
 const race={race_key:key,meta:{date:'2026-10-14',venue_code:'14',race_no:9,
  phase:'PRE_RESULT',results_seen:false,unlock:false,scoring:false},
  racers:Array.from({length:6},(_,i)=>({lane:i+1}))};
 const host={firstChild:null,querySelector:s=>s==='#be03PassiveRefreshNotice'?note:null,
  insertBefore:el=>{note=el;}};
 const view={classList:{contains:s=>s==='active'},querySelector:s=>s==='.race-summary'?host:null};
 class Clock extends Date{static now(){return Date.parse('2026-10-14T16:20:00+09:00');}}
 const ctx=vm.createContext({
  Date:Clock,Promise,String,JSON,Number,state:{race},
  document:{visibilityState:'visible',getElementById:s=>s==='raceView'?view:null,
   createElement:()=>({dataset:{},setAttribute(){},remove(){note=null;}})},
  fetch:async()=>reply(),
  be182FetchScratch:async r=>{scratch++;return r;},
  loadFormalOverlay:async()=>{overlay++;return null;},
  mergeFormalOverlay:r=>r,renderRace:()=>{redraw++;}
 });
 vm.runInContext(html.slice(a,b)+'\n'+html.slice(c,d),ctx);
 const refresh=()=>vm.runInContext('be162RefreshVisibleRace()',ctx);
 reply=()=>({ok:false,status:404});await refresh();
 assert.match(note?.textContent||'',/公開待ち（404）/);
 assert.match(note?.textContent||'',/前回取得時点/);
 assert.equal(note?.dataset.raceKey,key);
 assert.equal(redraw,0);assert.equal(scratch,0);assert.equal(overlay,0);
 const old=note;await refresh();assert.strictEqual(note,old,'do not duplicate status');
 reply=()=>{throw Error('offline');};await refresh();
 assert.match(note.textContent,/再取得でエラー/);
 reply=()=>({ok:true,json:async()=>({...race,race_key:'20261014-14-08'})});
 await refresh();assert.match(note.textContent,/照合が一致しません/);
 assert.equal(scratch,0,'do not process mismatched or missing source');
 reply=()=>({ok:true,json:async()=>({...race,meta:{...race.meta,results_seen:true}})});
 await refresh();assert.match(note.textContent,/安全条件/);
 assert.equal(scratch,0,'do not process result-open source');
 reply=()=>({ok:true,json:async()=>race});
 await refresh();assert.equal(note,null,'successful unchanged source clears stale state');
 assert.equal(redraw,0);assert.equal(scratch,1);assert.equal(overlay,0);
 reply=async()=>{ctx.state.race={...race,race_key:'20261014-14-10'};
  return {ok:false,status:404};};
 await refresh();assert.equal(note,null,'stale request cannot affect new selected race');
 console.log('BOAT_EDGE_03_PASSIVE_REFRESH_STALE_DATA_NOTICE_PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
