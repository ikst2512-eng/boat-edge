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
/* V244 A04: only the existing freeze banner can establish a stored FIRST/FINAL state. */
function freezeEvidence(p){
 const banner=one('.be181-freeze-banner',p),kind=banner?.dataset?.be181Source;
 const types={first:'FIRST｜初回保存',final:'FINAL｜締切前保存',latest:'LATEST｜変動する参考予想',unavailable:'保存なし｜買い目を確認できません'};
 const label=Object.prototype.hasOwnProperty.call(types,kind)?types[kind]:'保存状態未確認';
 const detail=textOf('.be181-freeze-banner > small',p);
 return {kind:kind||'unknown',label,detail,locked:kind==='first'||kind==='final'};
}
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
/* V247 A09: reuse only notes already highlighted in the EXISTING scenario diagram. */
function flowStages(){
 const parent=one('#scenarioFlow');
 const steps=parent?[...parent.querySelectorAll('.flow-step')]:[];
 const focus=step=>{
  if(!step)return '展開図の取得待ち';
  const emphasized=[...step.querySelectorAll('.flow-boat.attack,.flow-boat.hot')];
  const items=emphasized.map(b=>{
   const lane=textOf('.n',b),name=textOf('.r',b),role=textOf('.a',b);
   return [lane?/^[1-6]$/.test(lane)?lane+'号艇':lane:'',name,role].filter(Boolean).join('・');
  }).filter(Boolean);
  return items.length?'図の注目艇：'+items.join(' ／ '):'展開図に注目艇の記載なし';
 };
 return [
  {title:'① スタート',value:focus(steps[0])},
  {title:'② 1マークの攻め',value:focus(steps[1])},
  {title:'③ 抜け出し・受益',value:focus(steps[2])},
  {title:'④ 展開の結論',value:textOf('.flow-conclusion .v',parent)||'展開結論の取得待ち'}
 ];
}
/* V248 A16: Top3/5/10 are ordered ticket prefixes, not event probabilities. */
function topKExplanation(rows){
 const tickets=(Array.isArray(rows)?rows:[]).map(r=>{
  const raw=textOf('b',r),match=raw.match(/(?:^|[^0-9])([1-6]-[1-6]-[1-6])(?:$|[^0-9])/);
  if(!match)return null;
  const combo=match[1],lanes=combo.split('-');
  return new Set(lanes).size===3?combo:null;
 });
 const verified=tickets.length&&tickets.every(Boolean)&&new Set(tickets).size===tickets.length;
 const cover=n=>verified&&tickets.length>=n?('上位'+n+'点 '+tickets.slice(0,n).join(' / ')):'保存済み順位の確認待ち';
 return {head:verified?tickets[0][0]+'号艇（Top1買い目の1着）':'未確認（頭予想と別）',
  top3:cover(3),top5:cover(5),top10:cover(10),
  caution:'頭の的中確率：未校正 ／ 3連単の的中確率：未校正。Top3/5/10は買い目順位で、的中率や配当の保証ではありません。保存済みp_raw_percentは上位10点内の配分用相対重みであり、120通りに対する的中確率ではありません。'};
}
/* V250 A17: only the selected race's V223 pre-deadline inspector may certify odds. */
function oddsProof(r){
 const box=one('#be223Source');
 if(!safeKey(r?.race_key)||box?.dataset?.raceKey!==r.race_key)
   return {quality:'unknown',label:'公式3連単オッズ：選択レースの取得証跡を確認中'};
 const rows=[...box.querySelectorAll('.be223-row')];
 const item=rows.find(row=>textOf('span:first-child',row)==='3連単オッズ');
 const detail=item?one('span:last-child',item):null;
 const status=detail?.dataset?.quality;
 const stamp=detail?.textContent?.trim()||'';
 if(status==='ok'&&/^\d{1,2}:\d{2}取得/.test(stamp))
   return {quality:'verified',label:'BOAT RACE公式の保存値｜'+stamp+'（リアルタイムではありません）'};
 if(status==='stale')return {quality:'stale',label:'BOAT RACE公式の保存値｜'+stamp+'（古い取得値・予想用の最新値ではありません）'};
 return {quality:'unknown',label:'公式3連単オッズ：未取得・照合待ち（取得時刻は未確認）'};
}
function mount(p){
 let top=one('#be204Overview',p);
 if(!top){
   top=document.createElement('section');top.id='be204Overview';top.className='be204-overview';
   top.innerHTML='<div class="be204-kicker">BOAT EDGE / 展開から買い目まで</div><div class="be244-freeze-chip" role="status"><strong data-be244="freeze"></strong><span data-be244="freeze-detail"></span></div><div class="be204-intro"><strong class="be204-scenario"></strong><button type="button" data-be204-tab="scenario">展開を詳しく見る →</button></div><p class="be204-narrative"></p><div class="be247-flow" aria-label="既存の展開図から読み取った4段階"><div class="be247-flow-grid"></div><small>図で色が強調された艇と、保存済みの展開説明だけを転記。実際の着順や的中を保証するものではありません。</small></div><div class="be248-tops" role="group" aria-label="予測順位と頭予想を分けて確認"><strong>3連単の上位候補（確率・的中率とは別）</strong><div class="be248-tops-grid"><span data-be248="top3"></span><span data-be248="top5"></span><span data-be248="top10"></span></div><p><b>Top1買い目の1着：</b><span data-be248="head"></span></p><small data-be248="caution"></small></div><div class="be204-path"><span>① 展開を確認</span><span>② 予想スタイルを選ぶ</span><span>③ 配分・オッズ・想定払戻</span></div><div class="be204-timing"></div>';
   const anchor=one('.be108-mode-tabs',p)||one('.be108-mode-card',p);
   if(anchor)p.insertBefore(top,anchor);else p.appendChild(top);
 }
 const card=one('.be108-mode-card',p);
 if(!card)return [top,null];
 let bottom=one('#be204Budget',card);
 if(!bottom){
   bottom=document.createElement('section');bottom.id='be204Budget';bottom.className='be204-budget';
   bottom.innerHTML='<div class="be204-budget-title">この予想スタイルの買い目と配分</div><div class="be204-budget-grid"><div><small>表示中の買い目</small><b data-be204="count"></b></div><div><small>参考配分の合計</small><b data-be204="total"></b></div><div><small>確認済みオッズ</small><b data-be204="priced"></b></div></div><div class="be204-priceband"></div><div class="be204-freeze"></div><div class="be204-oddsstamp"></div><div class="be250-odds-proof" role="status"></div><p class="be204-footnote"></p>';
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
 const freeze=freezeEvidence(p);
 const changed=freeze.detail;
 const stamp=asJst(race?.meta?.updated_at);
 const flow=flowStages();
 const ranking=topKExplanation(s.rows);
 const odds=oddsProof(race);
 const signature=JSON.stringify([race.race_key,stage,stageNote,formal,source,changed,stamp,s.rows.length,
   s.total,s.confirmed,s.mid,s.settled,s.fresh,s.odds,odds,flow.map(x=>x.value),ranking,textOf('.be140-budget-notice',p)]);
 if(signature===lastSignature&&one('#be204Overview',p)&&one('#be204Budget',p)&&
    s.rows.every(r=>s.settled?!one('.be204-ticket-finance',r):!s.fresh?Boolean(one('.be204-unverified',r)):parsePayout(textOf('.be140-ticket-money',r))===null||Boolean(one('.be204-ticket-finance',r))))return;
 drawing=true;
 try{
  const [top,bottom]=mount(p);if(!bottom)return;
  const chip=one('.be244-freeze-chip',top);
  if(chip)chip.dataset.freeze=freeze.kind;
  set(one('[data-be244="freeze"]',top),freeze.label);
  set(one('[data-be244="freeze-detail"]',top),freeze.detail||'保存時刻・証跡は未確認');
  set(one('.be204-scenario',top),stage);
  set(one('.be204-narrative',top),(formal?'正式CURRENT接続：':'サイト参考の展開：')+stageNote);
  for(const key of ['top3','top5','top10','head','caution'])
    set(one('[data-be248="'+key+'"]',top),ranking[key]);
  const flowGrid=one('.be247-flow-grid',top);
  if(flowGrid&&flowGrid.children.length!==flow.length){
   flowGrid.replaceChildren();
   for(let i=0;i<flow.length;i++){
    const item=document.createElement('div'),strong=document.createElement('strong'),description=document.createElement('span');
    item.className='be247-flow-item';strong.textContent=flow[i].title;
    description.dataset.be247Stage=String(i);item.append(strong,description);flowGrid.append(item);
   }
  }
  flow.forEach((x,i)=>set(one('[data-be247-stage="'+i+'"]',flowGrid),x.value));
  set(one('.be204-timing',top),'レースデータ更新 '+stamp+' JST（買い目の保存時刻とは別）');
  set(one('[data-be204="count"]',bottom),s.rows.length+'点');
  set(one('[data-be204="total"]',bottom),s.settled?'当時の保存配分を個別表示':s.total===null?'配分確認待ち':yen(s.total));
  set(one('[data-be204="priced"]',bottom),s.settled?'確定倍率は的中組のみ':s.fresh?s.confirmed+'/'+s.rows.length+'点':'未取得／再確認');
  set(one('.be204-priceband',bottom),s.settled?'確定後にオッズから買い目を再評価しません。':s.fresh?'10〜20倍の買い目：'+s.mid+'点（確認済み倍率のみ・順位への反映なし）':'10〜20倍の該当点数：検証済みオッズ待ち');
  set(one('.be204-freeze',bottom),'買い目表示区分：'+source+(changed?' / '+changed:''));
  set(one('.be204-oddsstamp',bottom),s.odds);
  const oddNode=one('.be250-odds-proof',bottom);
  if(oddNode){oddNode.dataset.quality=odds.quality;set(oddNode,odds.label);}
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
 setInterval(()=>{if(!document.hidden)sync();},10000);
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)schedule();});
}
window.BoatEdgeV204={parseStake,parsePayout,summarize,sync,sourceLabel,freezeEvidence,flowStages,topKExplanation,oddsProof};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
