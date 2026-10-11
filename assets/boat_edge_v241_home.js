(function(){'use strict';
const el=document.getElementById('be241HomeResults');
if(!el)return;
const html=s=>String(s??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[ch]));
async function update(){try{
const response=await fetch('./data/site_autopilot/v241_results_current.json?t='+Date.now(),{cache:'no-store'});
if(!response.ok)throw Error('not available');const result=await response.json();
if(result.schema!=='BOAT_EDGE_V241_VERIFIED_SITE_RESULTS_V1'||result.formal_result_access!==false||!Array.isArray(result.rows))throw Error('unverified source');
const latest=result.rows.slice(0,3);
el.innerHTML=latest.map(x=>`<div class="be241-home-result-item"><div><strong>${html(x.venue)} ${Number(x.round)}R</strong><small>${html(x.winning_combo)} ・${html(x.date_jst.slice(4,6))}/${html(x.date_jst.slice(6,8))}</small></div><span class="${x.top10_hit?'hit':'miss'}">${x.top10_hit?'🎯 的中':'不的中'}</span></div>`).join('')||'<div class="be241-home-results-status">検証済みレースはまだありません。</div>';
document.getElementById('be241HomeResultsStatus').textContent=`サイト参考予想の厳格検証 ${result.settled_verified_races}R / Top10的中 ${result.top10_hits}R（実購入なし）`;
}catch(_){el.textContent='確認できる結果データはまだありません。';document.getElementById('be241HomeResultsStatus').textContent='未確認の結果に🎯は付けません。'} }
update();
})();
