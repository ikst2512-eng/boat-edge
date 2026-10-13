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
/* A24: rank-prefix ticket coverage is NOT the probability of head or trifecta.
 * Accept only the original already-rendered list. No odds/results/API reads. */
const extractCombo=v=>{
 const m=String(v||'').match(/(?:^|[^0-9])([1-6]-[1-6]-[1-6])(?:$|[^0-9])/);
 return m&&lanes(m[1])&&new Set(lanes(m[1])).size===3?m[1]:null;
};
function ticketClarity(combos,displayAllowed=true){
 const unknown={head:'未確認',top3:'未確認',top5:'未確認',top10:'未確認',
  confidenceHead:'未校正・個別の1着確率は未提供',
  confidenceTrifecta:'未校正・3連単の的中確率は未提供'};
 if(!displayAllowed||!Array.isArray(combos)||!combos.length)return unknown;
 const parsed=combos.map(extractCombo);
 if(parsed.some(v=>!v)||new Set(parsed).size!==parsed.length)return unknown;
 const top=n=>parsed.length>=n?('上位'+n+'点／'+parsed.slice(0,n).join(' · ')):'上位'+n+'点の保存順位は未確認';
 return {...unknown,head:parsed[0][0]+'号艇（Top1券の1着）',
  top3:top(3),top5:top(5),top10:top(10)};
}
/* V304: display amounts only when the original row explicitly records the
 * correct reference/frozen stake kind. No allocation or payout calculation. */
function shownStake(row,settled){
 const raw=str('.be140-ticket-money',row);
 const view=row?.dataset?.be257View||'';
 if(settled){
  if(view!=='frozen')return null;
  const m=raw.match(/締切前の保存配分\s*([\d,]+)円/);
  return m?digit(m[1]):null;
 }
 if(view!=='reference')return null;
 const m=raw.match(/現在の参考配分\s*([\d,]+)円/);
 return m?digit(m[1]):null;
}
function validTickets(rows){
 if(!Array.isArray(rows)||rows.length===0||rows.length>120)return false;
 const combos=rows.map(row=>extractCombo(str('b',row)));
 return combos.every(Boolean)&&new Set(combos).size===combos.length;
}

/* V305: selected-race V223 DOM is the ONLY display source. Provider receipts
   are independent audit statuses, not inferred numeric parity or predictions. */
function evidenceFor(key){
 const source=$('#be223Source');
 if(!valid(key)||source?.dataset?.raceKey!==key)
  return {ready:false,items:[{label:'選択レースの直前データ',quality:'unknown',text:'照合待ち'}]};
 const ids=[['展示タイム','time'],['オリ展CSV','original'],['BOATERS','boaters'],['競艇日和','biyori']];
 return {ready:true,items:ids.map(([label,id])=>{
  const chip=$('[data-be223-ex="'+id+'"]',source);
  const quality=chip?.dataset?.quality||'unknown';
  return {label,quality:['ok','limited','stop','wait','stale','unknown'].includes(quality)?quality:'unknown',
    text:chip?.textContent?.trim()||'未取得・未確認'};
 })};
}

let showFive=false,showTen=false,showAll=false,activeKey='',acting=false,queued=false,rendering=false,once=false,lastSig='';
/* Reset at a race change only when the ranked list is actually new. */
const holdPreviousRace=(previousKey,currentKey,previousList,nextList)=>
 Boolean(previousKey)&&previousKey!==currentKey&&(!nextList||nextList===previousList);
