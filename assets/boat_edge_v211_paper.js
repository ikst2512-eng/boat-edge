/* BOAT EDGE V211 paper-only: read-only UI. No real bets, no prediction changes. */
(()=>{'use strict';
const q=s=>document.querySelector(s), qa=s=>[...document.querySelectorAll(s)];
const yen=x=>(Number(x)||0).toLocaleString('ja-JP')+'円';
const fmt=x=>{const d=x?new Date(x):null;return d&&Number.isFinite(d.getTime())?d.toLocaleString('ja-JP',{timeZone:'Asia/Tokyo',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}):'未確認'};
const text=(s,v)=>{const e=q(s);if(e&&e.textContent!==String(v))e.textContent=String(v)};
const el=(tag,cls,txt)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=String(txt);return e};
/* V244 A07: never substitute a planned 50,000 yen for missing ledger evidence. */
function paperEvidence(data,now=Date.now()){
 const m=data?.money,valid=v=>Number.isSafeInteger(v)&&v>=0;
 if(data?.mode!=='PAPER_ONLY'||m?.virtual_only!==true||!/^20\d{6}$/.test(String(m.day||''))||
    !valid(m.daily_budget_yen)||!valid(m.today_spent_yen)||!valid(m.today_remaining_yen)||
    !valid(m.today_paper_races)||m.today_spent_yen+m.today_remaining_yen!==m.daily_budget_yen)
  return {verified:false,message:'仮想予算・使用額の記録を確認できません（配分や利益を補完しません）'};
 const today=new Date(now+9*3600000).toISOString().slice(0,10).replaceAll('-','');
 const current=String(m.day)===today;
 const skipped=data?.scan?.skipped_by_reason;
 const reasons=skipped&&typeof skipped==='object'&&!Array.isArray(skipped)?
   Object.entries(skipped).filter(([k,v])=>typeof k==='string'&&valid(v)&&v>0)
     .sort((a,b)=>b[1]-a[1]).slice(0,3).map(([k,v])=>k+' '+v+'R').join(' / '):'';
 const noBet=m.today_paper_races===0;
 const gate=data.strategy_status==='PAPER_ACTIVE'?'仮想購入条件の監査あり':'未見校正・購入条件の確認待ち';
 return {verified:true,current,day:m.day,budget:m.daily_budget_yen,spent:m.today_spent_yen,
   remaining:m.today_remaining_yen,count:m.today_paper_races,
   message:(current?'本日':'保存日 '+m.day+'（本日の数字ではない）')+' / 紙上予算 '+yen(m.daily_budget_yen)+
    ' / 台帳使用額 '+yen(m.today_spent_yen)+' / 残額 '+yen(m.today_remaining_yen)+
    ' / 仮想購入 '+m.today_paper_races+'R'+' / '+gate+
    (noBet?' / 条件未成立なら0円を維持':'')+(reasons?' / 見送り理由：'+reasons:'')};
}
/* V248 A15: never label unverified history as an actual or paper purchase. */
function verifiedBet(row){
 const amount=v=>Number.isSafeInteger(v)&&v>=0&&v%100===0;
 if(!row||!['pending','settled'].includes(row.state)||
    !amount(row.stake_yen)||row.stake_yen===0||
    !Number.isFinite(Date.parse(row.decision_at||''))||
    !Array.isArray(row.tickets)||!row.tickets.length)return false;
 const keys=new Set(),tickets=row.tickets;
 let sum=0;
 for(const t of tickets){
  if(!/^[1-6]-[1-6]-[1-6]$/.test(String(t?.combo||''))||new Set(t.combo.split('-')).size!==3||
     keys.has(t.combo)||!amount(t.paper_stake_yen)||t.paper_stake_yen<=0)return false;
  keys.add(t.combo);sum+=t.paper_stake_yen;
 }
 if(sum!==row.stake_yen)return false;
 return row.state!=='settled'||(Number.isSafeInteger(row.return_yen)&&row.return_yen>=0);
}
function paperStates(data,proof){
 const m=data?.money||{},amount=v=>Number.isSafeInteger(v)&&v>=0;
 if(!proof?.verified||!amount(m.pending_yen)||!amount(m.settled_stake_yen)||
    !Array.isArray(data?.recent_bets))return {kind:'unknown',label:'仮想結果：記録の確認待ち（補完しません）'};
 const history=data.recent_bets;
 if(history.some(r=>!verifiedBet(r)))return {kind:'unknown',label:'仮想結果：保存履歴の検証不一致（補完しません）'};
 const pending=history.filter(r=>r.state==='pending').length;
 const settled=history.filter(r=>r.state==='settled').length;
 const noBet=proof.current&&proof.count===0&&proof.spent===0&&history.length===0;
 const label=noBet?'本日は仮想購入0件。購入条件を満たすまで見送り':
   '保存履歴：結果待ち '+pending+'件／結果確定 '+settled+'件'+
     '（最近の記録のみ。総件数・確定利益ではありません）';
 return {kind:noBet?'no-bet':pending?'pending':settled?'settled':'unknown',label};
}
/* V250 A20: reject stale, wrong-day and uncounted skip reasons, never fill gaps. */
function skipEvidence(scan,proof,now=Date.now()){
  const t=Date.parse(scan?.as_of||'');
  const day=Number.isFinite(t)?new Date(t+9*3600000).toISOString().slice(0,10).replaceAll('-',''):'';
  if(!proof?.verified||!Number.isFinite(t)||t>now+30000||day!==proof.day||
     !scan?.skipped_by_reason||typeof scan.skipped_by_reason!=='object'||
     Array.isArray(scan.skipped_by_reason))
    return {verified:false,message:'見送り理由の内訳：保存元・取得日が未確認',rows:[]};
  const entries=Object.entries(scan.skipped_by_reason);
  if(entries.some(([k,v])=>!k||!Number.isSafeInteger(v)||v<0))
    return {verified:false,message:'見送り理由の内訳：記録値を確認できません',rows:[]};
  const rows=entries.filter(x=>x[1]>0).sort((a,b)=>b[1]-a[1]);
  return {verified:true,rows,message:rows.length?'保存済み見送り理由（'+day+'・'+fmt(scan.as_of)+'取得）':
    '見送り理由の個別件数は記録されていません（0Rとは断定しません）'};
}
function showPaperStates(status){
 let e=q('#be248PaperStates');
 if(!e){e=el('div','sim-notice');e.id='be248PaperStates';e.setAttribute('role','status');
  e.style.margin='8px 0';q('.stat-row')?.insertAdjacentElement('afterend',e);}
 if(e){e.dataset.state=status.kind;e.textContent=status.label;}
}
function showEvidence(e){
 let n=q('#be244PaperEvidence');
 if(!n){
  n=el('div','sim-notice');
  n.id='be244PaperEvidence';n.setAttribute('role','status');
  n.style.margin='10px 0';n.style.lineHeight='1.7';
  q('.sim-fund')?.insertAdjacentElement('afterend',n);
 }
 if(n){n.textContent=e.message;n.dataset.verified=String(e.verified);}
}
function dayLabel(day){if(!/^20\d{6}$/.test(String(day||'')))return '本日のレース';return `${day.slice(4,6)}/${day.slice(6,8)} の仮想運用`}
function showTab(k){for(const b of qa('.sim-tabs [data-tab]')){const on=b.dataset.tab===k;b.classList.toggle('selected',on);b.setAttribute('aria-selected',String(on));}
for(const pane of qa('.sim-pane')){const on=pane.id==='panel-'+k;pane.hidden=!on;pane.classList.toggle('selected',on);}}
async function refresh(){
 try{
  const r=await fetch('./data/site_paper_sim/current.json?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('http '+r.status);
  const d=await r.json();if(d.mode!=='PAPER_ONLY'||!['boat-edge-paper-sim-v211','boat-edge-paper-sim-v209'].includes(d.schema))throw Error('schema');
  const proof=paperEvidence(d);showEvidence(proof);
  if(!proof.verified)throw Error('unverified paper ledger');
  const m=d.money,actualDay=m.day;
  const evidenceStates=paperStates(d,proof);showPaperStates(evidenceStates);
  const spent=m.today_spent_yen,remaining=m.today_remaining_yen;
  text('#simDay',dayLabel(actualDay));
  text('#simMode',proof.current?'実際の購入なし':'過去の保存台帳（本日未確認）');
  text('#simUpdated',fmt(d.updated_at)+' 更新');
  text('#simBalance',proof.current?remaining.toLocaleString('ja-JP')+'円':'―');
  text('#simSpent',proof.current?yen(spent):'―');
  text('#simTodayBuys',proof.current?m.today_paper_races+'R':'―');
  const profit=evidenceStates.kind!=='unknown'&&m.settled_stake_yen>0&&Number.isSafeInteger(m.profit_yen)?((m.profit_yen>0?'+':'')+yen(m.profit_yen)):'未精算';text('#simProfit',profit);
  q('#simProfit')?.classList.toggle('negative',m.profit_yen<0);
  text('#simRoi',evidenceStates.kind==='unknown'||m.roi_percent==null||
   !Number.isFinite(m.roi_percent)?'未確認':Number(m.roi_percent).toFixed(1)+'%');
  text('#simPending',Number.isSafeInteger(m.pending_yen)&&m.pending_yen>=0?yen(m.pending_yen):'―');
  const active=proof.current&&d.strategy_status==='PAPER_ACTIVE';
  text('#simState',!proof.current?'本日台帳未確認':active?'仮想自走中':'精度検証待ち');q('#simState')?.classList.toggle('pill-active',active);q('#simState')?.classList.toggle('pill-wait',!active);
  text('#simGate',!proof.current?'この保存記録は別日のものです。本日の仮想購入状況は未確認。':
    d.calibration_status||'未見検証の取得待ち。条件未達のレースは見送り。');
  const scan=d.scan||{};text('#simScanAt',fmt(scan.as_of)+' 時点');
  text('#simDecision',proof.current?
    `締切前の審査 ${scan.in_window??0}R ／ 条件適合 ${scan.eligible??0}R ／ 今回の仮想購入 ${scan.paper_purchases??0}R`:
    '保存日は'+actualDay+'。本日の直前審査・仮想購入の状態は未確認。');
  const rows=q('#simReviewRows');rows.replaceChildren();
  const review=scan.reviews||[];
  if(!review.length){const tr=el('tr');const td=el('td','empty','直近の締切前レースを監視中。条件成立まで購入しません。');td.colSpan=4;tr.append(td);rows.append(tr)}
  for(const a of review.slice(-36).reverse()){
   const tr=el('tr');tr.append(el('td','',String(a.venue||'－')+' '+String(a.race_no||'－')+'R'),el('td','',a.deadline||'―'));
   const c=el('td');c.append(el('span','tag'+(a.decision==='candidate'?' ok':''),a.decision==='candidate'?'候補':'見送り'));tr.append(c,el('td','',a.reason||'要確認'));rows.append(tr);
  }
  const reasonBox=q('#simReasons');reasonBox.replaceChildren();
  const skips=skipEvidence(scan,proof);
  reasonBox.append(el('strong','be250-reason-head',skips.message));
  for(const [reason,count] of skips.rows)reasonBox.append(el('span','',reason+' '+count+'R'));
  const hist=q('#simHistory');hist.replaceChildren();
  const history=evidenceStates.kind==='unknown'?[]:d.recent_bets;
  text('#simHistoryCount',evidenceStates.kind==='unknown'?'未確認':history.length+'件（保存分）');
  if(!history.length)hist.append(el('p','empty',
    evidenceStates.kind==='unknown'?'仮想履歴を検証できません。架空の購入や払戻は作りません。':
    proof.current&&proof.count===0?'本日の仮想購入は0件です。条件が揃うまで見送ります。':
    '表示できる検証済みの最近の購入記録はありません。'));
  for(const row of history){const wrap=el('article','sim-race'),top=el('div','sim-race-top'),tag=el('span','state'+(row.state==='pending'?' pending':''),row.state==='settled'?'結果確定':'結果待ち');
   top.append(el('b','',`${row.venue||'開催場'} ${row.race_no||'－'}R`),tag);wrap.append(top);
   wrap.append(el('p','',`仮想購入 ${yen(row.stake_yen)} ｜ 判断 ${fmt(row.decision_at)}${row.state==='settled'?' ｜ 仮想払戻 '+yen(row.return_yen):''}`));
   const tickets=el('div','sim-bets');for(const t of row.tickets||[]){tickets.append(el('span','',`${t.combo}　${yen(t.paper_stake_yen)}`))}wrap.append(tickets);hist.append(wrap)}
 }catch(e){
  showPaperStates({kind:'unknown',label:'仮想結果：保存台帳の検証待ち。金額を補完しません。'});
  showEvidence({verified:false,message:'仮想運用の保存台帳を確認できません。予算・購入額・利益を補完しません。'});
  for(const id of ['#simBalance','#simSpent','#simTodayBuys','#simProfit','#simRoi','#simPending'])text(id,'―');
  text('#simMode','データ未確認');text('#simUpdated','最終更新未確認');
  text('#simState','未確認');text('#simGate','自走データを確認できません。未確認の購入・回収率は表示しません。');
 }
}
for(const b of qa('.sim-tabs [data-tab]'))b.addEventListener('click',()=>showTab(b.dataset.tab));
q('#simRefresh')?.addEventListener('click',refresh);showTab('decision');refresh();
setInterval(()=>{if(!document.hidden)refresh()},60000);
window.BoatEdgeV211PaperEvidence={paperEvidence,paperStates,verifiedBet,skipEvidence};
})();
