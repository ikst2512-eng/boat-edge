/* BOAT EDGE V211 paper-only: read-only UI. No real bets, no prediction changes. */
(()=>{'use strict';
const q=s=>document.querySelector(s), qa=s=>[...document.querySelectorAll(s)];
const yen=x=>(Number(x)||0).toLocaleString('ja-JP')+'円';
const fmt=x=>{const d=x?new Date(x):null;return d&&Number.isFinite(d.getTime())?d.toLocaleString('ja-JP',{timeZone:'Asia/Tokyo',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'}):'未確認'};
const text=(s,v)=>{const e=q(s);if(e&&e.textContent!==String(v))e.textContent=String(v)};
const el=(tag,cls,txt)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=String(txt);return e};
function dayLabel(day){if(!/^20\d{6}$/.test(String(day||'')))return '本日のレース';return `${day.slice(4,6)}/${day.slice(6,8)} の仮想運用`}
function showTab(k){for(const b of qa('.sim-tabs [data-tab]')){const on=b.dataset.tab===k;b.classList.toggle('selected',on);b.setAttribute('aria-selected',String(on));}
for(const pane of qa('.sim-pane')){const on=pane.id==='panel-'+k;pane.hidden=!on;pane.classList.toggle('selected',on);}}
async function refresh(){
 try{
  const r=await fetch('./data/site_paper_sim/current.json?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('http '+r.status);
  const d=await r.json();if(d.mode!=='PAPER_ONLY'||!['boat-edge-paper-sim-v211','boat-edge-paper-sim-v209'].includes(d.schema))throw Error('schema');
  const m=d.money||{};const actualDay=m.day||new Date(Date.now()+9*3600000).toISOString().slice(0,10).replaceAll('-','');
  const spent=Number(m.today_spent_yen??0),remaining=Number(m.today_remaining_yen??m.daily_budget_yen??50000);
  text('#simDay',dayLabel(actualDay));text('#simMode','実際の購入なし');text('#simUpdated',fmt(d.updated_at)+' 更新');
  text('#simBalance',(remaining||0).toLocaleString('ja-JP')+'円');
  text('#simSpent',yen(spent));text('#simTodayBuys',(m.today_paper_races??0)+'R');
  const profit=m.settled_stake_yen?((m.profit_yen>0?'+':'')+yen(m.profit_yen)):'未精算';text('#simProfit',profit);
  q('#simProfit')?.classList.toggle('negative',m.profit_yen<0);
  text('#simRoi',m.roi_percent==null?'未精算':Number(m.roi_percent).toFixed(1)+'%');text('#simPending',yen(m.pending_yen));
  const active=d.strategy_status==='PAPER_ACTIVE';text('#simState',active?'仮想自走中':'精度検証待ち');q('#simState')?.classList.toggle('pill-active',active);q('#simState')?.classList.toggle('pill-wait',!active);
  text('#simGate',d.calibration_status||'未見検証の取得待ち。条件未達のレースは見送り。');
  const scan=d.scan||{};text('#simScanAt',fmt(scan.as_of)+' 時点');text('#simDecision',`締切前の審査 ${scan.in_window??0}R ／ 条件適合 ${scan.eligible??0}R ／ 今回の仮想購入 ${scan.paper_purchases??0}R`);
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
 }catch(e){text('#simMode','データ準備中');text('#simUpdated','ページ公開後に反映');text('#simGate','自走データを取得できません。未確認の購入・回収率は表示しません。')}
}
for(const b of qa('.sim-tabs [data-tab]'))b.addEventListener('click',()=>showTab(b.dataset.tab));
q('#simRefresh')?.addEventListener('click',refresh);showTab('decision');refresh();
setInterval(()=>{if(!document.hidden)refresh()},60000);
})();
