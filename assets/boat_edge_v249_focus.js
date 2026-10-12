/* BOAT EDGE V249: navigational enhancement ONLY. No fetch, odds, score,
   scratch, stake, freeze, prediction or result mutation. */
(function(){'use strict';
if(window.BoatEdgeV249)return;
var NAV=[['tickets','買い目'],['racers','6艇比較'],['scenario','展開'],['before','直前']];
function el(s,root){return (root||document).querySelector(s)}
function text(s,root){var n=el(s,root);return n?(n.textContent||'').trim():''}
function onceButton(button,fn){button.type='button';button.addEventListener('click',fn)}
function tab(name,focus){
 var button=el('#raceTabs [data-tab="'+name+'"]');if(!button)return false;
 button.click();
 /* The legacy tab handler scrolls the view to the top; our scroll runs afterward. */
 window.setTimeout(function(){var target=el(focus);if(target&&target.getClientRects().length)target.scrollIntoView({behavior:'smooth',block:'start'});},160);
 return true;
}
function navigate(to){
 if(to==='tickets'){if(!tab('pred','#be207Top'))tab('pred','#tab-pred');return}
 if(to==='racers'){if(!tab('pred','#tab-pred .be203-cards'))tab('pred','#boats');return}
 if(to==='scenario'){tab('scenario','#scenarioFlow');return}
 if(to==='before'){tab('before','#tab-before .section');return}
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
function sourceStatus(root){
 var banner=el('.be181-freeze-banner',root),type=banner&&banner.dataset.be181Source;
 if(type==='final')return ['締切前FINAL固定','fixed'];
 if(type==='first')return ['FIRST固定（最終とは別）','fixed'];
 if(type==='latest')return ['LATEST：変動する参考予想','changed'];
 if(type==='unavailable')return ['締切前の保存買い目なし','unknown'];
 return ['予想固定の照合待ち','unknown'];
}
function auditStatus(){
 var scratch=el('.be205-scratch strong')||el('#be182ScratchStop');
 var x=scratch?(scratch.textContent||'').trim():'';
 if(!x)return '欠場・取消：状態未確認';
 return '欠場・取消：'+x.slice(0,50);
}
function refresh(){
 var node=build();if(!node)return;
 var source=sourceStatus(el('#raceView'));
 var evidence=el('.be249-evidence',node);
 if(!evidence)return;
 var labels=[[source[0],source[1]],[auditStatus(),'unknown'],['オッズは元の取得時刻表示を確認','unknown']];
 var sig=JSON.stringify(labels);
 if(evidence.dataset.signature===sig)return;
 evidence.dataset.signature=sig;
 evidence.replaceChildren();
 labels.forEach(function(pair){var span=document.createElement('span');span.textContent=pair[0];span.dataset.kind=pair[1];evidence.appendChild(span)});
}
function start(){refresh();window.setInterval(function(){if(!document.hidden)refresh()},3500);document.addEventListener('visibilitychange',function(){if(!document.hidden)refresh()})}
window.BoatEdgeV249={refresh:refresh,version:'V249-DISPLAY-ONLY'};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
