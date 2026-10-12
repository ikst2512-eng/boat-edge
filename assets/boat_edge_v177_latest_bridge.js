/* BOAT EDGE V177 — formal CURRENT strictly approved bridge and version display.
   Read-only consumer. No prediction weights, rankings, mode counts or frozen snapshots are modified. */
(()=>{'use strict';
 const CONTRACT='boat-edge-formal-approved-overlay-v1';
 const validSha=s=>typeof s==='string'&&/^[a-f0-9]{64}$/i.test(s);
 const combo=s=>typeof s==='string'&&/^[1-6]-[1-6]-[1-6]$/.test(s)&&new Set(s.split('-')).size===3;
 const validTicket=t=>{const c=typeof t==='string'?t:t?.combo||t?.ticket||t?.bet;return combo(c)};
 const worldsOf=d=>{
   if(!d||typeof d!=='object')return [];
   return [d.world_a||d.pattern_a,d.world_b||d.pattern_b].filter(Boolean);
 };
 function contractStatus(status){
   if(!status||status.connected!==true||status.predictions_ready!==true)return false;
   const g=status.guards;
   if(!g||g.results_seen!==false||g.unlock!==false||g.scoring!==false||g.RESULT_UNLOCK_TOKEN!==null)return false;
   return typeof status.active_model_id==='string'&&status.active_model_id.length>=6 &&
     typeof status.target_date==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(status.target_date);
 }
 function approvePayload(derived,meta,key,status){
   if(!/^\d{8}-\d{2}-\d{2}$/.test(String(key||''))||!contractStatus(status))return false;
   if(!meta||meta.schema_version!==CONTRACT||meta.race_key!==key||
     meta.model_id!==status.active_model_id||meta.model_approved!==true||
     meta.formal_gate_pass!==true||meta.scope!=='FORMAL_FRESH_APPROVED_PRE_RESULT')return false;
   if(key.slice(0,8)!==status.target_date.replaceAll('-',''))return false;
   if(!validSha(meta.freeze_sha256)||!validSha(meta.prediction_sha256))return false;
   if(meta.parent_sha256!==status.formalParentSha||!validSha(meta.parent_sha256))return false;
   const g=meta.guards;
   if(!g||g.results_seen!==false||g.unlock!==false||g.scoring!==false||g.RESULT_UNLOCK_TOKEN!==null)return false;
   const worlds=worldsOf(derived);
   if(!worlds.length)return false;
   for(const w of worlds){
     const bets=w.tickets||w.bets||w.combinations;
     if(!Array.isArray(bets)||bets.length===0||bets.length>120)return false;
     const cs=bets.map(t=>typeof t==='string'?t:t?.combo||t?.ticket||t?.bet);
     if(!bets.every(validTicket)||new Set(cs).size!==cs.length)return false;
   }
   return true;
 }
 function acceptRaw(raw,key,status){
   if(!raw||typeof raw!=='object')return false;
   const d=raw.derived||raw.prediction?.derived||raw.prediction||raw;
   const meta=raw.formal_meta||raw.meta;
   return approvePayload(d,meta,key,status);
 }
 function acceptNormalized(race,status){
   return Boolean(race && approvePayload(race.derived,race.formal_meta,race.race_key,status));
 }
 let last='',busy=false, formal=null,model=null,site=null;
 // Read current formal_status.json independently; stale site metadata cannot
 // certify the formal gate or replace the active date.
 function freshness(formalStatus,siteState,now=Date.now()){
   const stamp=formalStatus?.asOf;
   const ms=typeof stamp==='string'?Date.parse(stamp):NaN;
   const age=Number.isFinite(ms)?now-ms:NaN;
   const current=Number.isFinite(age)&&age>=-300000&&age<=1800000;
   const formalLabel=!Number.isFinite(age)?'取得時刻未確認':current?'取得時刻確認済み':'古い・未確認';
   const today=new Date(now).toLocaleDateString('sv-SE',{timeZone:'Asia/Tokyo'});
   const siteDate=typeof siteState?.as_of==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(siteState.as_of)?siteState.as_of:null;
   const siteLabel=!siteDate?'記録日未確認':siteDate<today?'過去の設定記録':'当日の設定記録';
   return {current,formalLabel,formalTime:typeof stamp==='string'?stamp:'未取得',siteLabel,siteDate:siteDate||'未取得'};
 }
 const safe=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function render(){
   const p=document.querySelector('#be108PredictionModes');
   if(!p||busy)return;
   const head=p.querySelector('.be108-head');if(!head)return;
   busy=true;
   try {
     let line=p.querySelector('.be177-model-bridge');
     if(!line){line=document.createElement('div');line.className='be177-model-bridge';head.insertAdjacentElement('afterend',line);}
     const active=p.querySelector('.be118-source.formal')!==null;
     const sitePolicy=site?.latest_prediction_policy?.version||'V127+V133-modes';
     const candidate=model?.model||'未取得';
     const proof=freshness(formal,site);
     const gateVerified=proof.current&&contractStatus(formal);
     const st=active&&gateVerified?`正式CURRENT接続：${safe(formal.active_model_id)}`:
       `サイト参考予想：${safe(sitePolicy)} ／ 正式CURRENT：${gateVerified?'レース別承認待ち':'未接続・未確認'}`;
     const explain=active&&gateVerified?'正式ゲートと承認済みモデルの接続を確認。':
       `検証候補：${safe(candidate)}（参考予想の計算とは別。本番採用を示さない）。`;
     const evidence=`正式状態：${safe(proof.formalLabel)}（${safe(proof.formalTime)}）／ 参考設定：${safe(proof.siteDate)}・${safe(proof.siteLabel)}。正式情報の出典はformal_status.json。`;
     const content=`<b>${st}</b><small>${explain}</small><small>${evidence}</small>`;
     if(content!==last || line.innerHTML!==content){line.innerHTML=content;last=content;}
   }finally{busy=false;}
 }
 async function refresh(){
   const get=async url=>{try{const r=await fetch(url+'?v=177&t='+Date.now(),{cache:'no-store'});return r.ok?await r.json():null;}catch(_){return null;}};
   [formal,model,site]=await Promise.all([
     get('./data/formal_status.json'),get('./data/model_status.json'),get('./data/site_current_state.json')]);
   render();
 }
 function start(){
   if(!document.getElementById('be177-style')){
     const style=document.createElement('style');style.id='be177-style';
     style.textContent='.be177-model-bridge{display:grid;gap:3px;border:1px solid #d5deea;border-radius:10px;padding:10px 12px;margin:8px 0;background:#f6f9ff;color:#1e344e;font-size:12px;line-height:1.5}.be177-model-bridge small{color:#55718e;font-size:11px}';
     document.head.appendChild(style);
   }
   refresh();
   if(typeof MutationObserver!=='undefined')new MutationObserver(()=>{if(!busy)render();}).observe(document.body,{childList:true,subtree:true});
   if(typeof setInterval==='function')setInterval(refresh,60000);
 }
 window.BoatEdgeV177={acceptRaw,acceptNormalized,approvePayload,contractStatus,freshness,refresh,render};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
