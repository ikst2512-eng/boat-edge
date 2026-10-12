/* BOAT EDGE V253: home list presentation only, no race-selection or feed mutation. */
(function(root){
'use strict';
if(typeof document==='undefined'||typeof window==='undefined')return;
if(window.BoatEdgeV253)return;
let expanded=false;
function find(s){return document.querySelector(s)}
function setup(){
 const home=find('#homeView'),list=find('#deadlineBoard');
 if(!home||!list)return;
 if(find('#be253ShowDeadlines'))return;
 const button=document.createElement('button');
 button.type='button';button.id='be253ShowDeadlines';button.className='be253-more';
 button.setAttribute('aria-controls','deadlineBoard');
 button.setAttribute('aria-expanded','false');
 button.textContent='残りの締切予定を見る';
 const where=list.parentElement;
 if(where)list.insertAdjacentElement('afterend',button);
 button.addEventListener('click',()=>{
  expanded=!expanded;update();
  if(expanded)list.scrollIntoView({behavior:'smooth',block:'start'});
 });
 const q=find('#venueSearch');
 if(q){q.setAttribute('aria-label','会場名・場コードを検索');}
}
function update(){
 const home=find('#homeView'),list=find('#deadlineBoard'),button=find('#be253ShowDeadlines');
 if(!home||!list)return;
 if(!button){setup();return;}
 const n=list.querySelectorAll('.deadline-card').length;
 home.classList.toggle('be253-compact',!expanded&&n>6);
 home.classList.toggle('be253-expanded',expanded);
 button.hidden=n<=6;
 button.setAttribute('aria-expanded',String(expanded));
 button.textContent=expanded?'締切順を6Rに戻す':'残り'+Math.max(0,n-6)+'Rの締切予定を見る';
 const header=find('#deadlineCount');
 if(header){
  if(n>6&&!expanded)button.title='全'+n+'レースの締切情報を表示';
  else button.title='締切順一覧';
 }
}
function start(){
 setup();update();
 window.setInterval(()=>{if(!document.hidden)update()},3000);
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)update()});
}
window.BoatEdgeV253={update,version:'V253-HOME-DISPLAY-ONLY'};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})(typeof window!=='undefined'?window:{});
