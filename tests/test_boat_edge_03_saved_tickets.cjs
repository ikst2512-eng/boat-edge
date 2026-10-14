'use strict';
// 03: existing predeadline browser archive, not a newly frozen prediction.
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const js=fs.readFileSync('assets/boat_edge_03_saved_tickets.js','utf8');
const KEY='20261013-14-03',OTHER='20261013-14-04';
const meta={date:'2026-10-13',venue_code:'14',race_no:3,deadline:'09:00'};
const seen='2026-10-13T08:25:00+09:00';
const combos=[];
for(let a=1;a<=6;a++)for(let b=1;b<=6;b++)for(let c=1;c<=6;c++)
 if(new Set([a,b,c]).size===3)combos.push(a+'-'+b+'-'+c);
const record={
 schema:'V181_FIRST_SEEN_BEFORE_DEADLINE',race_key:KEY,first_seen_at:seen,
 modes:Object.fromEntries(['hit','balance','hole','narrow'].map(mode=>
   [mode,{tickets:combos.slice(0,12).map(combo=>({combo,p:5}))}]))
};
const storage=new Map([['boatEdgeV181FirstShown:'+KEY,JSON.stringify(record)]]);
let writes=0,created=null,removed=0;
const anchor={insertAdjacentElement:(_pos,p)=>{created=p;}};
const host={querySelector:s=>s==='.summary-top'?anchor:null,prepend:p=>{created=p;}};
const page={readyState:'loading',addEventListener(){},
 querySelector:s=>s==='#raceView .race-summary'?host:null,
 getElementById:s=>s==='be03SavedTickets'?created:null,
 createElement:tag=>({
   tagName:tag,dataset:{},setAttribute(){},remove(){removed++;created=null;},
   className:'',innerHTML:'',id:''
 })};
const state={race:{race_key:KEY,meta}};
const localStorage={getItem:k=>storage.get(k)||null,setItem(){writes++;throw Error('read-only archive cannot write');}};
const window={};
vm.runInNewContext(js,{window,document:page,state,localStorage,Date,Set,Object,Number,JSON});
const api=window.BoatEdge03SavedTickets;
const NOW=Date.parse('2026-10-14T12:00:00+09:00');
assert.equal(api.displayOnly,true);
assert.equal(api.parse(KEY,meta,record,NOW)?.key,KEY);
assert.equal(api.parse(OTHER,meta,record,NOW),null,'a different race cannot claim this archive');
assert.equal(api.parse(KEY,{...meta,venue_code:'06'},record,NOW),null);
assert.equal(api.parse(KEY,{...meta,race_no:4},record,NOW),null);
assert.equal(api.parse(KEY,meta,{...record,first_seen_at:'2026-10-13T09:00:00+09:00'},NOW),null,
 'postdeadline capture must not be promoted');
assert.equal(api.parse(KEY,meta,{...record,first_seen_at:'2099-01-01T00:00:00+09:00'},NOW),null);
assert.equal(api.parse(KEY,meta,{...record,modes:{...record.modes,hit:{tickets:[{combo:'1-1-2'}]}}},NOW),null);
assert.equal(api.parse(KEY,meta,{...record,modes:{...record.modes,hit:{tickets:[{combo:'1-2-3'},{combo:'1-2-3'}]}}},NOW),null);
assert.equal(api.parse(KEY,meta,{...record,modes:{hit:record.modes.hit}},NOW),null);
assert.equal(api.read(KEY,meta,NOW)?.modes.hit.tickets.length,12);
const p=api.parse(KEY,meta,record,NOW);
for(const [limit,expected] of [[3,3],[5,5],[10,10],['all',12]]){
 const html=api.markup(p,'hit',limit);
 assert.equal((html.match(/<li>/g)||[]).length,expected);
 assert(html.includes(combos[0]));
 assert(html.includes('この端末の初回記録'));
 assert(html.includes('正式最終予想・的中判定・購入履歴ではありません'));
 assert(!/data-be207|be108-ticket|購入する|的中時想定払戻|オッズ [\d.]+倍/.test(html));
}
api.render();
assert(created&&created.dataset.raceKey===KEY);
assert(created.innerHTML.includes(combos[0]));
assert.equal((created.innerHTML.match(/<li>/g)||[]).length,10);
assert.equal(writes,0,'must not rewrite first shown local record');
state.race={race_key:OTHER,meta:{...meta,race_no:4}};
api.render();
assert.equal(created,null,'another race without archive must not show previous race tickets');
assert(removed>=1);
state.race={race_key:KEY,meta};
api.render();
assert(created&&created.dataset.raceKey===KEY,'same race reload should restore local first-seen picks');
assert.equal(writes,0);
const index=fs.readFileSync('index.html','utf8');
assert(index.includes('boat_edge_03_saved_tickets.js?display=first-seen-reference'));
assert(js.includes('#raceView.be03-race-loading #be03SavedTickets{display:none!important}'));
assert(!/(?:fetch\(|XMLHttpRequest|resultFor\(|payout|winning_combo|RESULT_UNLOCK_TOKEN|localStorage\.setItem)/.test(js),
 'view-only archive cannot read results or create new predictions');
console.log('BOAT_EDGE_03_SAVED_FIRST_SEEN_REFERENCE_PER_RACE_RESTORED_PASS');
