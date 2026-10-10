/* BOAT EDGE V205 — site presentation only. No odds, model, tickets, stakes, results, or formal reads. */
(()=>{'use strict';
if(window.BoatEdgeV205)return;
const $=(s,r=document)=>r.querySelector(s);
const safeKey=k=>/^20\d{6}-\d{2}-\d{2}$/.test(String(k||''));
const race=()=>{try{return typeof state==='undefined'?null:state?.race??null;}catch(_){return null;}};
let expanded=false,working=false,queued=false,initiated=false;
function set(el,txt){if(el&&el.textContent!==txt)el.textContent=txt;}
function sourceStatus(){
 const stop=$('#be182ScratchStop');
 if(stop?.isConnected)return {kind:'stop',title:'買い目停止・出走可否の確認が必要',detail:stop.textContent?.trim()||'欠場・取消の確認が必要です'};
 const current=race();
 const verified=window.BoatEdgeV203?.scratchHint?.(current);
 if(verified&&['stop','pending','partial'].includes(verified.type))return {kind:verified.type,title:verified.label||'欠場・取消：確認待ち',detail:verified.description||'出走可否の確認状態は未確定'};
 const health=$('#be203Layout .be203-health');
 if(!health)return {kind:'pending',title:'欠場・取消：確認待ち',detail:'直前の照合状態を表示できません。購入判断には使用しないでください'};
 const title=$('strong',health)?.textContent?.trim()||'欠場・取消：確認待ち';
 const detail=$('span',health)?.textContent?.trim()||'出走可否の確認状態は未確定';
 const kind=health.classList.contains('be203-stop')?'stop':health.classList.contains('be203-partial')?'partial':'pending';
 return {kind,title,detail};
}
function install(){
 if(working)return;
 const r=race(),panel=$('#be108PredictionModes'),overview=$('#be204Overview'),before=$('#be203Layout');
 if(!safeKey(r?.race_key)||!panel||!overview||!before){document.documentElement.classList.remove('be205-clean','be205-expanded');return;}
 working=true;
 try{
   let bar=$('#be205Actions',panel);
   if(!bar){
     bar=document.createElement('div');bar.id='be205Actions';bar.className='be205-actions';
     bar.innerHTML='<span>予想画面 · サイトV205</span><button type="button" data-be205="expand" aria-expanded="false">詳細表示</button>';
     overview.insertAdjacentElement('beforebegin',bar);
   }
   const button=$('[data-be205="expand"]',bar);
   if(button){set(button,expanded?'すっきり表示':'詳細表示');button.setAttribute('aria-expanded',String(expanded));}
   let notice=$('#be205Scratch',panel);
   if(!notice){notice=document.createElement('div');notice.id='be205Scratch';notice.className='be205-scratch';notice.setAttribute('role','status');
     notice.innerHTML='<strong></strong><span></span>';overview.insertAdjacentElement('beforebegin',notice);}
   const status=sourceStatus();if(notice.dataset.state!==status.kind)notice.dataset.state=status.kind;
   set($('strong',notice),status.title);
   set($('span',notice),status.detail+(status.kind==='partial'?'。出走確定・購入安全の保証ではありません':'。確認完了までは購入判断を保留してください'));
   document.documentElement.classList.add('be205-clean');
   document.documentElement.classList.toggle('be205-expanded',expanded);
   const small=$('.brandtext small');
   if(small&&/^v\d+$/i.test(small.textContent.trim()))small.textContent='サイトV205';
 }finally{working=false;}
}
function change(){
 expanded=!expanded;
 document.documentElement.classList.toggle('be205-expanded',expanded);
 // Retain the V202 author's own expanded/collapsed state for old chart details.
 const legacy=$('#be202Essential [data-be202-detail]');
 const oldOpen=document.documentElement.classList.contains('be202-expanded');
 if(legacy&&expanded!==oldOpen)legacy.click();
 install();
}
function schedule(){if(working||queued)return;queued=true;queueMicrotask(()=>{queued=false;install();});}
function init(){
 if(initiated)return;initiated=true;
 document.addEventListener('click',e=>{if(e.target.closest?.('#be205Actions [data-be205="expand"]'))change();});
 const pred=$('#tab-pred');
 if(pred&&typeof MutationObserver!=='undefined')new MutationObserver(schedule).observe(pred,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['class']});
 install();
 setInterval(()=>{if(!document.hidden)install();},5000);
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)schedule();});
}
window.BoatEdgeV205={sourceStatus,install,change};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
