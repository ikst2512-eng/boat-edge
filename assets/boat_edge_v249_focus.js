/* BOAT EDGE V297: race quick-navigation reliability ONLY. No fetch, odds, score,
   scratch, stake, freeze, prediction or result mutation. */
(function(){'use strict';
if(window.BoatEdgeV249)return;
var NAV=[['tickets','買い目'],['racers','6艇比較'],['scenario','展開'],['before','直前']];
function el(s,root){return (root||document).querySelector(s)}
function onceButton(button,fn){button.type='button';button.addEventListener('click',fn)}
var DEST={
 tickets:{tab:'pred',targets:['#be207Top','#be204Overview','#buyBoard','#tab-pred']},
 racers:{tab:'pred',targets:['#tab-pred .be203-cards','#be206Quick','#boats','#tab-pred']},
 scenario:{tab:'scenario',targets:['#scenarioFlow','#scenarioHero','#tab-scenario']},
 before:{tab:'before',targets:['#tab-before .section','#tab-before']}
};
function isVisible(node){return !!(node&&node.getClientRects&&node.getClientRects().length)}
function motion(){return window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'}
function scrollFirst(targets){
 for(var i=0;i<targets.length;i++){
  var target=el(targets[i]);
  if(isVisible(target)){
   target.scrollIntoView({behavior:motion(),block:'start'});
   return true;
  }
 }
 return false;
}
function navigate(to){
 var dest=DEST[to];if(!dest)return false;
 var button=el('#raceTabs [data-tab="'+dest.tab+'"]');if(!button)return false;
 button.click(); // Reuse the existing tab state; never select a different race.
 /* Rendered comparison panels can be absent while source data is loading.
    Look for the first *visible* destination only after the tab activates. */
 window.setTimeout(function(){scrollFirst(dest.targets)},180);
 return true;
}
function build(){
 var host=el('#raceView .race-summary'),title=el('#raceTitle');if(!host||!title)return;
 var node=el('#be249Focus');if(!node){
  node=document.createElement('section');node.id='be249Focus';node.setAttribute('aria-label','選択中レースのクイックナビ');
  var heading=document.createElement('div');heading.className='be249-heading';
  heading.innerHTML='<div><span class="be249-eyebrow">RACE QUICK VIEW</span><br><strong>まず見る4つの情報</strong></div><small>同じレースの表示を切り替え</small>';
  var rail=document.createElement('div');rail.className='be249-anchors';rail.setAttribute('role','group');rail.setAttribute('aria-label','選択中レースの表示切替');
  NAV.forEach(function(item){var b=document.createElement('button');b.dataset.nav=item[0];b.textContent=item[1];onceButton(b,function(){navigate(item[0])});rail.appendChild(b)});
  var stamps=document.createElement('div');stamps.className='be249-evidence';stamps.setAttribute('aria-live','polite');
  var help=document.createElement('p');help.className='be249-interpret';help.textContent='頭予想の的中と3連単Top10の的中は別。表示中の数字・オッズ・締切前固定状態は元の監査を確認してな。';
  node.appendChild(heading);node.appendChild(rail);node.appendChild(stamps);node.appendChild(help);
  var top=el('.summary-top',host);
  if(top)top.insertAdjacentElement('afterend',node);else host.insertBefore(node,host.firstChild);
 }
 return node;
}
/* V337: Only the active race's V223 audit receipt may supply quick-view
   source badges. Never fall back to a previous race or infer a missing value. */
function selectedKey(){
 try{
  var k=String(typeof state==='undefined'?'':state?.race?.race_key||'');
  return /^20\d{6}-\d{2}-\d{2}$/.test(k)?k:'';
 }catch(_){return ''}
}
function receiptFor(key){
 var node=el('#be223Source');
 return key&&node&&!node.hidden&&node.dataset?.raceKey===key?node:null;
}
function statusKind(x){
 return x==='ok'?'verified':x==='stop'?'stop':x==='stale'?'stale':'unknown';
}
function receiptChip(receipt,selector,label){
 var chip=receipt&&el(selector,receipt);
 if(!chip)return [label+'：未取得・未確認','unknown'];
 var value=(chip.textContent||'').trim();
 if(!value)return [label+'：未取得・未確認','unknown'];
 var detail=value.startsWith(label+'：')?value:label+'：'+value;
 return [detail.slice(0,85),statusKind(chip.dataset?.quality)];
}
function sourceStatus(root,receipt){
 if(!receipt)return ['予想固定：選択レースの照合待ち','unknown'];
 var banner=el('.be181-freeze-banner',root),type=banner&&banner.dataset.be181Source;
 if(type==='final')return ['締切前FINAL固定（履歴要確認）','fixed'];
 if(type==='first')return ['FIRST固定（最終とは別）','fixed'];
 if(type==='latest')return ['LATEST：変動する参考予想','changed'];
 if(type==='unavailable')return ['締切前の保存買い目なし','unknown'];
 return ['予想固定の照合待ち','unknown'];
}
function refresh(){
 var node=build();if(!node)return;
 var key=selectedKey(),receipt=receiptFor(key);
 var evidence=el('.be249-evidence',node);
 if(!evidence)return;
 var labels=[
  sourceStatus(el('#raceView'),receipt),
  receiptChip(receipt,'[data-be223-flag="scratch"]','欠場・取消'),
  receiptChip(receipt,'[data-be223-ex="time"]','展示タイム'),
  receiptChip(receipt,'[data-be223-flag="odds"]','3連単オッズ'),
  receiptChip(receipt,'[data-be223-ex="boaters"]','BOATERS'),
  receiptChip(receipt,'[data-be223-ex="biyori"]','競艇日和')
 ];
 var sig=JSON.stringify([key,labels]);
 if(evidence.dataset.signature===sig)return;
 evidence.dataset.signature=sig;
 evidence.replaceChildren();
 labels.forEach(function(pair){
  var span=document.createElement('span');
  span.textContent=pair[0];
  span.dataset.kind=pair[1];
  evidence.appendChild(span);
 });
}
function start(){refresh();window.setInterval(function(){if(!document.hidden)refresh()},3500);document.addEventListener('visibilitychange',function(){if(!document.hidden)refresh()})}
window.BoatEdgeV249={refresh:refresh,navigate:navigate,version:'V337-RACE-SCOPED-EVIDENCE-ONLY'};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
