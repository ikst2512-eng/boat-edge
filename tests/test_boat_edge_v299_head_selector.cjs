'use strict';
/* V299 strictly presentational head-ticket reader. Synthetic DOM; no fetches. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const js=fs.readFileSync('assets/boat_edge_v206_quickview.js','utf8');
const css=fs.readFileSync('assets/boat_edge_v206_quickview.css','utf8');
const window={},document={readyState:'loading',addEventListener(){}};
vm.runInNewContext(js,{window,document,console:{warn(){}},Date,Number,Math,Map,Set,JSON,
 queueMicrotask(){},setInterval(){throw Error('no timers in unit boot')}},{filename:'v299.js'});
const api=window.BoatEdgeV206;
assert.equal(api.version,'V299-UI-ONLY');
assert.equal(typeof api.headTickets,'function');
const node=combo=>({querySelector(k){return k==='b'?{textContent:combo}:null}});
const original=['1-2-3','2-1-3','1-3-2','3-1-2','1-2-4','1-4-2','4-2-1','1-5-2'].map(node);
const take=api.headTickets(original,1);
assert.equal(take.length,5,'max 5 from existing ranked list');
assert.equal(JSON.stringify([...take].map(x=>x.rank)),JSON.stringify([1,3,5,6,8]),'never rerank by filtering');
assert.equal(JSON.stringify([...take].map(x=>x.combo)),JSON.stringify(['1-2-3','1-3-2','1-2-4','1-4-2','1-5-2']));
assert.equal(api.headTickets(original,6).length,0,'absence is not inferred prediction');
assert.equal(api.headTickets(original,0),null);
assert.equal(api.headTickets(original,7),null);
assert.equal(api.headTickets(original.slice(0,121).concat(original).slice(0,121),1),null,'duplicate invalid');
assert.equal(api.headTickets([node('1-1-2')],1),null);
assert.equal(api.headTickets([node('1-2-3'),node('1-2-3')],1),null);
assert.equal(api.headTickets([node('1-2-3'),node('unknown')],1),null);
assert.equal(api.headTickets([],1),null);
assert.equal(api.headTickets(Array(121).fill(node('1-2-3')),1),null);
assert.match(js,/r\.meta\.results_seen===false&&r\.meta\.unlock===false&&r\.meta\.scoring===false/);
assert.match(js,/status\?\.kind!=='stop'/);
assert.match(js,/const locked=\['first','final','latest'\]\.includes\(marker\)/);
assert.match(js,/renderHead\(box,r,mode,st\)/);
assert(js.includes('data-be206-head-close'));
assert(css.includes('min-height:44px'));
assert(css.includes('aria-pressed="true"'));
assert(!/(?:fetch\(|XMLHttpRequest|localStorage|rankPredictions\(|updateOdds\(|RESULT_UNLOCK_TOKEN|winning_combo|official_payout)/.test(js));
const rows=Array.from({length:6},(_,i)=>({lane:i+1,name:'艇'+(i+1),grade:'A1',national:{win_rate:6}}));
assert.equal((api.matrix(rows).match(/data-be206-head="/g)||[]).length,6);
assert.equal((api.format(rows).match(/data-be206-head="/g)||[]).length,6);
if(fs.existsSync('index.html')){
 const html=fs.readFileSync('index.html','utf8');
 const home=html.indexOf('<main id="homeView"'),shortcuts=html.indexOf('class="be241-home-shortcuts"');
 const race=html.indexOf('<main id="raceView"');
 assert(home>0&&shortcuts>home&&race>shortcuts,'home shortcuts belong only inside home view');
 assert(html.includes('boat_edge_v206_quickview.css?v=299'));
 assert(html.includes('boat_edge_v206_quickview.js?v=299'));
}
console.log('V299_HEAD_SELECTION_SOURCE_ONLY_HOME_SCOPED_PASS');
