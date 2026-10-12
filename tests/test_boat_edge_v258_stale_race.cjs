'use strict';
/* V258: offline race-switch concurrency guards; no results, payouts, network or wager writes. */
const assert=require('assert'),fs=require('fs'),vm=require('vm');
const src=fs.readFileSync('assets/boat_edge_v108.js','utf8');
const snippet=(first,last)=>{const a=src.indexOf(first),b=src.indexOf(last,a);assert(a>=0&&b>a,first+' missing');return src.slice(a,b)};
const modesJs=snippet('let be258PredictionSerial=0;','\nasync function renderMainPick(');
const afterJs=snippet('let be258RaceRenderSerial=0;','\nfunction wrapRenderRace(');
const pending=()=>{let resolve;const promise=new Promise(r=>{resolve=r});return{promise,resolve}};
const raceA={race_key:'20261012-03-03'};
const raceB={race_key:'20261012-18-05'};
(async()=>{
  // Test A: a previous race's odds request cannot continue into mode computation.
  {
    const gate=pending();let active=raceA,indexCalls=0,adjustCalls=0;
    const context={
      raceOf:()=>active,
      $:()=>({}),oddsFor:async()=>gate.promise,resultFor:async()=>null,
      loadServerHistoryIndex:async()=>{indexCalls++},
      be122ScenarioAdjusted:async()=>{adjustCalls++;return {}}
    };
    vm.runInNewContext(modesJs+'\nthis.run=renderPredictionModes;',context);
    const first=context.run(raceA,{mode:'reference'});
    active=raceB;gate.resolve({});
    await first;
    assert.equal(indexCalls,0,'stale race must not read shared history');
    assert.equal(adjustCalls,0,'stale race must not recalculate tickets');
  }
  // Test B: two overlapping requests for the same race use latest-wins semantics.
  {
    const older=pending(),newer=pending(),onScenario=pending();
    let active=raceA,calls=0,adjustCalls=0,firstShown=0;
    const context={
      raceOf:()=>active,$:()=>({}),
      oddsFor:()=>++calls===1?older.promise:newer.promise,
      resultFor:async()=>null,
      loadServerHistoryIndex:async()=>{},
      be122ScenarioAdjusted:async()=>{adjustCalls++;return onScenario.promise},
      be181First:()=>{firstShown++;return null}
    };
    vm.runInNewContext(modesJs+'\nthis.run=renderPredictionModes;',context);
    const old=context.run(raceA,{mode:'formal'});
    const fresh=context.run(raceA,{mode:'formal'});
    older.resolve({});await old;
    assert.equal(adjustCalls,0,'superseded same-race request must stop');
    newer.resolve({});
    await new Promise(resolve=>setImmediate(resolve));
    assert.equal(adjustCalls,1,'only newest same-race request computes scenario');
    active=raceB;
    onScenario.resolve({});await fresh;
    assert.equal(firstShown,0,'race switch while scenario pending may not freeze a stale ticket');
  }
  // Test C: the parent afterRace pipeline must stop after async scenario fetch when selection moves.
  {
    const gate=pending();let selected=raceA,mutations=0;
    const context={
      raceOf:()=>selected,predOf:()=>({mode:'reference'}),
      $:()=>null,window:{},document:{getElementById:()=>null},
      cleanTabs(){},fixBottom(){},installBackButtons(){},enhanceRaceNav(){},markStandouts(){},
      be182StopReason:()=>null,
      be122ScenarioAdjusted:()=>gate.promise,
      be122PredictionFromAdjusted(){mutations++;return{}},
      renderMainPick(){mutations++},renderCourseStats(){mutations++},
      renderPredictionModes(){mutations++}
    };
    vm.runInNewContext(afterJs+'\nthis.run=afterRace;',context);
    const first=context.run(raceA);selected=raceB;gate.resolve({tickets:[]});
    await first;
    assert.equal(mutations,0,'outdated race may not repaint or compute derived buys');
  }
  // Test D: fail closed if async direct-mode or odds augmentation is invoked after a switch.
  assert(src.includes("if(raceOf()?.race_key!==key)return;\n  const rows=$$(\"#buyBoard .buy-ticket\")"));
  assert(src.includes('if(raceOf()?.race_key!==key)return;\\n  const stack=$("#tab-scenario .section.stack")'.replace('\\\\n','\\n')));
  console.log('V258_STALE_RACE_RENDER_PASS: race switch, same-race supersession, async pipeline, payout guard');
})().catch(e=>{console.error(e);process.exitCode=1});
