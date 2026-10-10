/* BOAT EDGE V202 — site-only, source-audited, compact race display.
   View existing data only. Never produce/update odds, bets, model predictions or formal gates. */
(function(){
  'use strict';
  const $=s=>document.querySelector(s);
  const esc=x=>String(x===null||x===undefined?'':x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const num=v=>v===null||v===undefined||v===''?null:Number.isFinite(Number(v))?Number(v):null;
  const fmt=(v,d=2)=>num(v)===null?'－':Number(v).toFixed(d);
  const stamp=ts=>{
    const date=ts?new Date(ts):null;
    return date&&Number.isFinite(date.getTime())?date.toLocaleTimeString('ja-JP',{hour:'2-digit',minute:'2-digit',timeZone:'Asia/Tokyo'}):'時刻未確認';
  };
  const validKey=key=>/^20\d{6}-\d{2}-\d{2}$/.test(String(key||''));
  const jstDate=()=>new Date(Date.now()+9*3600000).toISOString().slice(0,10).replaceAll('-','');
  const lastRace={key:'',odds:null,requested:0,seq:0};
  let currentKey='',busy=false,detail=false,latestRace=null,latestPred=null,observer=null;
  const sourceOK=(race,key)=>race?.source_audit?.[key]?.status==='ok' && Boolean(race?.source_audit?.[key]?.fetched_at);
  function deadlineAt(race){
    const key=race?.race_key, hm=race?.meta?.deadline;
    if(!validKey(key)||!/^\d{1,2}:\d{2}$/.test(String(hm||'')))return NaN;
    const d=new Date(`${key.slice(0,4)}-${key.slice(4,6)}-${key.slice(6,8)}T${hm}:00+09:00`);
    return d.getTime();
  }
  function snapshotPhase(ts,race){
    const t=ts?Date.parse(ts):NaN,due=deadlineAt(race);
    if(!Number.isFinite(t))return '取得時刻不明';
    if(Number.isFinite(due)&&t>=due)return '締切後取得・当時の予測には未使用';
    return '締切前取得（予測利用は別証跡）';
  }
  function entryMap(race){
    const arr=race?.beforeinfo?.start_exhibition||[];
    const available=sourceOK(race,'beforeinfo');
    const out={};
    if(available){
      for(const row of arr){
        const lane=String(row?.lane??''),course=num(row?.course);
        if(!/^[1-6]$/.test(lane))continue;
        out[lane]={course:course!==null&&course>=1&&course<=6?course:null,st:row?.st??null,f:row?.exhibition_f===true};
      }
    }
    return out;
  }
  function actualCheck(race){
    const racers=race?.racers||[],a=race?.source_audit?.race_card;
    return a?.status==='ok'&&racers.length===6&&new Set(racers.map(v=>String(v?.registration_no))).size===6;
  }
  function leaderMetric(values,{faster=false,margin=0}={}){
    const finite=values.map(v=>num(v)).filter(x=>x!==null);
    if(finite.length<4)return null;
    finite.sort((a,b)=>faster?a-b:b-a);
    return Math.abs(finite[0]-finite[1])+1e-10>=margin?finite[0]:null;
  }
  function makeRows(race){
    const names=(race?.racers||[]),bf=race?.beforeinfo||{},ok=sourceOK(race,'beforeinfo');
    const obs=sourceOK(race,'original_exhibition')&&Array.isArray(race?.original_exhibition?.boats)?race.original_exhibition:null;
    const labelMap=new Map((obs?.labels||[]).map((n,i)=>[n,i]));
    const rawOE={};for(const b of obs?.boats||[]){const n=Number(b?.lane);if(n>=1&&n<=6)rawOE[n]=b?.values||[];}
    const start=entryMap(race);
    const byEx=new Map((bf.racers||[]).map(x=>[Number(x.lane),x]));
    const savedEntry=new Map((race?.actual_entry||[]).map(x=>[Number(x?.lane),x]));
    const rows=names.map((r,i)=>{
      const lane=Number(r?.lane||i+1),b=byEx.get(lane)||{},e=start[String(lane)]||{},save=savedEntry.get(lane)||{};
      const oe=rawOE[lane]||[],pick=name=>{let idx=labelMap.get(name);return idx===undefined?null:num(oe[idx]);};
      return {lane,name:r?.name||'選手未取得',nationalWin:num(r?.national?.win_rate),nationalQ:num(r?.national?.quinella_rate),national3:num(r?.national?.trio_rate),
        localWin:num(r?.local?.win_rate),localQ:num(r?.local?.quinella_rate),local3:num(r?.local?.trio_rate),motorQ:num(r?.motor?.quinella_rate),motor3:num(r?.motor?.trio_rate),boatQ:num(r?.boat?.quinella_rate),boat3:num(r?.boat?.trio_rate),
        displayTime:num(b.exhibition_time),tilt:num(b.tilt),course:e.course??num(save.course),
        st:e.st??save.exhibition_st_raw??save.exhibition_st??null,exhibitionF:e.f===true||save.exhibition_f===true,
        cachedBeforeinfo:!ok&&(Boolean(b.exhibition_time!==undefined)||Boolean(save.course!==undefined)),
        lap:pick('一周'),turn:pick('まわり足'),straight:pick('直線')};
    });
    const strongest={
      nationalWin:leaderMetric(rows.map(x=>x.nationalWin),{margin:.4}),
      motorQ:leaderMetric(rows.map(x=>x.motorQ),{margin:3}),
      displayTime:ok?leaderMetric(rows.map(x=>x.displayTime),{faster:true,margin:.02}):null,
      lap:leaderMetric(rows.map(x=>x.lap),{faster:true,margin:.08}),
      turn:leaderMetric(rows.map(x=>x.turn),{faster:true,margin:.04}),
      straight:leaderMetric(rows.map(x=>x.straight),{faster:true,margin:.04})
    };
    return {rows,strongest,original:obs};
  }
  function metric(v,best,d=2){
    const x=num(v);
    return `<span class="be202-val ${best!==null&&x!==null&&Math.abs(x-best)<1e-7?'be202-strong':''}">${x===null?'－':esc(x.toFixed(d))}</span>`;
  }
  function displayST(item){
    const raw=String(item.st??'').trim();if(!raw)return '－';
    const x=num(raw);if(x===null)return '－';
    return item.exhibitionF||x<0?`<span class="be202-f">展示F${esc(Math.abs(x).toFixed(2))}</span>`:esc(x.toFixed(2));
  }
  function modelStatus(pred){
    return pred?.mode==='formal'?'正式CURRENT':'サイト参考予想（正式未接続）';
  }
  function sourceChip(race,key,label,has){
    const src=race?.source_audit?.[key]||{},good=sourceOK(race,key)&&has;
    return `<span class="be202-chip ${good?'be202-good':'be202-muted'}">${esc(label)} ${good?'取得済':'未取得'} <small>${good?stamp(src.fetched_at):''}</small></span>`;
  }
  function sourceReport(race,oe,bfRows,starts){
    const card=actualCheck(race),audit=race?.source_audit||{};
    const originalGood=Boolean(oe&&(oe.boats||[]).length>=4);
    const startGood=sourceOK(race,'beforeinfo')&&starts.length>=4;
    const bfGood=sourceOK(race,'beforeinfo')&&bfRows.length>=4;
    const cached=!bfGood&&((race?.beforeinfo?.racers||[]).length>=4||(race?.actual_entry||[]).length>=4);
    return `<div class="be202-chips">${sourceChip(race,'race_card','出走表',card)}${sourceChip(race,'beforeinfo','公式展示',bfGood)}${sourceChip(race,'beforeinfo','展示ST',startGood)}${sourceChip(race,'original_exhibition','オリ展',originalGood)}</div><div class="be202-source-note">公式直前 ${bfGood?`${stamp(audit.beforeinfo?.fetched_at)}／${esc(snapshotPhase(audit.beforeinfo?.fetched_at,race))}`:cached?'保存値はあり・現在の取得時刻は未照合':'未取得'} ・ オリ展 ${originalGood?`${stamp(audit.original_exhibition?.fetched_at)}／${esc(snapshotPhase(audit.original_exhibition?.fetched_at,race))}`:'未取得'}</div>`;
  }
  function html(race,pred,odds){
    const key=race?.race_key||'',{rows,strongest,original}=makeRows(race),bf=race?.beforeinfo||{};
    const bfRows=sourceOK(race,'beforeinfo')?(bf.racers||[]):[];
    const starts=sourceOK(race,'beforeinfo')?(bf.start_exhibition||[]):[];
    const official=actualCheck(race),all=rows.length===6;
    const meta=race?.meta||{},w=sourceOK(race,'beforeinfo')?bf.weather||{}:{};
    const water=[['風速',num(w.wind_speed_ms)===null?'－':`${fmt(w.wind_speed_ms,0)}m/s`],['波高',num(w.wave_cm)===null?'－':`${fmt(w.wave_cm,0)}cm`],['気温',num(w.air_temp_c)===null?'－':`${fmt(w.air_temp_c,0)}℃`],['水温',num(w.water_temp_c)===null?'－':`${fmt(w.water_temp_c,0)}℃`]];
    const model=modelStatus(pred);
    const currentOriginal=original&&sourceOK(race,'original_exhibition');
    const status=official&&all?'出走表6艇登録済み（欠場は別途確認）':'出走可否の再確認が必要';
    const o=odds&&odds.race_key===key&&odds.fetched_at?odds:null;
    const lag=o?Math.max(0,Math.round((Date.now()-new Date(o.fetched_at).getTime())/60000)):null;
    const oddsText=o?`公式3連単オッズ ${stamp(o.fetched_at)}取得${Number.isFinite(lag)&&lag>10?'（10分超・再確認）':''}`:'公式3連単オッズ 未取得・更新待ち';
    const dataRows=rows.map(r=>`<tr><th><span class="be202-boat b${r.lane}">${r.lane}</span> ${esc(r.name)}</th><td>${r.course??'－'}</td><td>${displayST(r)}</td><td>${metric(r.displayTime,strongest.displayTime)}</td><td>${metric(r.lap,strongest.lap)}</td><td>${metric(r.turn,strongest.turn)}</td><td>${metric(r.straight,strongest.straight)}</td><td>${metric(r.nationalWin,strongest.nationalWin)}</td><td>${metric(r.nationalQ,null)}</td><td>${metric(r.national3,null)}</td><td>${metric(r.localWin,null)}</td><td>${metric(r.localQ,null)}</td><td>${metric(r.local3,null)}</td><td>${metric(r.motorQ,strongest.motorQ)}</td><td>${metric(r.motor3,null)}</td><td>${metric(r.boatQ,null)}</td><td>${metric(r.boat3,null)}</td></tr>`).join('');
    const isAfter=Number.isFinite(deadlineAt(race))&&Date.now()>=deadlineAt(race);
    return `<div class="be202-top"><div><div class="be202-kicker">BOAT EDGE / 予想・直前まとめ</div><h3>予想と6艇の直前データ</h3></div><span class="be202-pred-label ${pred?.mode==='formal'?'formal':''}">${esc(model)}</span></div>
      <div class="be202-brief"><strong>${esc(meta.venue||'開催場')} ${esc(meta.race_no??'')}R</strong><span>締切 ${esc(meta.deadline||'－')}</span><span class="${official?'be202-okay':'be202-attention'}">${esc(status)}</span><span>データ ${stamp(meta.updated_at)}</span></div>
      ${!official?'<div class="be202-warning">欠場・取消を含む6艇の出走可否が未確認。買い目は確認するまで購入判断に使わないでください。</div>':''}
      <div class="be202-under"><b>買い目・1万円配分</b><span>上の「予想スタイル」で選択。買い目を直前データで再計算・書換えはしません。</span></div>
      ${sourceReport(race,currentOriginal,bfRows,starts)}
      <div class="be202-water">${water.map(([a,b])=>`<span>${esc(a)} <b>${esc(b)}</b></span>`).join('')}</div>
      <div class="be202-swipe">横にスクロールすると全国・当地・モーター・ボート成績まで確認できます →</div>
      <div class="be202-table-scroll"><table class="be202-table"><thead><tr><th>艇・選手</th><th>展示進入</th><th>展示ST</th><th>展示タイム</th><th>1周</th><th>まわり足</th><th>直線</th><th>全国勝率</th><th>全国2連%</th><th>全国3連%</th><th>当地勝率</th><th>当地2連%</th><th>当地3連%</th><th>M2連%</th><th>M3連%</th><th>B2連%</th><th>B3連%</th></tr></thead><tbody>${dataRows||'<tr><td colspan="17">出走データ未取得</td></tr>'}</tbody></table></div>
      <div class="be202-footer"><span>赤い数字は6艇内で明確に優位な項目。展示進入は本番の実進入確定ではありません。直前の保存値は元データの現在照合がない場合があります。</span><span>${esc(oddsText)}</span></div>
      <div class="be202-buttons"><button type="button" data-be202-tab="before">直前情報を詳しく</button><button type="button" data-be202-tab="scenario">展開を見る</button><button type="button" data-be202-detail="1">${detail?'重複表示を閉じる':'詳細・旧表示を開く'}</button></div>
      ${isAfter?'<div class="be202-after">締切済み。後から取得した展示データは締切前の予想・的中判定には反映しません。</div>':''}`;
  }
  function tab(name){
    const btn=$(`#raceTabs [data-tab="${name}"]`);
    if(btn&&typeof btn.click==='function'){btn.click();return;}
    document.querySelectorAll('#raceTabs [data-tab]').forEach(b=>b.classList.toggle('on',b.dataset.tab===name));
    document.querySelectorAll('.subview').forEach(v=>v.classList.toggle('active',v.id===`tab-${name}`));
  }
  function place(root){
    const modes=$('#be108PredictionModes'),main=$('#be108MainPick');
    if(modes?.parentElement===root)modes.insertAdjacentElement('afterend',$('#be202Essential'));
    else if(main?.parentElement===root)main.insertAdjacentElement('afterend',$('#be202Essential'));
    else if(root.firstChild!==$('#be202Essential'))root.insertBefore($('#be202Essential'),root.firstChild);
  }
  function draw(race,pred){
    if(!validKey(race?.race_key)||!$('#tab-pred'))return;
    latestRace=race;latestPred=pred;
    let root=$('#tab-pred .section.stack');if(!root)return;
    let box=$('#be202Essential');if(!box){box=document.createElement('section');box.id='be202Essential';box.className='be202-essential';root.prepend(box);}
    place(root);
    if(currentKey!==race.race_key){currentKey=race.race_key;lastRace.key=race.race_key;lastRace.odds=null;lastRace.requested=0;}
    const markup=html(race,pred,lastRace.odds);
    if(box.innerHTML!==markup)box.innerHTML=markup;
    document.documentElement.classList.toggle('be202-clean',(race?.racers||[]).length===6);
    document.documentElement.classList.toggle('be202-modes-ready',Boolean($('#be108PredictionModes .be108-ticket-list .be108-ticket')));
    document.documentElement.classList.toggle('be202-expanded',detail);
  }
  async function refreshOdds(key){
    if(!validKey(key)||key.slice(0,8)!==jstDate())return;
    if(lastRace.key===key&&Date.now()-lastRace.requested<25000)return;
    lastRace.key=key;lastRace.requested=Date.now();const seq=++lastRace.seq;
    try{
      const r=await fetch(`./data/site_odds/${key}.json?be202=${Date.now()}`,{cache:'no-store'});
      if(!r.ok)return;
      const json=await r.json();
      if(lastRace.key!==key||seq!==lastRace.seq||json?.race_key!==key)return;
      lastRace.odds=json;
      if(latestRace?.race_key===key)draw(latestRace,latestPred);
    }catch(_){}
  }
  function afterRace(race){
    if(!race?.race_key)return;
    let prediction=null;try{prediction=typeof window.getPrediction==='function'?window.getPrediction(race):null;}catch(_){}
    draw(race,prediction);
    refreshOdds(race.race_key);
    // V108 loads the interactive 1万円 wager modes asynchronously.
    setTimeout(()=>{if(latestRace?.race_key===race.race_key)draw(latestRace,latestPred);},500);
    setTimeout(()=>{if(latestRace?.race_key===race.race_key)draw(latestRace,latestPred);},1500);
  }
  function install(){
    const fn=window.renderRace;
    if(typeof fn!=='function'||fn.__be202Wrapped)return;
    window.renderRace=function(...args){const out=fn.apply(this,args);queueMicrotask(()=>afterRace(args[0]));return out;};
    window.renderRace.__be202Wrapped=true;
  }
  function init(){
    install();
    document.addEventListener('click',e=>{
      const el=e.target.closest?.('#be202Essential button');if(!el)return;
      if(el.dataset.be202Tab){tab(el.dataset.be202Tab);return;}
      if(el.dataset.be202Detail){detail=!detail;if(latestRace)draw(latestRace,latestPred);}
    });
    const mode=$('#be108PredictionModes');
    if(mode){observer=new MutationObserver(()=>{if(latestRace)draw(latestRace,latestPred);});observer.observe(mode,{childList:true});}
    try{if(typeof window.state!=='undefined'&&window.state?.race)afterRace(window.state.race);}catch(_){}
  }
  window.BoatEdgeV202={makeRows,entryMap,sourceOK,deadlineAt,snapshotPhase,leaderMetric,refresh:()=>{try{if(window.state?.race)afterRace(window.state.race);}catch(_){}}};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