let lastListNode=null,awaitingRaceList=false;
function skeleton(){
 const host=$('#raceView .race-summary');if(!host)return null;
 let box=$('#be207Top');
 if(!box){
  box=document.createElement('section');box.id='be207Top';box.className='be207-top';box.setAttribute('aria-label','3連単予想・買い目');
  box.innerHTML=`<div class="be207-topline"><div><span class="be207-eyebrow">BOAT EDGE</span><strong>3連単の予想</strong></div><span class="be207-version">画面 V306</span></div>
   <div class="be207-condition" role="status"><strong></strong><span></span></div>
   <section class="be305-evidence" aria-label="選択レースの直前データ取得状況">
    <div class="be305-evidence-head"><strong>直前データの取得状況</strong><button type="button" data-be207="before">直前情報を詳しく見る →</button></div>
    <div class="be305-evidence-items" role="list"></div>
    <small>取得証跡の表示です。BOATERS・競艇日和・オリ展CSVは別出典。数値の一致・鮮度・出走確定は別途確認が必要です。</small>
   </section>
   <div class="be207-mode-label">予想スタイル <small>タップで切替</small></div>
   <div class="be207-modes" role="group" aria-label="予想スタイル"></div>
   <div class="be207-explain"><strong>展開</strong><span></span><button type="button" data-be207="scenario">詳しく →</button></div>
   <div class="be207-freeze"></div>
   <section class="be259-head-coverage" role="group" aria-label="頭候補・3連単買い目範囲・未校正信頼度">
     <div class="be259-head-row"><small>Top1買い目の頭（独立の頭確率ではない）</small><strong data-be259="head"></strong></div>
     <div class="be259-top-grid"><span data-be259="top3"></span><span data-be259="top5"></span><span data-be259="top10"></span></div>
     <div class="be259-confidence"><span><b>頭の1着信頼度</b><small data-be259="confidenceHead"></small></span><span><b>3連単Top10信頼度</b><small data-be259="confidenceTrifecta"></small></span></div>
     <small class="be259-metric" data-be259="metric"></small>
     <small class="be259-disclaimer">Top3/5/10は買い目の順位別範囲。頭の1着確率・3連単的中率とは別。結果の🎯・不的中は検証済み結果欄だけで判定します。</small>
   </section>
   <div class="be207-listhead"><strong>上位買い目</strong><span>元の予想順位を維持・オッズで並べ替えません。結果判定とは別</span></div>
   <div class="be207-bets"></div>
   <div class="be207-actions" role="group" aria-label="表示する3連単買い目の件数"><button type="button" data-be207="five">Top5</button><button type="button" data-be207="ten">Top10</button><button type="button" data-be207="all">全買い目</button></div><div class="be208-detail-actions"><button type="button" data-be207="detail">詳しいデータ・監査を開く</button></div>
   <div class="be207-bottom"><div class="be207-budget"></div><div class="be207-odds"></div></div>`;
  const first=$('.summary-top',host);
  if(first)first.insertAdjacentElement('afterend',box);else host.prepend(box);
 }
 return box;
}
/* Presentation only: never infer a prediction, verified source or freeze. */
function predictionWindowNotice(r,now=Date.now()){
 const key=String(r?.race_key||''),time=String(r?.meta?.deadline||'');
 const clock=/^([01]\d|2[0-3]):([0-5]\d)$/.exec(time);
 if(!valid(key)||!clock||String(r?.meta?.venue_code||'').padStart(2,'0')!==key.slice(9,11)||
    Number(r?.meta?.race_no)!==Number(key.slice(12,14)))
  return '出走表と締切予定を照合できません。未確認の買い目は表示しません。';
 const day=key.slice(0,4)+'-'+key.slice(4,6)+'-'+key.slice(6,8);
 if(r?.meta?.date&&r.meta.date!==day&&r.meta.date!==day.slice(0,4)+'-'+day.slice(4,6)+'-'+day.slice(6,8))
  return 'レース日付が一致しません。未確認の買い目は表示しません。';
 const due=Date.parse(day+'T'+time+':00+09:00');
 if(!Number.isFinite(due))return '締切予定時刻を確認できません。買い目は表示しません。';
 if(now>=due)return '締切済み：締切前に固定保存された買い目がなければ後付け表示しません。';
 if(now<due-15*60000){
  const from=new Date(due-15*60000).toLocaleTimeString('ja-JP',{timeZone:'Asia/Tokyo',hour:'2-digit',minute:'2-digit'});
  return '直前データ照合前：締切予定 '+time+' ／ 直前照合の目安 '+from+' JST。欠場・取消と保存証拠が揃うまでは買い目を表示しません。';
 }
 return '締切前の直前照合時間帯です。公式直前情報・欠場／取消・予想保存の証拠が揃うまでは買い目停止中です。';
}
function showPredictionWait(r,blocked){
 const host=$('#raceView .race-summary');
 let note=$('#be391PredictionWait');
 if(!host||!valid(r?.race_key)||!blocked){note?.remove();return;}
 if(!note){note=document.createElement('div');note.id='be391PredictionWait';note.className='be391-prediction-wait';note.setAttribute('role','status');host.appendChild(note);}
 if(note.parentElement!==host)host.appendChild(note);
 note.dataset.raceKey=r.race_key;
 text(note,'予想表示待ち｜'+predictionWindowNotice(r));
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
function listRow(row,i,fresh,settled){
 const node=document.createElement('div');node.className='be207-ticket';
 const v=str('b',row),combo=extractCombo(v),nums=combo?lanes(combo):null;
 const relative=str('em',row),label=str('small',row);
 const raw=str('.be140-ticket-money',row),stake=shownStake(row,settled);
 const payout=window.BoatEdgeV204?.parsePayout?.(raw)??null;
 const verifiedPrice=fresh&&/^\d+(?:\.\d+)?倍$/.test(label)?label:null;
 node.innerHTML='<span class="be207-rank"></span><div class="be207-combo"></div><span class="be207-prob"></span><span class="be207-multi"></span><div class="be207-moneys"><span class="be207-stake"></span><span class="be207-pay"></span></div>';
 text($('.be207-rank',node),i+1);
 const comboNode=$('.be207-combo',node);
 if(nums){for(const n of nums){const chip=document.createElement('span');chip.className='be207-lane be207-l'+n;chip.textContent=n;comboNode.append(chip);}}
 else text(comboNode,'買い目未確認');
 // The source "em" contains uncalibrated relative weight, not a calibrated probability.
 text($('.be207-prob',node),relative?('配分相対重み '+relative+'（未校正）'+'／勝率ではない'):'配分相対重み 未確認（勝率ではない）');
 text($('.be207-multi',node),verifiedPrice||'倍率未確認');
 text($('.be207-stake',node),stake===null?'配分未確認':(settled?'締切前の保存配分 ':'未購入の参考配分 ')+money(stake));
 text($('.be207-pay',node),!settled&&stake!==null&&verifiedPrice&&payout!==null?'既存の想定払戻 '+money(payout):'想定払戻 未確認');
 return node;
}

function render(){
 if(rendering)return;
 const r=race(),p=$('#be108PredictionModes'),v=$('#raceView');
 if(!valid(r?.race_key)||!p||!v||!window.BoatEdgeV204?.summarize){
  showPredictionWait(r,valid(r?.race_key)&&Boolean(v));
  $('#be207Top')?.remove();document.documentElement.classList.remove('be207-ready','be306-race-await');return;
 }
 const key=r.race_key,st=safety(r),sum=window.BoatEdgeV204.summarize(p),settled=sum.settled;
 const sourceList=$('.be108-ticket-list',p);
 // The V108 view can lag a race switch: its original ranked rows have no race
 // attribute. Never label the old list as a new race while it is still mounted.
 if(key!==activeKey){
  awaitingRaceList=holdPreviousRace(activeKey,key,lastListNode,sourceList);
  activeKey=key;showFive=false;showTen=false;showAll=false;
  document.documentElement.classList.remove('be208-details-on');lastSig='';
 }
 if(awaitingRaceList&&sourceList&&sourceList!==lastListNode)awaitingRaceList=false;
 if(!awaitingRaceList&&sourceList)lastListNode=sourceList;
 const rows=Array.from(p.querySelectorAll('.be108-ticket-list > .be108-ticket'));
 const mode=$('.be108-mode-tabs .on',p)?.dataset.be108Mode||'unknown';
 const stage=str('#scenarioHero .scenario-main')||'展開説明は現在確認できません';
 const freeze=window.BoatEdgeV204.sourceLabel?.(p)||'買い目保存状態未確認';
 const proof=window.BoatEdgeV204?.oddsProof?.(r);
 const fresh=Boolean(sum.fresh&&!settled&&proof?.quality==='verified');
 const evidence=evidenceFor(key);
 const provenance=$('.be181-freeze-banner',p)?.dataset?.be181Source||'';
 const rowOK=validTickets(rows);
 const pendingScratch=!settled&&st.kind!=='partial';
 const ticketViewSynced=Boolean(sourceList&&!awaitingRaceList);
 document.documentElement.classList.toggle('be306-race-await',!ticketViewSynced);
 const sig=JSON.stringify([key,mode,st.kind,st.title,st.detail,rows.length,showFive,showTen,showAll,fresh,settled,provenance,proof?.quality,proof?.label,rowOK,pendingScratch,ticketViewSynced,evidence,
  str('#be204Budget [data-be204="total"]',p),str('.be166-odds-status',p),stage,freeze,
  rows.map(x=>[str('b',x),str('em',x),str('small',x),str('.be140-ticket-money',x),str('.be204-ticket-finance',x)])]);
 const box=skeleton();if(!box)return;
 const stop=st.kind==='stop'||pendingScratch||!ticketViewSynced||!rowOK||!['first','final','latest'].includes(provenance);
 showPredictionWait(r,stop); // Refresh across the deadline even when the ticket signature stays unchanged.
 if(sig===lastSig&&box.classList.contains('ready'))return;
 rendering=true;
 try{
  box.classList.add('ready');box.dataset.status=st.kind;
  text($('.be207-condition strong',box),st.title||'欠場・取消確認待ち');
  text($('.be207-condition span',box),st.detail||'出走可否未確定');
  const evidenceList=$('.be305-evidence-items',box);
  evidenceList.replaceChildren();
  for(const item of evidence.items){
   const tag=document.createElement('div');tag.className='be305-evidence-item';tag.setAttribute('role','listitem');
   tag.dataset.quality=item.quality;
   const label=document.createElement('b');label.textContent=item.label;
   const value=document.createElement('span');value.textContent=item.text;
   tag.append(label,value);evidenceList.append(tag);
  }
  const modeHost=$('.be207-modes',box);
  if(ticketViewSynced)modeButtons(p,modeHost);
  else if(modeHost){if(modeHost.children.length)modeHost.replaceChildren();modeHost.dataset.sig='';}
  text($('.be207-explain span',box),ticketViewSynced?stage:'新レースの展開を照合中');
  text($('.be207-freeze',box),ticketViewSynced?'買い目：'+freeze+(settled?'／結果確定後の保存表示':''):'買い目：新レースの保存状態を照合中');
  const clarity=ticketClarity(rows.map(row=>str('b',row)),!stop);
  for(const field of ['head','top3','top5','top10','confidenceHead','confidenceTrifecta'])
    text($('[data-be259="'+field+'"]',box),clarity[field]);
  // V174 may replace this panel with measured *past* site-only hit rate.
  // Do not mix that historical rate with a current-race confidence claim.
  const evidenceTitle=str('.be108-mode-top small',p);
  const evidenceValue=str('.be108-mode-top strong',p);
  const evidenceLabel=/過去的中率/.test(evidenceTitle)?'過去実績（このレース固有の確率ではない）':
    /内部スコア/.test(evidenceTitle)?'内部評価値（未校正・確率ではない）':'既存参考指標（校正状態不明）';
  text($('[data-be259="metric"]',box),!ticketViewSynced?'既存参考指標：新レースの値を照合中':evidenceValue?evidenceLabel+'：'+evidenceValue:'信頼度の独立した検証値は未取得');
  const list=$('.be207-bets',box);list.replaceChildren();
  const count=showAll?rows.length:showTen?10:showFive?5:3;
  if(stop){const w=document.createElement('div');w.className='be207-stop';w.textContent=!ticketViewSynced?'選択した新しいレースの買い目を照合中。前レースの買い目は表示しません。':'買い目は非表示：出走可否・締切前保存状態・買い目の一意性を確認してください。欠測値から候補を補完しません。';list.append(w);}
  else rows.slice(0,count).forEach((row,i)=>list.append(listRow(row,i,fresh,settled)));
  const five=$('[data-be207="five"]',box);five.hidden=stop||rows.length<5||showAll;
  text(five,showFive?'Top3に戻す':'Top5を表示');
  five.setAttribute('aria-pressed',String(showFive));
  const ten=$('[data-be207="ten"]',box);ten.hidden=stop||rows.length<10||showAll;
  text(ten,showTen?'Top3に戻す':'Top10を表示');
  ten.setAttribute('aria-pressed',String(showTen));
  const all=$('[data-be207="all"]',box);all.hidden=stop;
  text(all,showAll?'Top3に戻す':'全買い目を表示');
  all.setAttribute('aria-pressed',String(showAll));
  const total=str('#be204Budget [data-be204="total"]',p);
  // A stopped/unverified ticket list must not retain an actionable-looking budget.
  text($('.be207-budget',box),!ticketViewSynced?'配分：新レースの値を照合中（旧レースの値は表示しません）':stop?'配分：買い目を停止・未確認のため非表示':settled?'締切前の保存配分がある券のみ個別表示（実購入なし）':
    '元画面の参考配分合計：'+(total||'未確認')+' ／ '+(rowOK?rows.length+'点':'券種照合待ち')+'（実購入なし）');
  text($('.be207-odds',box),!ticketViewSynced?'公式オッズ：新レースの証跡を照合中':stop?'公式オッズ・想定払戻：買い目停止・未確認のため非表示':fresh?
    '公式3連単オッズの保存値（非リアルタイム）：'+(proof?.label||'取得状態確認中'):
    '公式3連単オッズ未確認／想定払戻は非表示');
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
  if(command==='five'){showFive=!showFive;showTen=false;showAll=false;lastSig='';render();return;}
  if(command==='ten'){showTen=!showTen;showFive=false;showAll=false;lastSig='';render();return;}
  if(command==='scenario'){$('#raceTabs [data-tab="scenario"]')?.click();return;}
  if(command==='before'){$('#raceTabs [data-tab="before"]')?.click();return;}
  if(command==='all'){showAll=!showAll;showFive=false;showTen=false;lastSig='';render();return;}
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
window.BoatEdgeV207={render,displayOnly:true,version:'V306-DISPLAY-ONLY',ticketClarity,extractCombo,shownStake,validTickets,evidenceFor,holdPreviousRace,predictionWindowNotice};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
