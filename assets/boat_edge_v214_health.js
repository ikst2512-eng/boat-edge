/* V214 pre-result source health, separate from P&L and formal scoring. */
(()=>{'use strict';
function init(){const panel=document.querySelector('#panel-shadow');if(!panel||document.querySelector('#be214Status'))return;
const b=document.createElement('div');b.id='be214Status';b.className='be214-status';b.textContent='直前データの検証状況を確認中…';panel.insertBefore(b,panel.querySelector('.be213-stats'));
async function refresh(){try{const r=await fetch('./data/site_paper_sim/preflight_v214_current.json?t='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('404');const v=await r.json();if(v.schema!=='BOAT_EDGE_V214_PRE_RESULT_DIAGNOSTIC_V1'||v.scope!=='SITE_ONLY_PRE_RESULT_NO_RESULT_READ')throw Error('schema');
const n=v.reason_counts||{};let main=v.window_races?`直前 ${v.window_races}R / 証跡一致 ${n.verified_shadow_ready||0}R`:'現在、締切15〜2分前の確認対象なし';
if(!v.schedule_source_today)main='当日出走表の更新待ち';
const errors=Object.entries(n).filter(([k])=>k!=='verified_shadow_ready').sort((a,b)=>b[1]-a[1]);
if(errors.length)main+='｜不足 '+errors.map(([k,v])=>({snapshot_missing:'予想未保存',snapshot_audit_sha_failed:'予想監査未一致',scratch_unknown_or_blocked:'欠場確認不足',scratch_source_stale:'欠場情報が古い',odds_sha_mismatch_or_missing:'オッズ証跡未一致',odds_time_or_source_invalid:'オッズ時刻不適合',odds_source_stale:'オッズが古い',no_raw_ev_candidate_8_25x:'対象の買い目なし'}[k]||k)+':'+v+'R').join(' / ');
b.textContent=main;}catch(e){b.textContent='直前データ検証の記録待ち。未確認を合格とは表示しません。';}}
refresh();document.querySelector('#simRefresh')?.addEventListener('click',refresh);}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
