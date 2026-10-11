(function(){'use strict';
const API='./data/site_autopilot/v241_results_current.json';
const SCHEMA='BOAT_EDGE_V241_VERIFIED_SITE_RESULTS_V1';
const ID=id=>document.getElementById(id);
const nf=new Intl.NumberFormat('ja-JP');
const modeNames={hit:'的中重視',balance:'バランス',hole:'波乱展開',narrow:'激絞り'};
let data=null,filter='all';
const yen=n=>typeof n==='number'&&Number.isFinite(n)?'¥'+nf.format(n):'未取得';
const safe=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
function tiles(combo){const values=String(combo||'').split('-');return values.length===3&&values.every(n=>/^[1-6]$/.test(n))?values.map(n=>`<span class="be241-boat" data-n="${n}">${n}</span>`).join(''):safe(combo)}
function dateLabel(yyyymmdd){return /^20\d{6}$/.test(yyyymmdd)?`${yyyymmdd.slice(0,4)}年${Number(yyyymmdd.slice(4,6))}月${Number(yyyymmdd.slice(6))}日`:'日付不明'}
function verifiedRow(r){return r?.post_result_verified===true &&
 r.mode_outcomes?.hit && typeof r.mode_outcomes.hit.hit==='boolean' &&
 r.top10_hit===r.mode_outcomes.hit.hit &&
 typeof r.official_payout_per_100_yen==='number' &&
 Number.isFinite(r.official_payout_per_100_yen);}
function modeRow(r,mode){const out=r.mode_outcomes?.[mode];if(!out||!verifiedRow(r))return '';
const profit=out.hypothetical_profit_yen;
const returnText=out.hit?yen(out.hypothetical_return_yen):'¥0';
return `<article class="be241-item"><div class="be241-item-top"><div class="be241-venue">${safe(r.venue)} <b>${Number(r.round)}R</b> <small>${safe(r.model_id)}</small></div><span class="be241-status ${out.hit?'hit':''}" data-verification="${out.hit?'verified-hit':'verified-miss'}">${out.hit?'🎯 的中':'不的中'}</span></div><div class="be241-mainline"><div class="be241-combo" role="img" aria-label="確定着順 ${safe(r.winning_combo)}">${tiles(r.winning_combo)}</div><div class="be241-result-money"><small>公式3連単払戻 / 100円</small><strong>${yen(r.official_payout_per_100_yen)}</strong></div></div><div class="be241-detail"><div><span>AI予想1着</span><b class="${r.head_hit?'headtag':''}">${safe(r.head_prediction)}号艇 ${r.head_hit?'✓頭的中':'頭外れ'}</b></div><div><span>仮想1万円の払戻</span><b>${returnText}</b></div><div class="${profit>=0?'gain':'loss'}"><span>仮想損益</span><b>${profit>=0?'+':'−'}${yen(Math.abs(profit))}</b></div></div><div class="be241-item-footer"><span>${out.tickets}点・予想締切前に固定 / 実購入なし</span><a href="${safe(r.result_source)}" target="_blank" rel="noopener noreferrer">公式結果 ↗</a></div></article>`}
function render(){if(!data)return;const mode=ID('be241Mode').value;const rows=data.rows.filter(r=>{const v=r.mode_outcomes?.[mode];return verifiedRow(r)&&v&&(filter==='all'||filter==='hit'&&v.hit||filter==='miss'&&!v.hit||filter==='head'&&r.head_hit)});let chunks=[],last='';for(const r of rows){if(r.date_jst!==last){last=r.date_jst;chunks.push(`<h3 class="be241-date">${dateLabel(last)} <small>検証済み結果</small></h3>`)}chunks.push(modeRow(r,mode))}ID('be241Results').innerHTML=chunks.join('')||'<div class="be241-empty">この条件の検証済みレースはありません。<br>未確定を不的中扱いしません。</div>';ID('be241Scope').textContent=`${modeNames[mode]}・${rows.length}R表示 / 確定${data.settled_verified_races}R`;ID('be241Updated').textContent='保存済み結果（自動更新）'}
async function load(){ID('be241Latest').textContent='サイト限定の検証済み結果を照合中';try{const res=await fetch(API+'?t='+Date.now(),{cache:'no-store'});if(!res.ok)throw Error('HTTP '+res.status);const o=await res.json();if(o.schema!==SCHEMA||o.scope!=='VERIFIED_POST_RESULT_SITE_RESEARCH_ONLY_NOT_FORMAL_FRESH'||o.formal_result_access!==false||o.real_or_paper_wagers_placed!==0||!Array.isArray(o.rows)||o.rows.length!==o.settled_verified_races||!o.rows.every(verifiedRow))throw Error('未確認の結果データ形式');data=o;ID('be241Count').textContent=nf.format(o.settled_verified_races);ID('be241Wins').textContent=nf.format(o.top10_hits);ID('be241Head').textContent=nf.format(o.head_hits);ID('be241Rate').textContent=o.top10_hit_rate_percent===null?'未算定':o.top10_hit_rate_percent+'%';ID('be241Latest').textContent=o.date_latest?`${dateLabel(o.date_latest)}の確定履歴まで掲載`:'検証済み結果はまだありません';render()}catch(e){data=null;ID('be241Latest').textContent='確定結果の検証データを取得できません';ID('be241Results').innerHTML='<div class="be241-empty">結果データを検証できませんでした。<br>未確認の的中表示は行いません。「更新」で再試行できます。</div>';ID('be241Scope').textContent='確認待ち';ID('be241Updated').textContent=''}}
ID('be241Refresh').addEventListener('click',load);ID('be241Mode').addEventListener('change',render);document.querySelectorAll('[data-filter]').forEach(el=>el.addEventListener('click',()=>{filter=el.dataset.filter;document.querySelectorAll('[data-filter]').forEach(x=>x.classList.toggle('on',x===el));render()}));load();
})();
