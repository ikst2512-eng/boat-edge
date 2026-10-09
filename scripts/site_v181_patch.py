from pathlib import Path
p=Path('assets/boat_edge_v108.js')
s=p.read_text(encoding='utf8')
marker='/* BOAT_EDGE_V181_FIRST_VIEW_IMMUTABLE_AND_FINAL_ONLY */'
if marker in s:
    print('V181_ALREADY_APPLIED')
    raise SystemExit(0)
helpers=r'''/* BOAT_EDGE_V181_FIRST_VIEW_IMMUTABLE_AND_FINAL_ONLY */
const BE181_FIRST_KEY='boatEdgeV181FirstShown:';
const BE181_VIEW_KEY='boatEdgeV181ModeChoice:';
const BE181_STATE=new Map();
const be181KeyValid=k=>/^\d{8}-\d{2}-\d{2}$/.test(String(k||''));
const be181TicketValid=t=>{
  const c=String(t?.combo||'');
  return /^[1-6]-[1-6]-[1-6]$/.test(c)&&new Set(c.split('-')).size===3;
};
function be181ValidModeRows(m){
  return !!m&&typeof m==='object'&&Object.values(m).length===4&&
    ['hit','balance','hole','narrow'].every(k=>Array.isArray(m[k]?.tickets)&&m[k].tickets.length>0&&
      m[k].tickets.every(be181TicketValid));
}
function be181First(key,modes,mins,resultConfirmed){
  if(!be181KeyValid(key))return null;
  const name=BE181_FIRST_KEY+key;
  let first=readLocal(name,null);
  if(first?.schema==='V181_FIRST_SEEN_BEFORE_DEADLINE'&&first.race_key===key&&
      be181ValidModeRows(first.modes))return first;
  if(resultConfirmed||mins===null||mins<0||!be181ValidModeRows(
     Object.fromEntries(Object.entries(modes).map(([k,v])=>[k,{tickets:v}]))) )return null;
  // A once-only snapshot of the FIRST set of picks the browser actually displayed.
  // Do not modify it when new exhibition data, odds, or a later result arrives.
  first={schema:'V181_FIRST_SEEN_BEFORE_DEADLINE',race_key:key,first_seen_at:new Date().toISOString(),
    modes:Object.fromEntries(Object.entries(modes).map(([k,rows])=>[k,{tickets:rows.map(t=>({combo:t.combo,p:t.p}))}]))};
  writeLocal(name,first);
  return first;
}
function be181ValidFinal(s,key){
  if(!s||s.race_key!==key||s.snapshot_window!=='FINAL_15M'||!s.modes||
     !['hit','balance','hole','narrow'].every(k=>Array.isArray(s.modes[k]?.tickets)&&
     s.modes[k].tickets.length&&s.modes[k].tickets.every(be181TicketValid)))return false;
  if(s.guards&&(s.guards.results_seen!==false||s.guards.unlock!==false||s.guards.scoring!==false))return false;
  const m=Number(s.minutes_to_deadline);
  return Number.isFinite(m)&&m>=0&&m<=16;
}
async function be181ServerFinal(key){
  if(!be181KeyValid(key))return null;
  try{
    const r=await fetch(`./data/site_prediction_snapshots/${key}.json?t=${Date.now()}`,{cache:'no-store'});
    if(!r.ok)return null;
    const s=await r.json();
    return be181ValidFinal(s,key)?s:null;
  }catch(_){return null;}
}
function be181ShowChoice(key,mins,resultConfirmed,finalSnap,first,modes,mode){
  const after=resultConfirmed||(mins!==null&&mins<0);
  const now=modes?.[mode]||[];
  const original=first?.modes?.[mode]?.tickets||null;
  const changed=original?JSON.stringify(original.map(x=>x.combo))!==JSON.stringify(now.map(x=>x.combo)):false;
  if(after){
    return {rows:finalSnap?.modes?.[mode]?.tickets||[],source:finalSnap?'final':'unavailable',
      changed,first,finalSnap,selected:'final'};
  }
  let selected=readLocal(BE181_VIEW_KEY+key,'first');
  if(!['first','latest'].includes(selected))selected='first';
  return {rows:selected==='first'&&original?original:now,source:selected==='first'&&original?'first':'latest',
    changed,first,finalSnap,selected};
}
function be181Banner(selection,mode,key,mins,finalSnap){
  const first=selection.first,after=selection.source==='final'||selection.source==='unavailable';
  const fixed=selection.source==='first';
  const title=selection.source==='final'?'締切前の最終保存買い目（固定）':
    selection.source==='unavailable'?'締切前の最終保存なし：現在の買い目は非表示':
    fixed?'初回に見た買い目（固定）':'最新の参考買い目（更新あり）';
  const stamp=selection.source==='final'?(finalSnap?.saved_at||finalSnap?.first_saved_at||'時刻不明'):
    first?.first_seen_at||'初回記録なし';
  const updated=selection.changed?'初回と最新で買い目・順位に変化あり':'初回と最新の買い目・順位は同じ';
  const safe=x=>esc(x);
  const counts=first?.modes?.[mode]?.tickets||[];
  const previous=counts.map(x=>x.combo).join(' / ');
  const buttons=after?'':`<div class="be181-switch"><button type="button" data-be181-choice="first" ${fixed?'disabled':''}>初回の買い目</button><button type="button" data-be181-choice="latest" ${fixed?'':'disabled'}>最新の買い目</button></div>`;
  return `<div class="be181-freeze-banner" data-be181-source="${selection.source}"><b>${title}</b><small>初回/保存の記録：${safe(stamp)} ／ ${safe(updated)}</small>${buttons}`+
     `${first?`<details><summary>初回の${safe(mode)}モード買い目を確認</summary><span>${safe(previous)}</span></details>`:''}`+
     `<small>途中の予想更新と締切前の最終保存は別記録。結果確定後に再計算した買い目は表示・的中判定に使用しません。</small></div>`;
}
'''
needle='async function renderPredictionModes(race,pred){'
assert s.count(needle)==1, 'V181 source mismatch: no renderPredictionModes'
s=s.replace(needle,helpers+'\n'+needle,1)
old='''  const inFinalWindow=!resultConfirmed && mins!==null && mins>=0 && mins<=15;

  let snap=readLocal(snapKey(key));
  if(inFinalWindow)snap=saveFinalSnapshot(key,race,pred,modes,mins);

  const finalSnap=isFinalSnapshot(snap)?snap:null;
  const serverSnap=serverRecord?.snapshot||null;
  const effectiveSnap=resultConfirmed?(serverSnap||finalSnap):finalSnap;
  const settled=resultConfirmed?(serverRecord?.settlement||(finalSnap?settle(finalSnap,result):null)):null;'''
