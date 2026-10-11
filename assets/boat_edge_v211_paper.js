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
  const spent=m.today_spent_yen,remaining=m.today_remaining_yen;
  text('#simDay',dayLabel(actualDay));
  text('#simMode',proof.current?'実際の購入なし':'過去の保存台帳（本日未確認）');
  text('#simUpdated',fmt(d.updated_at)+' 更新');
  text('#simBalance',proof.current?remaining.toLocaleString('ja-JP')+'円':'―');
  text('#simSpent',proof.current?yen(spent):'―');
  text('#simTodayBuys',proof.current?m.today_paper_races+'R':'―');
  const profit=m.settled_stake_yen?((m.profit_yen>0?'+':'')+yen(m.profit_yen)):'未精算';text('#simProfit',profit);
  q('#simProfit')?.classList.toggle('negative',m.profit_yen<0);
  text('#simRoi',m.roi_percent==null?'未精算':Number(m.roi_percent).toFixed(1)+'%');text('#simPending',yen(m.pending_yen));
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
  const reasonBox=q('#simReasons');reasonBox.replaceChildren();for(const [reason,count] of Object.entries(scan.skipped_by_reason||{})){reasonBox.append(el('span','',`${reason} ${count}R`))}
  const hist=q('#simHistory');hist.replaceChildren();const history=d.recent_bets||[];text('#simHistoryCount',history.length+'件');
  if(!history.length)hist.append(el('p','empty','まだ仮想購入はありません。条件を満たさない日は資金を使いません。'));
  for(const row of history){const wrap=el('article','sim-race'),top=el('div','sim-race-top'),tag=el('span','state'+(row.state==='pending'?' pending':''),row.state==='settled'?'結果確定':'結果待ち');
   top.append(el('b','',`${row.venue||'開催場'} ${row.race_no||'－'}R`),tag);wrap.append(top);
   wrap.append(el('p','',`仮想購入 ${yen(row.stake_yen)} ｜ 判断 ${fmt(row.decision_at)}${row.state==='settled'?' ｜ 仮想払戻 '+yen(row.return_yen):''}`));
   const tickets=el('div','sim-bets');for(const t of row.tickets||[]){tickets.append(el('span','',`${t.combo}　${yen(t.paper_stake_yen)}`))}wrap.append(tickets);hist.append(wrap)}
 }catch(e){
  showEvidence({verified:false,message:'仮想運用の保存台帳を確認できません。予算・購入額・利益を補完しません。'});
  for(const id of ['#simBalance','#simSpent','#simTodayBuys','#simProfit','#simRoi','#simPending'])text(id,'―');
  text('#simMode','データ未確認');text('#simUpdated','最終更新未確認');
  text('#simState','未確認');text('#simGate','自走データを確認できません。未確認の購入・回収率は表示しません。');
 }
}
for(const b of qa('.sim-tabs [data-tab]'))b.addEventListener('click',()=>showTab(b.dataset.tab));
q('#simRefresh')?.addEventListener('click',refresh);showTab('decision');refresh();
setInterval(()=>{if(!document.hidden)refresh()},60000);
window.BoatEdgeV211PaperEvidence={paperEvidence};
})();
