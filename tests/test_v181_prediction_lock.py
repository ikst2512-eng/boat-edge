from pathlib import Path
import tempfile,subprocess
patch_path=Path(__file__).resolve().parents[1]/'scripts/site_v181_patch.py'
patch=patch_path.read_text()
fixture=r'''const x='test';
async function renderPredictionModes(race,pred){
  const inFinalWindow=!resultConfirmed && mins!==null && mins>=0 && mins<=15;

  let snap=readLocal(snapKey(key));
  if(inFinalWindow)snap=saveFinalSnapshot(key,race,pred,modes,mins);

  const finalSnap=isFinalSnapshot(snap)?snap:null;
  const serverSnap=serverRecord?.snapshot||null;
  const effectiveSnap=resultConfirmed?(serverSnap||finalSnap):finalSnap;
  const settled=resultConfirmed?(serverRecord?.settlement||(finalSnap?settle(finalSnap,result):null)):null;

  const frozenRows=effectiveSnap?.modes?.[mode]?.tickets||null;
  const baseRows=(resultConfirmed&&frozenRows)?frozenRows:modes[mode]||[];
  const conf=(resultConfirmed&&effectiveSnap?.modes?.[mode]?.confidence!=null)?effectiveSnap.modes[mode].confidence:confidence(pred,mode,rows);
  let snapStatus="🎯履歴は締切15分前から保存";
  else if(resultConfirmed&&!effectiveSnap)snapStatus="締切前の最終スナップショットなし・的中判定対象外";
  else if(mins!==null&&mins<0)snapStatus=finalSnap?"締切済み・保存した最終予想を固定中":"締切済み・締切前スナップショットなし";
  panel.innerHTML=`${sourceBar}${be166OddsStatus(key,resultConfirmed)}${resultBar}<div class="be108-snapshot-status">${snapStatus}</div><div class="be108-mode-tabs">...`;
  $$("[data-be108-mode]",panel).forEach(b=>b.onclick=()=>{localStorage.setItem(ACTIVE_MODE,b.dataset.be108Mode);renderPredictionModes(race,pred)});
}
async function afterRace(race){
  if(typeof renderBuyBoard==="function")renderBuyBoard(race,adjustedPred);
  if(typeof renderDirectMode==="function")renderDirectMode(race,adjustedPred);
}
'''
with tempfile.TemporaryDirectory() as td:
    root=Path(td); (root/'assets').mkdir(); f=root/'assets/boat_edge_v108.js'; f.write_text(fixture)
    (root/'index.html').write_text('<script src="./assets/boat_edge_v108.js?v=168"></script>')
    v=subprocess.run(['python',str(patch_path)],cwd=td,text=True,capture_output=True)
    if v.returncode: print(v.stdout);print(v.stderr);raise SystemExit(v.returncode)
    a=f.read_text()
    assert 'BE181_FIRST_KEY' in a and "<div class=\"be108-snapshot-status\">${snapStatus}</div>${be181Banner" in a
    assert 'const baseRows=choice.rows;' in a
    v2=subprocess.run(['python',str(patch_path)],cwd=td,text=True,capture_output=True)
    assert v2.returncode==0 and v2.stdout.strip()=='V181_ALREADY_APPLIED'
    assert a==f.read_text()
    assert 'boat_edge_v108.js?v=181' in (root/'index.html').read_text()
    # Extract functions as JS module tests; source fixture itself is intentionally incomplete
    st=a.index('/* BOAT_EDGE_V181_FIRST_VIEW_IMMUTABLE_AND_FINAL_ONLY */')
    en=a.index('async function renderPredictionModes(race,pred){')
    (root/'helper.js').write_text(a[st:en])
    t=root/'test.cjs'
    t.write_text(r'''
const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
let mem=new Map();const root={readLocal:(k,f)=>mem.has(k)?mem.get(k):f,writeLocal:(k,v)=>mem.set(k,v),esc:x=>String(x),Date,Set,Map,Number,Object,Array,String,RegExp,JSON,fetch:async()=>({ok:false})};
vm.createContext(root);vm.runInContext(fs.readFileSync('helper.js','utf8'),root);
const fn=x=>vm.runInContext(x,root);
const key='20261010-01-01';
const combos=['1-2-3','1-3-2','1-2-4','1-4-2','1-2-5','1-5-2','2-1-3','2-3-1','3-1-2','3-2-1'];
const old=Object.fromEntries(['hit','balance','hole','narrow'].map(k=>[k,combos.map((combo,i)=>({combo,p:100-i,amount:1000}))]));
const first=fn(`be181First(${JSON.stringify(key)},${JSON.stringify(old)},10,false)`);
assert.equal(first.modes.hit.tickets[0].combo,'1-2-3');
const changed=JSON.parse(JSON.stringify(old));changed.hit[0].combo='2-1-4';
const kept=fn(`be181First(${JSON.stringify(key)},${JSON.stringify(changed)},5,false)`);
assert.equal(kept.modes.hit.tickets[0].combo,'1-2-3');
let choose=fn(`be181ShowChoice(${JSON.stringify(key)},5,false,null,${JSON.stringify(kept)},${JSON.stringify(changed)},'hit')`);
assert.equal(choose.source,'first');assert.equal(choose.rows[0].combo,'1-2-3');assert.equal(choose.changed,true);
mem.set('boatEdgeV181ModeChoice:'+key,'latest');
choose=fn(`be181ShowChoice(${JSON.stringify(key)},5,false,null,${JSON.stringify(kept)},${JSON.stringify(changed)},'hit')`);
assert.equal(choose.source,'latest');assert.equal(choose.rows[0].combo,'2-1-4');
const good={race_key:key,snapshot_window:'FINAL_15M',minutes_to_deadline:2,guards:{results_seen:false,unlock:false,scoring:false},modes:Object.fromEntries(Object.entries(old).map(([k,v])=>[k,{tickets:v}]))};
assert.equal(fn(`be181ValidFinal(${JSON.stringify(good)},'${key}')`),true);
const no={...good,minutes_to_deadline:-1};assert.equal(fn(`be181ValidFinal(${JSON.stringify(no)},'${key}')`),false);
const resultBad={...good,guards:{results_seen:true,unlock:false,scoring:false}};assert.equal(fn(`be181ValidFinal(${JSON.stringify(resultBad)},'${key}')`),false);
choose=fn(`be181ShowChoice(${JSON.stringify(key)},-3,false,${JSON.stringify(good)},${JSON.stringify(kept)},${JSON.stringify(changed)},'hit')`);
assert.equal(choose.source,'final');assert.equal(choose.rows[0].combo,'1-2-3');
choose=fn(`be181ShowChoice(${JSON.stringify(key)},-3,true,null,${JSON.stringify(kept)},${JSON.stringify(changed)},'hit')`);
assert.equal(choose.source,'unavailable');assert.equal(choose.rows.length,0);
const later=fn(`be181First('20261010-02-01',${JSON.stringify(old)},-1,false)`);assert.equal(later,null);
console.log('V181_IMMUTABLE_FIRST_LATEST_SWITCH_FINAL_ONLY_NEGATIVE_TESTS_PASS');
''')
    proc=subprocess.run(['node','test.cjs'],cwd=td,text=True,capture_output=True)
    print(v.stdout.strip());print(proc.stdout.strip());
    if proc.returncode: print(proc.stderr);raise SystemExit(1)
    print('V181_PATCH_IDEMPOTENCE_PASS')
