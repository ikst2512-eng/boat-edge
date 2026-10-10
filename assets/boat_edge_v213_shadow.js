/* V213 isolated prospective SHADOW evidence. Never buys, never changes original bankroll or predictions. */
(()=>{'use strict';
const q=s=>document.querySelector(s), qa=s=>[...document.querySelectorAll(s)];
const txt=(el,t)=>{if(el)el.textContent=String(t)};
const el=(tag,className,value)=>{const e=document.createElement(tag);if(className)e.className=className;if(value!==undefined)e.textContent=String(value);return e};
const fmtMoney=n=>typeof n==='number'&&Number.isFinite(n)?n.toLocaleString('ja-JP')+'円':'―';
function install(){
 const tabs=q('.sim-tabs');if(!tabs||q('#be213Tab'))return;
 const tab=el('button','','未見検証');tab.id='be213Tab';tab.type='button';tab.dataset.tab='shadow';tabs.insertBefore(tab,tabs.querySelector('a'));
 const pane=el('section','sim-pane');pane.id='panel-shadow';pane.hidden=true;
 pane.innerHTML=`<div class="pane-title"><h2>未見シャドー検証</h2><span class="soft">V213</span></div>
  <p class="be213-note">締切前に買い目を固定し、後から公式結果を照合する研究用レーン。<strong>仮想購入・実購入ではない</strong>ので、上の5万円予算や購入履歴には加算しません。</p>
  <div class="be213-stats"><div><small>事前固定</small><strong id="be213Frozen">―</strong></div><div><small>結果照合済み</small><strong id="be213Settled">―</strong></div><div><small>結果待ち</small><strong id="be213Pending">―</strong></div><div><small>参考ROI</small><strong id="be213ROI">―</strong></div></div>
  <div id="be213State" class="sim-notice">監査データを読み込み中…</div>
  <div class="pane-title"><h2>事前固定候補</h2><span class="soft" id="be213Scan">取得待ち</span></div>
  <div class="table-scroll"><table class="sim-table"><thead><tr><th>場／R</th><th>候補（上位3）</th><th>オッズ</th><th>状態</th></tr></thead><tbody id="be213Rows"><tr><td colspan="4">確認中</td></tr></tbody></table></div>
  <p class="be213-foot">見込みEVは未校正の参考値であり購入判断ではありません。シャドーの回収率は一律100円ずつ購入したと仮定した検証用数値で、実収支ではありません。</p>`;
 q('.sim-main')?.insertBefore(pane,q('.sim-footer'));
 tab.addEventListener('click',()=>{
   for(const b of qa('.sim-tabs [data-tab]')){const active=b===tab;b.classList.toggle('selected',active);b.setAttribute('aria-selected',String(active));}
   for(const p of qa('.sim-pane')){p.hidden=p!==pane;p.classList.toggle('selected',p===pane);}refresh();
 });
}
async function refresh(){
 if(!q('#panel-shadow'))return;
 try{
  const res=await fetch('./data/site_paper_sim/shadow_v213_current.json?ts='+Date.now(),{cache:'no-store'});
  if(!res.ok)throw Error('status '+res.status);
  const d=await res.json();if(d.schema!=='BOAT_EDGE_V213_PROSPECTIVE_SHADOW_V1'||d.cash_stake_yen!==0)throw Error('schema');
  txt(q('#be213Frozen'),(d.frozen_races??0)+'R');txt(q('#be213Settled'),(d.settled_races??0)+'R');
  txt(q('#be213Pending'),(d.pending_races??0)+'R');
  txt(q('#be213ROI'),d.flat100_observed_roi_percent==null?'集計待ち':Number(d.flat100_observed_roi_percent).toFixed(1)+'%');
  txt(q('#be213State'),(d.settled_races??0)<100?'正式判定前：未見100R以上と独立した確率校正が必要。参考成績を5万円運用に混ぜません。':'100R以上を照合済み。ただし購入条件の正式承認は別監査が必要です。');
  const scan=d.last_scan||{};txt(q('#be213Scan'),`直近対象 ${scan.window_races??0}R ／ 今回固定 ${scan.new_shadow_frozen??0}R`);
  const rows=q('#be213Rows');rows.replaceChildren();
  const recent=Array.isArray(d.recent)?d.recent:[];
  if(!recent.length){const tr=el('tr');const td=el('td','','締切前の証跡が揃った候補を待機中。買い目を後付けしません。');td.colSpan=4;tr.append(td);rows.append(tr)}
  for(const x of recent){
   const tr=el('tr');tr.append(el('td','',`${x.venue||'―'} ${x.race_no??'―'}R`),el('td','',(x.tickets||[]).map(t=>t.combo).join(' / ')||'―'),el('td','',(x.tickets||[]).map(t=>String(t.pre_result_odds)+'倍').join(' / ')||'―'),el('td','',x.status==='shadow_settled'?`結果照合済 ${fmtMoney(x.shadow_return_yen)}`:'結果待ち'));rows.append(tr);
  }
 }catch(_){txt(q('#be213State'),'未見検証データが未生成または未公開。購入実績を補完しません。');}
}
function init(){install();refresh();document.querySelector('#simRefresh')?.addEventListener('click',refresh);setInterval(()=>{if(!document.hidden)refresh()},60000);}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
