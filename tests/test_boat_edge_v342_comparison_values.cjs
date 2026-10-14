'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
function boot(){
 const window={};
 vm.runInNewContext(fs.readFileSync('assets/boat_edge_v206_quickview.js','utf8'),{
 window,document:{readyState:'loading',addEventListener(){}},console,Date,Number,Math,Set,Map,JSON});
 return window.BoatEdgeV206;
}
function rows(){return Array.from({length:6},(_,i)=>({lane:i+1,name:'選手'+(i+1),grade:'A1',
 national:{win_rate:6-i*.5,quinella_rate:40+i,trio_rate:60+i},local:{win_rate:5,quinella_rate:30+i},motor:{quinella_rate:20+i},
 time:6.8+i*.1,st:.1+i*.04,course:i+1,avg:.15+i*.01,lap:36+i*.1,turn:5+i*.1,straight:7+i*.1,f:false}));}
function fixture(count){
 const cells=Array.from({length:count},()=>({textContent:'old',className:'old'}));
 const selectedButton={focused:true},table={querySelectorAll:()=>cells};
 Object.defineProperty(table,'innerHTML',{set(){throw Error('must keep racer buttons mounted');}});
 return {cells,selectedButton,table};
}
test('matrix value updates preserve mounted buttons and input objects',()=>{
 const api=boot(),r=rows(),f=fixture(18),before=JSON.stringify(r);
 assert.equal(api.updateComparisonValues(f.table,r,'lanes','base'),true);
 assert.equal(f.cells[0].textContent,'6.00');assert.equal(f.cells[5].textContent,'3.50');
 assert.equal(f.cells[6].textContent,'5.00');assert.equal(f.cells[12].textContent,'20.0');
 assert(f.cells[0].className.includes('best'));
 r[0].national.win_rate=3;
 api.updateComparisonValues(f.table,r,'lanes','base');
 assert.equal(f.cells[0].textContent,'3.00');assert(!f.cells[0].className.includes('best'));
 assert.equal(f.selectedButton.focused,true);
 r[0].national.win_rate=6;assert.equal(JSON.stringify(r),before);
});
test('row layout uses the correct cell order and precision in all four metric modes',()=>{
 const api=boot(),r=rows();
 for(const [name,count,first] of [['base',18,'6.00'],['combo',24,'40.0'],['exhibit',24,'6.80'],['original',18,'36.00']]){
  const f=fixture(count);assert.equal(api.updateComparisonValues(f.table,r,'rows',name),true);
  assert(f.cells.every(x=>x.textContent!=='old'&&x.className.startsWith('be206-val')));
  assert.equal(f.cells[0].textContent,first);
 }
 const f=fixture(18);api.updateComparisonValues(f.table,r,'rows','base');
 assert.deepEqual(f.cells.slice(0,6).map(x=>x.textContent),['6.00','5.00','20.0','5.50','5.00','21.0']);
});
test('missing exhibition values, F and strict highlight rules survive in-place updates',()=>{
 const api=boot(),r=rows(),f=fixture(24);r[2].st=-.03;r[2].f=true;r[5].time=null;
 assert.equal(api.updateComparisonValues(f.table,r,'lanes','exhibit'),true);
 assert.equal(f.cells[5].textContent,'－');assert.equal(f.cells[8].textContent,'F0.03');
 assert(f.cells[8].className.includes('foul'));
 assert(f.cells.slice(0,12).every(x=>!x.className.includes('best')));
});
test('unexpected table shapes fail before any cell writes so board can rerender safely',()=>{
 const api=boot(),f=fixture(17),r=rows();
 assert.equal(api.updateComparisonValues(f.table,r,'lanes','base'),false);
 assert(f.cells.every(x=>x.textContent==='old'));
 assert.equal(api.updateComparisonValues(null,r,'lanes','base'),false);
 assert.equal(api.updateComparisonValues(f.table,r.slice(0,5),'lanes','base'),false);
 assert.equal(api.updateComparisonValues(f.table,r,'bad','base'),false);
 assert.equal(api.updateComparisonValues(f.table,r,'rows','bad'),false);
});

test('bad source types never masquerade as measured zero in six-lane basic metrics',()=>{
 const api=boot(),r=rows(),f=fixture(18);
 r[0].national.win_rate=false;    // previously 0.00
 r[1].national.win_rate=[];       // previously 0.00
 r[2].national.win_rate={};       // malformed composite
 r[3].national.win_rate='';       // empty source
 r[4].national.win_rate='0';      // measured numeric zero stays measurable
 r[5].national.win_rate=0;        // raw measured numeric zero
 assert.equal(api.updateComparisonValues(f.table,r,'lanes','base'),true);
 assert.deepEqual(f.cells.slice(0,6).map(x=>x.textContent),
  ['－','－','－','－','0.00','0.00']);
 assert(f.cells.slice(0,6).every(x=>!x.className.includes('best')),
  'missing lanes cannot establish a six-of-six best boat');
 const rr=rows();rr[0].motor.quinella_rate=true;rr[1].motor.quinella_rate=[];
 assert.equal(api.updateComparisonValues(f.table,rr,'lanes','base'),true);
 assert.equal(f.cells[12].textContent,'－');
 assert.equal(f.cells[13].textContent,'－');
 assert.equal(api.best(rr,'motor.quinella_rate',3,false),null);
});
test('exhibition ST preserves measured zero and F while rejecting malformed booleans',()=>{
 const api=boot(),r=rows(),f=fixture(24);
 r[0].st=false;r[1].st=[];r[2].st=0;r[3].st=-0.02;r[3].f=true;
 api.updateComparisonValues(f.table,r,'lanes','exhibit');
 assert.equal(f.cells[6].textContent,'－');
 assert.equal(f.cells[7].textContent,'－');
 assert.equal(f.cells[8].textContent,'0.00');
 assert.equal(f.cells[9].textContent,'F0.02');
 assert(f.cells[6].className.includes('be206-val'));
 assert(f.cells.slice(6,12).every(x=>!x.className.includes('best')));
});
