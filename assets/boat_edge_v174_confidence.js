/* BOAT EDGE V174: evidence-based display instead of uncalibrated internal confidence.
   Display only. Frozen predictions, tickets, weights, and formal state are untouched. */
(()=>{'use strict';
 const SCHEMA='boat-edge-v173-frozen-head-tail-diagnostics-v1';
 const SCOPE='SITE_REFERENCE_POST_SETTLEMENT_ONLY_NOT_FORMAL_FRESH';
 const MODES={hit:'的中重視',balance:'バランス',hole:'波乱展開',narrow:'激絞り'};
 const KEYS=Object.keys(MODES);
 let evidence=null,registry=new Map(),lastKey='',working=false;
 const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function validEvidence(d){
   if(!d||d.schema_version!==SCHEMA||d.scope!==SCOPE||d.formal_results_seen!==false||
      d.formal_2026_10_08_touched!==false||d.production_model_weights_changed!==false||
      d.historical_mode!=='RETROSPECTIVE_DIAGNOSTIC_ONLY_NOT_FRESH_VALIDATION'||
      !Number.isInteger(d.eligible_races)||d.eligible_races<=0||!d.all||
      d.all.races!==d.eligible_races||!Array.isArray(d.distinct_dates)||!d.distinct_dates.length)return false;
   return KEYS.every(k=>Number.isInteger(d.all['wins_'+k])&&d.all['wins_'+k]>=0&&d.all['wins_'+k]<=d.eligible_races);
 }
 function auditRate(d,mode){
   if(!validEvidence(d)||!MODES[mode])return null;
   const hits=d.all['wins_'+mode],n=d.eligible_races;
   return {hits,n,rate:(100*hits/n).toFixed(1),days:d.distinct_dates.length};
 }
 const parseCombo=x=>{const v=String(x??'').match(/[1-6]-[1-6]-[1-6]/);if(!v)return null;
   const a=v[0].split('-');return new Set(a).size===3?v[0]:null;};
 function getHeads(combos){const counts={};for(const combo of combos){const head=combo[0];counts[head]=(counts[head]||0)+1;}return counts;}
 function modeExplain(modes,mode){
   const current=modes?.[mode];if(!Array.isArray(current)||!current.length)return null;
   const count=getHeads(current),n=current.length;
   const ordered=Object.entries(count).sort((a,b)=>Number(b[1])-Number(a[1])||Number(a[0])-Number(b[0]));
   const heads=ordered.map(([k,v])=>k+'号艇 '+v+'点').join(' / ');
   const non1=current.filter(k=>k[0]!=='1').length;
   const hitSet=new Set(modes.hit||[]),common=current.filter(k=>hitSet.has(k)).length;
   return {heads,headTypes:ordered.length,non1,total:n,common,
     explanatory:mode==='hole'?'別頭を優先して拾う方式。高配当を約束するものではありません。':
      mode==='hit'?'展開順位上位から選ぶ方式。頭が複数に分かれる場合があります。':
      mode==='balance'?'上位と別展開を組み合わせる方式です。':'上位の少数買い目です。'};
 }
 function register(key,modes){
   if(!/^\d{8}-\d{2}-\d{2}$/.test(String(key||''))||!modes||typeof modes!=='object')return false;
   const normalized={};for(const k of KEYS){
     const src=modes[k]?.tickets||modes[k]||[];
     if(!Array.isArray(src))return false;
     const result=src.map(x=>parseCombo(typeof x==='string'?x:x?.combo)).filter(Boolean);
     if(new Set(result).size!==result.length)return false;
     normalized[k]=result;
   }
   registry.set(key,normalized);lastKey=key;
   if(registry.size>16)registry.delete(registry.keys().next().value);
   if(typeof setTimeout==='function')setTimeout(render,0);
   return true;
 }
 function render(){
   if(working)return;
   const panel=document.querySelector('#be108PredictionModes');if(!panel)return;
   const label=[...panel.querySelectorAll('.be108-mode-top small')].find(x=>
     /内部信頼度|過去的中率/.test(x.textContent||''));
   if(!label)return;
   working=true;
   try{
     const strong=label.parentElement?.querySelector('strong');if(!strong)return;
     const mode=panel.querySelector('.be108-mode-tabs button.on')?.getAttribute('data-be108-mode')||'hit';
     const formal=!!panel.querySelector('.be118-source.formal');
     const metric=formal?null:auditRate(evidence,mode);
     const name=formal?'正式モデルの的中率未検証':'過去的中率（参考）';
     const score=metric?metric.rate+'%':'－';
     if(label.textContent!==name)label.textContent=name;
     if(strong.textContent!==score)strong.textContent=score;
     let source=panel.querySelector('.be174-evidence-detail');
     if(!source){source=document.createElement('div');source.className='be174-evidence-detail';
       label.parentElement.appendChild(source);}
     const auditText=formal?'サイト参考予想の実績を正式CURRENTへ転用しません。':
       metric?`監査済み ${metric.hits}/${metric.n}R・${metric.days}日分。今回のレース固有の的中確率ではありません。`:
       '監査済みの実績が未取得。内部の高い数値を的中確率として表示しません。';
     if(source.textContent!==auditText)source.textContent=auditText;
     let key=lastKey;try{const active=typeof state!=='undefined'?state.race?.race_key:null;if(active)key=active;}catch(_){/* no global */}
     const info=modeExplain(registry.get(key),mode);
     const top=panel.querySelector('.be108-mode-top');if(!top)return;
     let note=panel.querySelector('.be174-mode-clarity');if(!note){note=document.createElement('div');note.className='be174-mode-clarity';top.insertAdjacentElement('afterend',note);}
     let message;
     if(!info)message='買い目の展開内訳は集計待ちです。';
     else{
       message=`選択中の頭の内訳：${info.heads}（${info.headTypes}種類）。`;
       if(mode==='hole')message+=`非1号艇頭 ${info.non1}/${info.total}点・的中重視と ${info.common}点重複。`;
       else if(mode==='balance'||mode==='narrow')message+=`的中重視と ${info.common}点重複。`;
       message+=info.explanatory+' 「予想の頭が正しい確率」と「3連単の的中率」は別です。';
     }
     if(note.textContent!==message)note.textContent=message;
   }finally{working=false;}
 }
 async function fetchEvidence(){
   try{const r=await fetch('./data/site_learning/v173_head_tail_diagnostic.json?v=174',{cache:'no-store'});
     if(!r.ok)return;
     const d=await r.json();if(validEvidence(d))evidence=d;
   }catch(_){/* no invented rate */}finally{render();}
 }
 function initialize(){
   render();fetchEvidence();
   if(typeof MutationObserver!=='undefined'){
     const obs=new MutationObserver(()=>{
       if(working)return;
       if(typeof requestAnimationFrame==='function')requestAnimationFrame(render);else render();
     });obs.observe(document.body,{childList:true,subtree:true});
   }
 }
 window.BoatEdgeV174={register,validEvidence,auditRate,modeExplain,parseCombo,refresh:fetchEvidence};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize,{once:true});else initialize();
})();
