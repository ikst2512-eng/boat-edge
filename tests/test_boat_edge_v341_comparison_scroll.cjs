'use strict';
/* Synthetic comparison viewport only. No race data, outcomes, network or timers. */
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
function fixture(left=0,width=300,total=650){
 const calls=[],previous={},next={},position={textContent:''};
 const view={clientWidth:width,scrollWidth:total,scrollLeft:left,hidden:false,
  querySelector:()=>({offsetWidth:94}),scrollTo:options=>calls.push(options)};
 const controls={hidden:true,querySelector:s=>s.includes('previous')?previous:s.includes('next')?next:position};
 const box={querySelector:s=>s==='.be206-matrix-scroll'?view:s==='.be206-scroll-controls'?controls:null};
 return {box,view,controls,previous,next,position,calls};
}
test('both ends, middle and Safari elastic overscroll are bounded',()=>{
 const api=boot();
 for(const [left,prev,next] of [[0,false,true],[120,true,true],[350,true,false],[-18,false,true],[380,true,false]]){
  const state=api.comparisonScrollState({clientWidth:300,scrollWidth:650,scrollLeft:left});
  assert.equal(state.previous,prev);assert.equal(state.next,next);
  assert(state.left>=0&&state.left<=350);
 }
});
test('absent, hidden-sized, invalid and nonoverflowing viewports have no navigation',()=>{
 const api=boot();
 for(const view of [null,{}, {clientWidth:0,scrollWidth:650,scrollLeft:0},
  {clientWidth:300,scrollWidth:NaN,scrollLeft:0},{clientWidth:650,scrollWidth:650,scrollLeft:0}]){
  assert.equal(api.comparisonScrollState(view).overflow,false);
 }
 assert.equal(api.scrollComparison(null,'next'),false);
 api.updateComparisonScroll(null);
});
test('button availability and labels follow actual scroll position',()=>{
 const api=boot(),f=fixture();api.updateComparisonScroll(f.box);
 assert.equal(f.controls.hidden,false);assert.equal(f.previous.disabled,true);assert.equal(f.next.disabled,false);
 assert.equal(f.position.textContent,'左端から表示中');
 f.view.scrollLeft=350;api.updateComparisonScroll(f.box);
 assert.equal(f.previous.disabled,false);assert.equal(f.next.disabled,true);assert.equal(f.position.textContent,'右端まで表示中');
 f.view.scrollLeft=160;api.updateComparisonScroll(f.box);
 assert.equal(f.position.textContent,'左右の艇へ移動できます');
 f.view.hidden=true;api.updateComparisonScroll(f.box);assert.equal(f.controls.hidden,true);
 f.view.hidden=false;f.view.clientWidth=700;api.updateComparisonScroll(f.box);assert.equal(f.controls.hidden,true);
});
test('next and previous reveal columns after the sticky label without changing source values',()=>{
 const api=boot(),f=fixture();
 assert.equal(api.scrollComparison(f.box,'next'),true);
 assert.equal(f.calls[0].left,206);assert.equal(f.calls[0].behavior,'smooth');
 assert.equal(f.view.scrollLeft,0,'browser owns the viewport scroll, not application state');
 f.view.scrollLeft=300;api.scrollComparison(f.box,'next');assert.equal(f.calls[1].left,350);
 api.scrollComparison(f.box,'previous');assert.equal(f.calls[2].left,94);
});
test('reduced motion, resizing and end buttons never overshoot',()=>{
 const api=boot(true),f=fixture();
 api.scrollComparison(f.box,'next');assert.equal(f.calls[0].behavior,'auto');
 assert.equal(api.scrollComparison(f.box,'previous'),false);
 f.view.scrollLeft=350;assert.equal(api.scrollComparison(f.box,'next'),false);
 f.view.hidden=true;assert.equal(api.scrollComparison(f.box,'previous'),false);
 f.view.hidden=false;assert.equal(api.scrollComparison(f.box,'bad'),false);
 f.view.clientWidth=650;assert.equal(api.scrollComparison(f.box,'previous'),false);
 assert.equal(f.calls.length,1);
});
test('tiny viewport keeps forward movement positive when the sticky label is wide',()=>{
 const api=boot(),f=fixture(0,80,650);api.scrollComparison(f.box,'next');
 assert.equal(f.calls[0].left,40);
});
