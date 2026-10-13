'use strict';
/* Exercise real board/init handlers with a synthetic DOM; no data or network. */
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
function boot(){
 const handlers={},queue=[],classes=new Set();
 const cls={add:x=>classes.add(x),remove:x=>classes.delete(x),contains:x=>classes.has(x),toggle:(x,on)=>on?classes.add(x):classes.delete(x)};
 function makeTable(){
  let html='';const node={cells:[],rebuilds:0,button:{},querySelectorAll:()=>node.cells};
  Object.defineProperty(node,'innerHTML',{get:()=>html,set:value=>{
    html=value;node.rebuilds++;node.button={};node.cells=Array.from({length:(value.match(/<td /g)||[]).length},()=>({textContent:'',className:''}));
  }});return node;
 }
 const mode={dataset:{be108Mode:'hit'}},matrix=makeTable(),table=makeTable();
 const compact={hidden:true},viewport={hidden:false,clientWidth:300,scrollWidth:650,scrollLeft:0};
 const controls={hidden:true,querySelector:()=>({})};
 let panelHtml='';const panelNodes={};
 const panel={hidden:true,isConnected:true,childNodes:[],rebuilds:0,focus(){},scrollIntoView(){},
  querySelector:s=>panelNodes[s]||null,replaceChildren(){this.childNodes=[];panelHtml='';for(const key of Object.keys(panelNodes))delete panelNodes[key];}};
 Object.defineProperty(panel,'innerHTML',{get:()=>panelHtml,set:value=>{
  panelHtml=value;panel.childNodes=[{}];panel.rebuilds++;
  panelNodes['.be206-head-top strong']={textContent:''};panelNodes['.be206-head-source']={textContent:''};
  panelNodes['.be206-head-lines']={innerHTML:''};panelNodes['[data-be206-head-close]']={focused:false};
 }});
 const source={textContent:''},help={textContent:''},safety={dataset:{}};
 const strong={textContent:''},detail={textContent:''};
 let list={};
 let tickets=['1-2-3','2-1-3'];
 const pred={querySelector:s=>s==='.be108-ticket-list'?list:null};
 const nodes={'.be206-safety':safety,'.be206-safety strong':strong,'.be206-safety span':detail,
  '.be206-table-scroll':compact,'.be206-matrix-scroll':viewport,'.be206-matrix':matrix,'.be206-table':table,
  '.be206-table-help':help,'.be206-source':source,'.be206-headpanel':panel,'.be206-scroll-controls':controls};
 const box={isConnected:true,nextElementSibling:pred,querySelector:s=>
  s==='.be206-matrix tbody'?(matrix.innerHTML?{}:null):s==='.be206-table tbody'?(table.innerHTML?{}:null):nodes[s]||null,
  querySelectorAll:()=>[],remove(){this.isConnected=false;}};
 const root={insertBefore(){}};
 const selectors={'#be108PredictionModes':pred,'#tab-pred .section.stack':root,'#be203Layout':{},'#be204Overview':{},
  '#be206Quick':box,'#be108PredictionModes .be108-mode-tabs .on':mode,
  '#be108PredictionModes .be181-freeze-banner':{dataset:{be181Source:'latest'}}};
 const document={readyState:'loading',hidden:false,documentElement:{classList:cls},
  querySelector:s=>selectors[s]||null,querySelectorAll:s=>s==='#be108PredictionModes .be108-ticket-list > .be108-ticket'?
   tickets.map(combo=>({querySelector:()=>({textContent:combo})})):[],addEventListener:(name,fn)=>{handlers[name]=fn;}};
 const state={race:{race_key:'20261013-02-05',meta:{phase:'PRE_RESULT',results_seen:false,unlock:false,scoring:false}}};
 const rows=Array.from({length:6},(_,i)=>({lane:i+1,name:'選手'+(i+1),grade:'A1',national:{win_rate:6+i/10},local:{win_rate:5},motor:{quinella_rate:30}}));
 const window={BoatEdgeV203:{getRows:()=>rows},BoatEdgeV205:{sourceStatus:()=>({kind:'partial',title:'照合中',detail:'fixture'})},addEventListener(){}};
 vm.runInNewContext(fs.readFileSync('assets/boat_edge_v206_quickview.js','utf8'),{
  window,document,state,console,Date,Number,Math,Map,Set,JSON,queueMicrotask:fn=>queue.push(fn),setInterval(){}
 });
 handlers.DOMContentLoaded();
 function flush(){let count=0;while(queue.length){assert(++count<20);queue.shift()();}}
 function layout(value){handlers.click({target:{closest:s=>s.includes('[data-be206-layout]')?{dataset:{be206Layout:value}}:null}});flush();}
 function openHead(lane){handlers.click({target:{closest:s=>s==='#be206Quick [data-be206-head]'?{dataset:{be206Head:String(lane)}}:null}});flush();}
 function nextRace(){state.race={...state.race,race_key:'20261013-02-06'};list={};window.BoatEdgeV206.sync();}
 return {api:window.BoatEdgeV206,state,rows,mode,viewport,compact,layout,nextRace,matrix,table,panel,openHead,setTickets:value=>{tickets=value;}};
}
test('same-race mode changes retain the explicitly chosen row layout',()=>{
 const f=boot();f.layout('rows');assert.equal(f.compact.hidden,false);assert.equal(f.viewport.hidden,true);
 f.mode.dataset.be108Mode='balance';f.api.sync();
 assert.equal(f.compact.hidden,false);assert.equal(f.viewport.hidden,true);
 f.mode.dataset.be108Mode='chaos';f.api.sync();assert.equal(f.compact.hidden,false);
 f.nextRace();assert.equal(f.compact.hidden,true);assert.equal(f.viewport.hidden,false);
});
test('same-race updates retain horizontal position; a new race starts at lane one',()=>{
 const f=boot();f.viewport.scrollLeft=250;const original=JSON.stringify(f.state.race),rows=JSON.stringify(f.rows);
 f.api.sync();assert.equal(f.viewport.scrollLeft,250);
 f.mode.dataset.be108Mode='balance';f.api.sync();assert.equal(f.viewport.scrollLeft,250);
 assert.equal(JSON.stringify(f.state.race),original);assert.equal(JSON.stringify(f.rows),rows);
 f.nextRace();assert.equal(f.viewport.scrollLeft,0);
});
test('real board retains racer controls for value updates and rebuilds for a changed roster',()=>{
 const f=boot(),button=f.matrix.button,rebuilds=f.matrix.rebuilds;
 f.rows[0].national.win_rate=8;f.api.sync();
 assert.equal(f.matrix.rebuilds,rebuilds);assert.equal(f.matrix.button,button);
 assert.equal(f.matrix.cells[0].textContent,'8.00');
 f.state.race.source_audit={beforeinfo:{fetched_at:'2026-10-13T06:35:00+09:00'}};f.api.sync();
 assert.equal(f.matrix.button,button);
 f.rows[0].name='別の選手';f.api.sync();
 assert.equal(f.matrix.rebuilds,rebuilds+1);assert.notEqual(f.matrix.button,button);
});
test('head-ticket updates keep the focused close button mounted',()=>{
 const f=boot();f.openHead(1);assert.equal(f.panel.hidden,false);
 const button=f.panel.querySelector('[data-be206-head-close]');button.focused=true;
 const count=f.panel.rebuilds;
 assert(f.panel.querySelector('.be206-head-lines').innerHTML.includes('1-2-3'));
 f.setTickets(['1-3-2','2-1-3']);f.api.sync();
 assert(f.panel.querySelector('.be206-head-lines').innerHTML.includes('1-3-2'));
 assert(!f.panel.querySelector('.be206-head-lines').innerHTML.includes('1-2-3'));
 assert.equal(f.panel.querySelector('[data-be206-head-close]'),button);
 assert.equal(button.focused,true);assert.equal(f.panel.rebuilds,count);
 f.api.sync();assert.equal(f.panel.rebuilds,count);
});
test('invalid or no-longer-safe head tickets clear while preserving the close control',()=>{
 const f=boot();f.openHead(1);const button=f.panel.querySelector('[data-be206-head-close]');
 f.setTickets(['unknown']);f.api.sync();
 assert(f.panel.querySelector('.be206-head-lines').innerHTML.includes('確認できない'));
 assert.equal(f.panel.querySelector('[data-be206-head-close]'),button);
 f.setTickets(['1-2-3']);f.api.sync();assert(f.panel.querySelector('.be206-head-lines').innerHTML.includes('1-2-3'));
 f.state.race.meta.phase='UNCONFIRMED';f.api.sync();
 assert(!f.panel.querySelector('.be206-head-lines').innerHTML.includes('1-2-3'));
 assert.equal(f.panel.querySelector('[data-be206-head-close]'),button);
 f.nextRace();assert.equal(f.panel.hidden,true);assert.equal(f.panel.childNodes.length,0);
});
