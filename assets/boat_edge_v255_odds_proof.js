/* BOAT EDGE V255: race-bound official 3連単 odds evidence alongside tickets.
 * Read only V223 independently saved source-state. Does NOT certify odds
 * numeric parity, fetch odds, rerank predictions, or change frozen bets. */
(function(root){
'use strict';
const KEY=/^20\d{6}-\d{2}-\d{2}$/;
function deriveEvidence(audit,key){
 const unknown={quality:'unknown',label:'公式3連単オッズ：取得時刻・照合状態は未確認。ページ更新では新規オッズを収集しません。'};
 if(typeof key!=='string'||!KEY.test(key)||!audit||audit.dataset?.raceKey!==key)return unknown;
 const rows=[...audit.querySelectorAll('.be223-row')];
 const row=rows.find(x=>x.querySelector('span:first-child')?.textContent?.trim()==='3連単オッズ');
 const detail=row?.querySelector('span:last-child');
 if(!detail)return unknown;
 const status=detail.dataset?.quality||'unknown';
 const stamp=detail.textContent?.trim()||'';
 if(status==='ok'&&/^\d{1,2}:\d{2}取得/.test(stamp)&&stamp.length<=160)
  return {quality:'logged',label:'BOAT RACE公式オッズ｜'+stamp+'｜取得記録あり・数値一致や現時点の最新値は別確認'};
 if(status==='stale'&&stamp.length>0&&stamp.length<=160)
  return {quality:'stale',label:'古い公式オッズ取得記録｜'+stamp+'｜現在値・購入用の最新値ではありません'};
 return unknown;
}
if(typeof module!=='undefined'&&module.exports)module.exports={deriveEvidence};
if(typeof document==='undefined'||typeof window==='undefined')return;
if(window.BoatEdgeV255)return;
let last='';
const find=s=>document.querySelector(s);
function selectedKey(){try{return typeof state==='undefined'?null:state?.race?.race_key}catch(_){return null}}
function render(){
 const top=find('#be207Top'),rootView=find('#raceView');
 if(!top||!rootView?.classList.contains('active')||!KEY.test(String(selectedKey()||'')))return;
 let node=find('#be255OddsProof');
 if(!node){
  node=document.createElement('div');node.id='be255OddsProof';node.className='be255-odds-proof';
  node.setAttribute('role','status');
  node.setAttribute('aria-label','選択中レースの公式オッズ取得証跡');
  const footer=top.querySelector('.be207-bottom');
  if(footer)footer.insertAdjacentElement('beforebegin',node);else top.appendChild(node);
 }
 const proof=deriveEvidence(find('#be223Source'),selectedKey());
 const signature=JSON.stringify([selectedKey(),proof.quality,proof.label]);
 if(signature!==last){
  last=signature;
  node.dataset.quality=proof.quality;
  node.textContent=proof.label;
 }
 top.classList.add('be255-odds-mounted');
}
function start(){
 render();
 window.setInterval(()=>{if(!document.hidden)render()},2700);
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)render()});
}
window.BoatEdgeV255={refresh:render,version:'V255-RACE-BOUND-ODDS-SOURCE-NOT-REALTIME'};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})(typeof window!=='undefined'?window:{});