new='''  const inFinalWindow=!resultConfirmed && mins!==null && mins>=0 && mins<=15;
  const firstShown=be181First(key,modes,mins,resultConfirmed);

  let snap=readLocal(snapKey(key));
  if(inFinalWindow)snap=saveFinalSnapshot(key,race,pred,modes,mins);

  const localFinal=be181ValidFinal(snap,key)?snap:null;
  const serverSnap=be181ValidFinal(serverRecord?.snapshot,key)?serverRecord.snapshot:null;
  const serverFinal=(resultConfirmed||(mins!==null&&mins<0))?await be181ServerFinal(key):null;
  const effectiveSnap=serverSnap||serverFinal||localFinal||null;
  const settled=resultConfirmed&&effectiveSnap?(serverSnap&&serverRecord?.settlement?serverRecord.settlement:settle(effectiveSnap,result)):null;'''
assert s.count(old)==1, 'V181 source mismatch: final snapshot block'
s=s.replace(old,new,1)
old='''  const frozenRows=effectiveSnap?.modes?.[mode]?.tickets||null;
  const baseRows=(resultConfirmed&&frozenRows)?frozenRows:modes[mode]||[];'''
new='''  const choice=be181ShowChoice(key,mins,resultConfirmed,effectiveSnap,firstShown,modes,mode);
  const baseRows=choice.rows;'''
assert s.count(old)==1, 'V181 source mismatch: displayed row source'
s=s.replace(old,new,1)
s=s.replace('''  const conf=(resultConfirmed&&effectiveSnap?.modes?.[mode]?.confidence!=null)?effectiveSnap.modes[mode].confidence:confidence(pred,mode,rows);''',
'''  const conf=(choice.source==='final'&&effectiveSnap?.modes?.[mode]?.confidence!=null)?effectiveSnap.modes[mode].confidence:confidence(pred,mode,rows);''',1)
# Missing final may not be represented as old tickets; correctly explain no pre-result stored evidence.
old='''  else if(resultConfirmed&&!effectiveSnap)snapStatus="締切前の最終スナップショットなし・的中判定対象外";
  else if(mins!==null&&mins<0)snapStatus=finalSnap?"締切済み・保存した最終予想を固定中":"締切済み・締切前スナップショットなし";'''
new='''  else if(resultConfirmed&&!effectiveSnap)snapStatus="締切前保存なし・結果を見た後の予想は非表示・判定対象外";
  else if(mins!==null&&mins<0)snapStatus=effectiveSnap?"締切済み・締切前保存の買い目のみ表示":"締切済み・締切前保存なし（当時の買い目は復元しません）";'''
