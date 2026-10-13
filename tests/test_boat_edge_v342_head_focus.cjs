'use strict';
/* V342 synthetic head-panel focus only. No race data, outcomes or network. */
const test=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
function boot(reduced=false){
 const window={matchMedia:()=>({matches:reduced})};
 vm.runInNewContext(fs.readFileSync('assets/boat_edge_v206_quickview.js','utf8'),{
  window,document:{readyState:'loading',addEventListener(){}},
  console,Date,Number,Math,Map,Set,JSON
 });
 return window.BoatEdgeV206;
}
function focusFixture(){
 const calls=[];
 const button=(lane,visible,connected=true)=>({dataset:{be206Head:String(lane)},
  isConnected:connected,disabled:false,getClientRects:()=>visible?[{}]:[],focus:options=>calls.push({lane,options})});
 const buttons=[button(2,false),button(3,true),button(2,true)];
 return {calls,buttons,box:{isConnected:true,querySelectorAll:()=>buttons}};
}
test('closing restores the same racer in the visible layout only',()=>{
 const api=boot(),f=focusFixture(),key='20261013-02-05';
 assert.equal(api.restoreHeadFocus(key,key,2,f.box),true);
 assert.equal(f.calls.length,1);assert.equal(f.calls[0].lane,2);
 assert.equal(f.calls[0].options.preventScroll,true);
});
test('race changes and invalid selections never move focus',()=>{
 const api=boot(),f=focusFixture(),key='20261013-02-05';
 assert.equal(api.restoreHeadFocus(key,'20261013-02-06',2,f.box),false);
 assert.equal(api.restoreHeadFocus('bad',key,2,f.box),false);
 for(const lane of [null,0,7,2.5,'2'])assert.equal(api.restoreHeadFocus(key,key,lane,f.box),false);
 assert.equal(f.calls.length,0);
});
test('unmounted, hidden or disabled controls cannot receive returned focus',()=>{
 const api=boot(),f=focusFixture(),key='20261013-02-05';
 assert.equal(api.restoreHeadFocus(key,key,2,null),false);
 f.box.isConnected=false;assert.equal(api.restoreHeadFocus(key,key,2,f.box),false);
 f.box.isConnected=true;f.buttons[2].isConnected=false;
 assert.equal(api.restoreHeadFocus(key,key,2,f.box),false);
 f.buttons[2].isConnected=true;f.buttons[2].disabled=true;
 assert.equal(api.restoreHeadFocus(key,key,2,f.box),false);
 assert.equal(f.calls.length,0);
});
test('both comparison layouts expose a collapsed named head panel control',()=>{
 const api=boot(),rows=Array.from({length:6},(_,i)=>({lane:i+1,name:'選手'+(i+1)}));
 for(const html of [api.matrix(rows),api.format(rows)]){
  assert.equal((html.match(/aria-controls="be206HeadPanel"/g)||[]).length,6);
  assert.equal((html.match(/aria-expanded="false"/g)||[]).length,6);
 }
});
