/* BOAT EDGE V204 — prediction presentation only.
   Never changes forecasts, ranked tickets, odds collection, stake calculations, formal locks, or results. */
(()=>{'use strict';
if(window.BoatEdgeV204)return;
const one=(s,r=document)=>r.querySelector(s);
const textOf=(s,r=document)=>one(s,r)?.textContent?.trim()||'';
const safeKey=v=>/^20\d{6}-\d{2}-\d{2}$/.test(String(v||''));
const yen=v=>Number(v).toLocaleString('ja-JP')+'円';
const digits=s=>{const n=Number(String(s||'').replace(/,/g,''));return Number.isSafeInteger(n)&&n>=0?n:null;};
const parseStake=s=>{const m=String(s||'').match(/現在の参考配分\s*([\d,]+)円/);return m?digits(m[1]):null;};
const parsePayout=s=>{const m=String(s||'').match(/的中時想定払戻\s*([\d,]+)円/);return m?digits(m[1]):null;};
const readRace=()=>{try{return typeof state==='undefined'?null:state?.race||null;}catch(_){return null;}};
const asJst=ts=>{const d=ts?new Date(ts):null;return d&&Number.isFinite(d.getTime())?d.toLocaleTimeString('ja-JP',{timeZone:'Asia/Tokyo',hour:'2-digit',minute:'2-digit'}):'未確認';};
function sourceLabel(p){
 const kind=one('.be181-freeze-banner',p)?.dataset?.be181Source;
 return kind==='final'?'締切前に保存された買い目（固定）':
   kind==='first'?'初回表示時の買い目（固定）':
   kind==='latest'?'最新の参考買い目（変動あり）':
   kind==='unavailable'?'締切前の保存なし・買い目非表示':'表示の保存状態を確認中';
}
function summarize(p){
 const rows=[...p.querySelectorAll('.be108-ticket-list>.be108-ticket')];
 const settled=/結果確定後/.test(textOf('.be140-budget-notice',p));
 const oddsNode=one('.be166-odds-status',p);
 const fresh=!settled&&oddsNode&&!oddsNode.classList.contains('warning')&&/公式取得時点のオッズ/.test(oddsNode.textContent||'');
 const stakes=rows.map(r=>parseStake(textOf('.be140-ticket-money',r)));
 const total=(!settled&&rows.length&&stakes.every(x=>x!==null))?stakes.reduce((a,b)=>a+b,0):null;
 const prices=rows.map(r=>{const m=textOf('small',r).match(/^(\d+(?:\.\d+)?)倍$/);return fresh&&m?Number(m[1]):null;});
 const confirmed=prices.filter(x=>x!==null).length;
 const mid=prices.filter(x=>x!==null&&x>=10&&x<=20).length;
 return {rows,settled,total,confirmed,mid,fresh,odds:oddsNode?.textContent?.trim()||'公式3連単オッズ：取得状態未確認'};
}
function mount(p){
 let top=one('#be204Overview',p);
 if(!top){
   top=document.createElement('section');top.id='be204Overview';top.className='be204-overview';
   top.innerHTML='<div class="be204-kicker">BOAT EDGE V204 / 展開から買い目まで</div><div class="be204-intro"><strong class="be204-scenario"></strong><button type="button" data-be204-tab="scenario">展開を詳しく見る →</button></div><p class="be204-narrative"></p><div class="be204-path"><span>① 展開を確認</span><span>② 予想スタイルを選ぶ</span><span>③ 配分・オッズ・想定払戻</span></div><div class="be204-timing"></div>';
   const anchor=one('.be108-mode-tabs',p)||one('.be108-mode-card',p);
   if(anchor)p.insertBefore(top,anchor);else p.appendChild(top);
 }
 const card=one('.be108-mode-card',p);
 if(!card)return [top,null];
 let bottom=one('#be204Budget',card);
 if(!bottom){
   bottom=document.createElement('section');bottom.id='be204Budget';bottom.className='be204-budget';
   bottom.innerHTML='<div class="be204-budget-title">この予想スタイルの買い目と配分</div><div class="be204-budget-grid"><div><small>表示中の買い目</small><b data-be204="count"></b></div><div><small>参考配分の合計</small><b data-be204="total"></b></div><div><small>確認済みオッズ</small><b data-be204="priced"></b></div></div><div class="be204-priceband"></div><div class="be204-freeze"></div><div class="be204-oddsstamp"></div><p class="be204-footnote"></p>';
   const list=one('.be108-ticket-list',card);if(list)card.insertBefore(bottom,list);else card.appendChild(bottom);
 }
 return [top,bottom];
}
function set(el,value){if(el&&el.textContent!==value)el.textContent=value;}
function decorate(rows,settled,fresh){
 for(const r of rows){
   let box=one('.be204-ticket-finance',r);
   let pending=one('.be204-unverified',r);
   if(settled){
     box?.remove();pending?.remove();
     r.classList.remove('be204-finance-ready','be204-odds-unverified');
     continue;
   }
   const raw=textOf('.be140-ticket-money',r),stake=parseStake(raw),estimate=parsePayout(raw);
   if(!fresh){
     box?.remove();r.classList.remove('be204-finance-ready');r.classList.add('be204-odds-unverified');
     if(!pending){pending=document.createElement('div');pending.className='be204-unverified';r.appendChild(pending);}
     set(pending,(stake!==null?'参考配分 '+yen(stake)+' / ':'')+'公式オッズ確認待ち：想定払戻は表示しません');
     continue;
   }
   pending?.remove();r.classList.remove('be204-odds-unverified');
   if(stake===null||estimate===null){
     box?.remove();r.classList.remove('be204-finance-ready');
     continue;
   }
   if(!box){
     box=document.createElement('div');box.className='be204-ticket-finance';
     box.innerHTML='<div><small>参考配分</small><b data-be204="stake"></b></div><div><small>的中時の想定払戻</small><b data-be204="payout"></b></div>';
     r.appendChild(box);r.classList.add('be204-finance-ready');
   }
   set(one('[data-be204="stake"]',box),yen(stake));
   set(one('[data-be204="payout"]',box),yen(estimate));
 }
}
let drawing=false,lastSignature='';
function sync(){
 if(drawing)return;
 const p=one('#be108PredictionModes'),race=readRace();
 if(!p||!safeKey(race?.race_key))return;
 const s=summarize(p);
 const stage=textOf('#scenarioHero .scenario-main')||'展開の詳細は「展開」タブで確認';
 const stageNote=textOf('#scenarioHero .scenario-sub')||'展開の説明は未取得。取得済みデータだけを表示';
 const formal=Boolean(one('.be118-source.formal',p));
 const source=sourceLabel(p);
 const changed=textOf('.be181-freeze-banner > small',p);
 const stamp=asJst(race?.meta?.updated_at);
 const signature=JSON.stringify([race.race_key,stage,stageNote,formal,source,changed,stamp,s.rows.length,
   s.total,s.confirmed,s.mid,s.settled,s.fresh,s.odds,textOf('.be140-budget-notice',p)]);
 if(signature===lastSignature&&one('#be204Overview',p)&&one('#be204Budget',p)&&
    s.rows.every(r=>s.settled?!one('.be204-ticket-finance',r):!s.fresh?Boolean(one('.be204-unverified',r)):parsePayout(textOf('.be140-ticket-money',r))===null||Boolean(one('.be204-ticket-finance',r))))return;
 drawing=true;
 try{
  const [top,bottom]=mount(p);if(!bottom)return;
  set(one('.be204-scenario',top),stage);
  set(one('.be204-narrative',top),(formal?'正式CURRENT接続：':'サイト参考の展開：')+stageNote);
  set(one('.be204-timing',top),'レースデータ更新 '+stamp+' JST（買い目の保存時刻とは別）');
  set(one('[data-be204="count"]',bottom),s.rows.length+'点');
  set(one('[data-be204="total"]',bottom),s.settled?'当時の保存配分を個別表示':s.total===null?'配分確認待ち':yen(s.total));
  set(one('[data-be204="priced"]',bottom),s.settled?'確定倍率は的中組のみ':s.fresh?s.confirmed+'/'+s.rows.length+'点':'未取得／再確認');
  set(one('.be204-priceband',bottom),s.settled?'確定後にオッズから買い目を再評価しません。':s.fresh?'10〜20倍の買い目：'+s.mid+'点（確認済み倍率のみ・順位への反映なし）':'10〜20倍の該当点数：検証済みオッズ待ち');
  set(one('.be204-freeze',bottom),'買い目表示区分：'+source+(changed?' / '+changed:''));
  set(one('.be204-oddsstamp',bottom),s.odds);
  set(one('.be204-footnote',bottom),s.settled?'購入履歴ではありません。過去の買い目・配分の後付け復元をしません。':'参考配分は1万円を基準にした表示です。想定払戻は「参考配分×取得時点の公式オッズ」であり、確定払戻や利益の保証ではありません。未取得倍率から金額を作りません。');
  decorate(s.rows,s.settled,s.fresh);
  lastSignature=signature;
 }finally{drawing=false;}
}
let scheduled=false;
function schedule(){if(scheduled||drawing)return;scheduled=true;queueMicrotask(()=>{scheduled=false;sync();});}
function init(){
 document.addEventListener('click',event=>{
   const b=event.target.closest?.('#be204Overview [data-be204-tab]');
   if(!b)return;
   const tab=one('#raceTabs [data-tab="scenario"]');if(tab&&typeof tab.click==='function')tab.click();
 });
 const root=one('#tab-pred');
 if(root&&typeof MutationObserver!=='undefined')new MutationObserver(schedule).observe(root,{childList:true,subtree:true});
 const scenario=one('#tab-scenario');
 if(scenario&&typeof MutationObserver!=='undefined')new MutationObserver(schedule).observe(scenario,{childList:true,subtree:true,characterData:true});
 sync();
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)schedule();});
}
window.BoatEdgeV204={parseStake,parsePayout,summarize,sync,sourceLabel};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