assert s.count(old)==1, 'V181 source mismatch: outdated snap status'
s=s.replace(old,new,1)
old='''<div class="be108-snapshot-status">${snapStatus}</div><div class="be108-mode-tabs">'''
new='''<div class="be108-snapshot-status">${snapStatus}</div>${be181Banner(choice,mode,key,mins,effectiveSnap)}<div class="be108-mode-tabs">'''
assert s.count(old)==1,'V181 source mismatch: panel banner'
s=s.replace(old,new,1)
old='''  $$('[data-be108-mode]',panel).forEach(b=>b.onclick=()=>{localStorage.setItem(ACTIVE_MODE,b.dataset.be108Mode);renderPredictionModes(race,pred)});'''
# current uses double quote in JS
old='''  $$(`[data-be108-mode]`,panel).forEach(b=>b.onclick=()=>{localStorage.setItem(ACTIVE_MODE,b.dataset.be108Mode);renderPredictionModes(race,pred)});'''
if old not in s: old='''  $$("[data-be108-mode]",panel).forEach(b=>b.onclick=()=>{localStorage.setItem(ACTIVE_MODE,b.dataset.be108Mode);renderPredictionModes(race,pred)});'''
assert s.count(old)==1,'V181 source mismatch: modes handlers'
new=old+'''
  $$("[data-be181-choice]",panel).forEach(b=>b.onclick=()=>{
    if(resultConfirmed||(mins!==null&&mins<0))return;
    writeLocal(BE181_VIEW_KEY+key,b.dataset.be181Choice);
    Promise.resolve().then(()=>afterRace(race));
  });'''
s=s.replace(old,new,1)
# Label legacy panels as non-audited live suggestions and hide recomputed post-deadline boxes.
old='''  if(typeof renderBuyBoard==="function")renderBuyBoard(race,adjustedPred);
  if(typeof renderDirectMode==="function")renderDirectMode(race,adjustedPred);'''
new='''  if(typeof renderBuyBoard==="function")renderBuyBoard(race,adjustedPred);
  if(typeof renderDirectMode==="function")renderDirectMode(race,adjustedPred);
  const postDeadline=raceMinutesToDeadline(race)<0;
  const initialMode=readLocal(BE181_VIEW_KEY+race.race_key,'first')!=='latest';
  for(const id of ['buyBoard','directMode','be108MainPick']){
    const el=document.getElementById(id);if(!el)continue;
    // Legacy boards use a separate live recalculation. Never show them beside
    // a frozen-first or a post-deadline result as if they were the same tickets.
    if(postDeadline || (initialMode&&id!=='be108MainPick')){
      el.hidden=true;el.setAttribute('data-be181-historical-hidden','true');
    }else if(el.getAttribute('data-be181-historical-hidden')==='true'){
      el.hidden=false;el.removeAttribute('data-be181-historical-hidden');
    }
  }
  if(!postDeadline&&initialMode){
    const first=readLocal(BE181_FIRST_KEY+race.race_key,null);
    const top=first?.modes?.hit?.tickets?.[0];
    const box=document.getElementById('be108MainPick');
    if(box&&top){
      const combo=box.querySelector('b');if(combo)combo.textContent=top.combo;
      const title=box.querySelector('small');if(title)title.textContent='初回に見た買い目・固定';
      const badge=box.querySelector('em');if(badge)badge.textContent='初回固定';
    }
  }'''
assert s.count(old)==1,'V181 source mismatch: legacy predictions'
s=s.replace(old,new,1)
# to keep layout isolated: style injected into index as a static linkless style, change only original JS
old='''  panel.innerHTML=`${sourceBar}${be166OddsStatus(key,resultConfirmed)}${resultBar}'''
new='''  panel.innerHTML=`${sourceBar}${be166OddsStatus(key,resultConfirmed)}${resultBar}'''
assert s.count(old)==1
# Inject CSS near helper first invocation, via style tag only once
needle='''function be181Banner(selection,mode,key,mins,finalSnap){'''
assert needle in s
s=s.replace(needle,'''function be181InstallStyle(){
  if(document.getElementById('be181-style'))return;
  const st=document.createElement('style');st.id='be181-style';
  st.textContent='.be181-freeze-banner{display:grid;gap:6px;margin:8px 0;padding:12px;background:#fff9e9;border:1px solid #ebca81;border-radius:11px;color:#45361c;font-size:12px;line-height:1.5}.be181-freeze-banner small{display:block;font-size:11px;color:#6b573a}.be181-switch{display:flex;gap:7px}.be181-switch button{flex:1;border:1px solid #ac935f;border-radius:8px;padding:7px;background:white;color:#574016;font-weight:700}.be181-switch button:disabled{background:#e9dfca;opacity:.75}.be181-freeze-banner details span{display:block;padding:7px;font-family:monospace;line-height:1.8}';
  document.head.appendChild(st);
}
'''+needle,1)
needle='''  const choice=be181ShowChoice(key,mins,resultConfirmed,effectiveSnap,firstShown,modes,mode);'''
assert needle in s
s=s.replace(needle,'''  be181InstallStyle();
'''+needle,1)
p.write_text(s,encoding='utf8')
html=Path('index.html')
if html.exists():
    h=html.read_text(encoding='utf8')
    import re
    token=re.compile(r'boat_edge_v108\.js\?v=\d+')
    assert len(token.findall(h))==1, 'V181 index cache-bust source missing'
    h=token.sub('boat_edge_v108.js?v=181',h)
    html.write_text(h,encoding='utf8')

print('V181_PATCH_APPLIED')
