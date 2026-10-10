/* BOAT EDGE V207 — prediction FIRST (BOATERS-inspired independent presentation).
   Presentation only: reads existing, rendered, source-audited bets. NO score, odds,
   stake, result, scratch, snapshot, or formal-lock recalculation or edits. */
(()=>{'use strict';
if(window.BoatEdgeV207)return;
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const valid=k=>/^20\d{6}-\d{2}-\d{2}$/.test(String(k||''));
const race=()=>{try{return typeof state==='undefined'?null:state?.race||null;}catch(_){return null;}};
const str=(s,r=document)=>$(s,r)?.textContent?.trim()||'';
const text=(el,v)=>{if(el&&el.textContent!==String(v))el.textContent=String(v);};
const digit=(s)=>{const x=Number(String(s||'').replace(/,/g,''));return Number.isSafeInteger(x)&&x>=0?x:null;};
const money=x=>x===null?'未確認':Number(x).toLocaleString('ja-JP')+'円';
const lanes=combo=>{const parts=String(combo||'').match(/^([1-6])-([1-6])-([1-6])$/);return parts?parts.slice(1):null;};
let showFive=false,showAll=false,activeKey='',acting=false,queued=false,rendering=false,once=false,lastSig='';
function skeleton(){
 const host=$('#raceView .race-summary');if(!host)return null;
 let box=$('#be207Top');
 if(!box){
  box=document.createElement('section');box.id='be207Top';box.className='be207-top';box.setAttribute('aria-label','3連単予想・買い目');
  box.innerHTML=`<div class="be207-topline"><div><span class="be207-eyebrow">BOAT EDGE</span><strong>3連単の予想</strong></div><span class="be207-version">画面 V208</span></div>
   <div class="be207-condition" role="status"><strong></strong><span></span></div>
   <div class="be207-mode-label">予想スタイル <small>タップで切替</small></div>
   <div class="be207-modes" role="group" aria-label="予想スタイル"></div>
   <div class="be207-explain"><strong>展開</strong><span></span><button type="button" data-be207="scenario">詳しく →</button></div>
   <div class="be207-freeze"></div>
   <div class="be207-listhead"><strong>上位買い目</strong><span>確率順・オッズで順位を変更しません</span></div>
   <div class="be207-bets"></div>
   <div class="be207-actions"><button type="button" data-be207="five">上位5点</button><button type="button" data-be207="all">全買い目を表示</button></div><div class="be208-detail-actions"><button type="button" data-be207="detail">詳しいデータ・監査を開く</button></div>
   <div class="be207-bottom"><div class="be207-budget"></div><div class="be207-odds"></div></div>`;
  const first=$('.summary-top',host);
  if(first)first.insertAdjacentElement('afterend',box);else host.prepend(box);
 }
 return box;
}
function safety(r){
 if($('#be182ScratchStop')?.isConnected)return {kind:'stop',title:'欠場・取消確認中／買い目停止',detail:'出走可否の確認が必要'};
 const s=window.BoatEdgeV205?.sourceStatus?.();
 if(!s)return {kind:'pending',title:'欠場・取消 未照合',detail:'確認状態が取得できません'};
 return s;
}
function modeButtons(p,b){
 const old=$$('.be108-mode-tabs [data-be108-mode]',p);
 const data=old.map(x=>({key:x.dataset.be108Mode,label:x.textContent.trim(),selected:x.classList.contains('on')}));
 const sig=JSON.stringify(data);
 if(b.dataset.sig!==sig){
  b.replaceChildren();
  for(const x of data){
   const btn=document.createElement('button');btn.type='button';btn.dataset.be207Mode=x.key;
   btn.className=x.selected?'on':'';btn.setAttribute('aria-pressed',String(x.selected));
   text(btn,x.label.replace(/^🎯\s*/,''));
   b.append(btn);
  }
  b.dataset.sig=sig;
 }
}
function listRow(row,i,fresh){
 const node=document.createElement('div');node.className='be207-ticket';
 const v=str('b',row),nums=lanes(v),prob=str('em',row),label=str('small',row);
 const raw=str('.be140-ticket-money',row),stake=window.BoatEdgeV204?.parseStake?.(raw)??null;
 const payout=window.BoatEdgeV204?.parsePayout?.(raw)??null;
 const actual=str('.be204-ticket-finance [data-be204="payout"]',row);
 const odds=fresh&&/^\d+(?:\.\d+)?倍$/.test(label)?label:'倍率未確認';
 node.innerHTML='<span class="be207-rank"></span><div class="be207-combo"></div><span class="be207-prob"></span><span class="be207-multi"></span><div class="be207-moneys"><span class="be207-stake"></span><span class="be207-pay"></span></div>';
 text($('.be207-rank',node),i+1);
 const combo=$('.be207-combo',node);
 if(nums){for(const n of nums){const chip=document.createElement('span');chip.className='be207-lane be207-l'+n;chip.textContent=n;combo.append(chip);}}
 else text(combo,v||'買い目未取得');
 text($('.be207-prob',node),prob?(prob+' 予測'):'確率未取得');
 text($('.be207-multi',node),odds);
 text($('.be207-stake',node),stake!==null?'配分 '+money(stake):'配分未確認');
 text($('.be207-pay',node),fresh&&payout!==null&&actual?'想定 '+actual:'想定払戻 未確認');
 return node;
}
function render(){
 if(rendering)return;
 const r=race(),p=$('#be108PredictionModes'),v=$('#raceView');
 if(!valid(r?.race_key)||!p||!v||!window.BoatEdgeV204?.summarize){
  $('#be207Top')?.remove();document.documentElement.classList.remove('be207-ready');return;
 }
 const key=r.race_key,st=safety(r),sum=window.BoatEdgeV204.summarize(p),settled=sum.settled;
 if(key!==activeKey){activeKey=key;showFive=false;showAll=false;document.documentElement.classList.remove('be208-details-on');lastSig='';}
 const rows=$$('.be108-ticket-list > .be108-ticket',p);
 const mode=$('.be108-mode-tabs .on',p)?.dataset.be108Mode||'unknown';
 const stage=str('#scenarioHero .scenario-main')||'展開説明は現在確認できません';
 const freeze=window.BoatEdgeV204.sourceLabel?.(p)||'買い目保存状態未確認';
 const fresh=Boolean(sum.fresh&&!settled);
 const sig=JSON.stringify([key,mode,st.kind,st.title,st.detail,rows.length,showFive,showAll,fresh,settled,
  str('#be204Budget [data-be204="total"]',p),str('.be166-odds-status',p),stage,freeze,
  rows.map(x=>[str('b',x),str('em',x),str('small',x),str('.be140-ticket-money',x),str('.be204-ticket-finance',x)])]);
 const box=skeleton();if(!box)return;
 if(sig===lastSig&&box.classList.contains('ready'))return;
 rendering=true;
 try{
  const stop=st.kind==='stop'||!rows.length;
  box.classList.add('ready');box.dataset.status=st.kind;
  text($('.be207-condition strong',box),st.title||'欠場・取消確認待ち');
  text($('.be207-condition span',box),st.detail||'出走可否未確定');
  modeButtons(p,$('.be207-modes',box));
  text($('.be207-explain span',box),stage);
  text($('.be207-freeze',box),'買い目：'+freeze+(settled?'／結果確定後の保存表示':''));
  const list=$('.be207-bets',box);list.replaceChildren();
  const count=showAll?rows.length:showFive?5:3;
  if(stop){const w=document.createElement('div');w.className='be207-stop';w.textContent=rows.length?'出走可否の確認が必要なため、買い目の表示を停止中です。':'買い目を表示できません。直前データ・欠場情報を確認してください。';list.append(w);}
  else rows.slice(0,count).forEach((row,i)=>list.append(listRow(row,i,fresh)));
  const five=$('[data-be207="five"]',box);five.hidden=stop||rows.length<=3||showAll;
  text(five,showFive?'上位3点に戻す':'上位5点を見る');
  const all=$('[data-be207="all"]',box);all.hidden=stop;
  text(all,showAll?'上位3点に戻す':'全買い目を表示');
  const total=str('#be204Budget [data-be204="total"]',p);
  text($('.be207-budget',box),'参考配分合計 '+(total||'未確認')+(rows.length?' ／ 全'+rows.length+'点':''));
  text($('.be207-odds',box),fresh?'公式オッズ取得確認済み（表示時点）': '公式オッズ未確認・想定払戻は非表示');
  document.documentElement.classList.add('be207-ready');
  const brand=$('.brandtext small');
  if(brand&&/^(?:v\d+|サイトV20[3456])$/i.test(brand.textContent.trim()))text(brand,'サイトV208');
  lastSig=sig;
 }finally{rendering=false;}
}
function schedule(){if(queued||rendering)return;queued=true;queueMicrotask(()=>{queued=false;render();});}
function init(){if(once)return;once=true;
 document.addEventListener('click',e=>{
  const btn=e.target.closest?.('#be207Top button');if(!btn)return;
  if(btn.dataset.be207Mode){
   const target=$(`#be108PredictionModes .be108-mode-tabs [data-be108-mode="${btn.dataset.be207Mode}"]`);
   target?.click();schedule();return;
  }
  const command=btn.dataset.be207;
  if(command==='five'){showFive=!showFive;lastSig='';render();return;}
  if(command==='scenario'){$('#raceTabs [data-tab="scenario"]')?.click();return;}
  if(command==='all'){showAll=!showAll;showFive=false;lastSig='';render();return;}
  if(command==='detail'){
   const expanded=document.documentElement.classList.toggle('be208-details-on');
   text(btn,expanded?'詳しいデータ・監査を閉じる':'詳しいデータ・監査を開く');
   return;
  }
 });
 const source=$('#tab-pred'),scenario=$('#tab-scenario');
 if(source&&typeof MutationObserver!=='undefined')new MutationObserver(schedule).observe(source,{childList:true,subtree:true,characterData:true});
 if(scenario&&typeof MutationObserver!=='undefined')new MutationObserver(schedule).observe(scenario,{childList:true,subtree:true,characterData:true});
 setInterval(()=>{if(!document.hidden)render();},3500);
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)schedule();});
 render();
}
window.BoatEdgeV207={render,displayOnly:true,version:'V208-UI'};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
