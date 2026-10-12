'use strict';
const assert=require('assert'),fs=require('fs'),vm=require('vm');
const js=fs.readFileSync(process.argv[2]||__dirname+'/boat_edge_v222_live_odds.js','utf8');
const tick=Date.parse('2026-10-11T08:27:00+09:00');
const key='20261011-23-01';
const odds=(()=>{let d={};for(let a=1;a<=6;a++)for(let b=1;b<=6;b++)for(let c=1;c<=6;c++)if(a!==b&&a!==c&&b!==c)d[`${a}-${b}-${c}`]=13.0;return d})();
const race={race_key:key,meta:{deadline:'08:35',date:'2026-10-11'}};
const doc={schema_version:'boat-edge-site-odds-v71',race_key:key,phase:'PRE_RESULT_PURCHASE_ONLY',results_seen:false,scoring:false,source_url:'https://www.boatrace.jp/owpc/pc/race/odds3t?hd=20261011&jcd=23&rno=1',deadline:'08:35',fetched_at:'2026-10-11T08:26:00+09:00',trifecta_odds:odds,available_count:120};
let now=tick,shown=0,invalidated=0,fetches=0,shownKeys=[],res=structuredClone(doc),delayed=false,release;
const MockDate=class extends Date {static now(){return now}};
const ctx={window:{},Date:MockDate,document:{visibilityState:'visible',readyState:'loading',querySelector(s){return s==='#raceView.active'?{}:null;},addEventListener(){}},state:{race},
 renderRace(r,opts){shown++;shownKeys.push(r.race_key);assert.strictEqual(opts.silent,true);},
 fetch:async()=>{fetches++; if(delayed)await new Promise(resolve=>{release=resolve});return {ok:res!==null,json:async()=>structuredClone(res)};},
 setInterval(){},setTimeout(){},Number,JSON,Object,Math,String,Set};
ctx.window.BoatEdgeV166Invalidate=k=>{invalidated++;assert.strictEqual(k,key)};
vm.runInNewContext(js,ctx,{filename:'boat_edge_v222_live_odds.js'});
const api=ctx.window.BoatEdgeV222Odds;
(async()=>{
 assert.strictEqual(api.validate(res,race,now).quality,'fresh');
 await api.poll();assert.strictEqual(shown,1);assert.strictEqual(invalidated,1);
 await api.poll();assert.strictEqual(shown,1,'unchanged odds must not redraw');
 res=structuredClone(doc);res.trifecta_odds['1-2-3']=14.2;
 await api.poll();assert.strictEqual(shown,2,'odds-only change must redraw');
 res=structuredClone(doc);res.fetched_at='2026-10-11T08:12:00+09:00';
 await api.poll();assert.strictEqual(shown,3,'fresh->stale must clear displayed current price');
 await api.poll();assert.strictEqual(shown,3,'unchanged stale status must not loop redraw');
 res=structuredClone(doc);res.results_seen=true;
 await api.poll();assert.strictEqual(shown,4,'result-flag odds must be invalidated');
 assert.strictEqual(api.validate(res,race,now).quality,'invalid');
 res=structuredClone(doc);res.source_url='https://example.com/odds';assert.strictEqual(api.validate(res,race,now).quality,'invalid');
 res=structuredClone(doc);res.fetched_at='2026-10-11T08:40:00+09:00';assert.strictEqual(api.validate(res,race,now).quality,'invalid');
 res=structuredClone(doc);res.trifecta_odds['1-2-3']=0;assert.strictEqual(api.validate(res,race,now).quality,'invalid');
 res=null;await api.poll();assert.strictEqual(shown,5,'missing evidence must invalidate current status');
 await api.poll();assert.strictEqual(shown,5,'no redrawing on repeated absent evidence');
 now=Date.parse('2026-10-11T08:36:00+09:00');
 const fetchedBeforeCutoff=fetches;
 await api.poll();assert.strictEqual(shown,6,'cutoff must clear previously visible purchase odds once');
 assert.strictEqual(fetches,fetchedBeforeCutoff,'postdeadline must not fetch odds');
 await api.poll();assert.strictEqual(shown,6,'repeated cutoff poll must not redraw');
 now=tick;res=structuredClone(doc);delayed=true;const promise=api.poll();
 await new Promise(resolve=>setImmediate(resolve));
 ctx.state.race={race_key:'20261011-18-01',meta:{deadline:'08:47'}};
 release();await promise;assert.strictEqual(shown,6,'race switch while fetch inflight must not repaint old race');
 console.log('V222_PASS: odds-only update, idempotency, stale/missing fail-closed, source check, time cutoff, race switch');
})().catch(e=>{console.error(e);process.exitCode=1});
