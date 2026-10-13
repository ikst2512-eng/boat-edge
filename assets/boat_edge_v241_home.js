/* BOAT EDGE V360 — verify site-only saved results before any home 🎯 indicator.
   This is display-only and never reads or unlocks Formal Fresh results. */
(function(){'use strict';
const el=document.getElementById('be241HomeResults');
if(!el)return;
const status=document.getElementById('be241HomeResultsStatus');
const html=s=>String(s??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
const KEY=/^20\d{6}-\d{2}-\d{2}$/;
const COMBO=/^[1-6]-[1-6]-[1-6]$/;
const SHA=/^[a-f0-9]{64}$/i,COMMIT=/^[a-f0-9]{40}$/i;
const isInt=n=>Number.isSafeInteger(n);
const comboOK=s=>typeof s==='string'&&COMBO.test(s)&&new Set(s.split('-')).size===3;
function verifiedRow(x){
 if(!x||!KEY.test(String(x.race_key||''))||!comboOK(x.winning_combo)||
   x.date_jst!==x.race_key.slice(0,8)||x.post_result_verified!==true||
   !SHA.test(String(x.precommitted_sha256||''))||!COMMIT.test(String(x.first_frozen_commit||''))||
   !isInt(x.round)||x.round<1||x.round>12||
   !isInt(x.official_payout_per_100_yen)||x.official_payout_per_100_yen<=0||
   typeof x.top10_hit!=='boolean'||typeof x.head_hit!=='boolean'||
   x.head_hit!==(String(x.head_prediction)===x.winning_combo[0])||!x.mode_outcomes)return false;
 const hit=x.mode_outcomes.hit;
 if(!hit||x.top10_hit!==hit.hit)return false;
 return ['hit','balance','hole','narrow'].every(mode=>{
   const item=x.mode_outcomes[mode];
   return item&&typeof item.hit==='boolean'&&item.stake_yen===10000&&
     isInt(item.hypothetical_return_yen)&&item.hypothetical_return_yen>=0&&
     item.hypothetical_profit_yen===item.hypothetical_return_yen-10000;
 });
}
function verifiedReport(data){
 if(!data||data.schema!=='BOAT_EDGE_V241_VERIFIED_SITE_RESULTS_V1'||
   data.scope!=='VERIFIED_POST_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH'||
   data.formal_result_access!==false||data.production_model_changed!==false||
   data.real_or_paper_wagers_placed!==0||
   !isInt(data.settled_verified_races)||data.settled_verified_races<0||
   !isInt(data.top10_hits)||!isInt(data.head_hits)||
   !Array.isArray(data.rows)||data.rows.length!==data.settled_verified_races||
   !data.rows.every(verifiedRow))return false;
 const rows=data.rows;
 if(new Set(rows.map(x=>x.race_key)).size!==rows.length)return false;
 return rows.filter(x=>x.top10_hit).length===data.top10_hits&&
   rows.filter(x=>x.head_hit).length===data.head_hits;
}
window.BoatEdgeV241Home={verifiedReport,verifiedRow,version:'V360-DISPLAY-ONLY'};
async function update(){
 try{
  const response=await fetch('./data/site_autopilot/v241_results_current.json?t='+Date.now(),{cache:'no-store'});
  if(!response.ok)throw Error('unavailable');
  const result=await response.json();
  if(!verifiedReport(result))throw Error('unverified site-only rows');
  const latest=result.rows.slice(0,3);
  el.innerHTML=latest.map(x=>`<div class="be241-home-result-item"><div><strong>${html(x.venue)} ${x.round}R</strong><small>${html(x.winning_combo)} ・${html(x.date_jst.slice(4,6))}/${html(x.date_jst.slice(6,8))}</small></div><span class="${x.top10_hit?'hit':'miss'}">${x.top10_hit?'🎯 的中':'不的中'}</span></div>`).join('')||'<div class="be241-home-results-status">検証済みレースはまだありません。</div>';
  if(status)status.textContent=`サイト参考予想の厳格検証 ${result.settled_verified_races}R / Top10的中 ${result.top10_hits}R（実購入なし）`;
 }catch(_){
  // Fail closed: an unverified row must never become a homepage "🎯".
  el.textContent='確認できる結果データはまだありません。';
  if(status)status.textContent='未確認の結果に🎯は付けません。';
 }
}
update();
})();
