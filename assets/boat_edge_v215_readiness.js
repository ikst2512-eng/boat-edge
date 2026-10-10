/* V215: show forward-only data readiness. No changes to wagers or prediction engine. */
(()=>{'use strict';
 const $=(sel,root=document)=>root.querySelector(sel);
 const SOURCE_DETAILS={race_file_missing:'レース情報未保存',six_racers_unverified:'出走6艇未確認',race_card_not_ok:'公式出走表未取得',race_card_stale:'公式出走表が古い',beforeinfo_not_ok:'公式直前情報未取得',beforeinfo_stale:'公式直前情報が古い',scratch_missing_or_blocked:'欠場確認不足・取消警告',scratch_stale:'欠場確認が古い',pre_result_odds_unverified:'締切前オッズ未確認',pre_result_odds_stale:'締切前オッズが古い'};
 const TEXT={snapshot_missing:'予想未保存',snapshot_invalid:'保存形式不正',snapshot_not_eligible:'予想モデル対象外',pre_result_guard_failed:'結果未参照ガード不一致',snapshot_time_invalid:'予想時刻不正',outside_decision_window:'購入時間外',not_final15:'直前予想でない',snapshot_stale:'予想が古い',snapshot_audit_sha_failed:'予想監査SHA不一致',scratch_unknown_or_blocked:'欠場・取消確認不足',scratch_source_stale:'欠場情報が古い',odds_sha_mismatch_or_missing:'保存オッズSHA不一致',odds_time_or_source_invalid:'オッズ取得時刻不正',odds_source_stale:'オッズが古い',no_raw_ev_candidate_8_25x:'期待値候補なし',verified_shadow_ready:'証跡一致（シャドー候補）'};
 function init(){const pane=$('#panel-shadow');if(!pane||$('#be215Readiness'))return;
  const box=document.createElement('section');box.id='be215Readiness';box.className='be215-readiness';
  box.innerHTML='<div class="be215-top"><strong>次の直前検証</strong><span id="be215Next">確認中</span></div><div class="be215-small" id="be215Summary">当日のレースを確認中</div><div id="be215Window"></div><div id="be215History" class="be215-small"></div>';
  pane.insertBefore(box,$('#be214Status')||$('.be213-stats',pane));
  async function refresh(){try{
    const res=await fetch('./data/site_paper_sim/readiness_v215_current.json?t='+Date.now(),{cache:'no-store'});
    if(!res.ok)throw Error('no readiness'); const data=await res.json();
    if(data.schema!=='BOAT_EDGE_V215_PRE_RESULT_READINESS_V1'||data.not_a_purchase_or_proven_accuracy!==true)throw Error('schema');
    const nxt=data.next_race;
    $('#be215Next').textContent=nxt?`${nxt.venue} ${nxt.race_key.split('-')[2]}R ${nxt.deadline}締切（${nxt.watch_start}から）`:'当日残りレースなし';
    $('#be215Summary').textContent=`出走表 ${data.scheduled_races||0}R / 現在の直前検証 ${data.window_races||0}R / 本日確認済 ${data.day_observed_races||0}R`;
    const place=$('#be215Window');place.replaceChildren();
    for(const row of (data.current_window||[]).slice(0,6)){
      const p=document.createElement('p');p.className='be215-item';
      const gaps=(row.source_gaps||[]).map(k=>SOURCE_DETAILS[k]||k);
      p.textContent=`${row.venue} ${row.race_key.split('-')[2]}R（${row.deadline}） ${TEXT[row.reason]||row.reason}${gaps.length?' ／ 不足情報：'+gaps.join('・'):''}`;place.appendChild(p);
    }
    const h=data.day_latest_reasons||{};
    $('#be215History').textContent=Object.keys(h).length?`本日の最終確認記録：${Object.entries(h).sort((a,b)=>b[1]-a[1]).slice(0,5).map(([k,v])=>`${TEXT[k]||k} ${v}R`).join(' / ')}`:'締切前の監査記録を蓄積中。結果は使用しません。';
    if(!data.schedule_source_today)$('#be215Summary').textContent='当日の出走表待ち';
   }catch(e){$('#be215Summary').textContent='直前検証の保存記録待ち。未確認のデータは合格扱いにしません。';}
  }refresh();$('#simRefresh')?.addEventListener('click',refresh);
  // Lightweight updates; table changes are passive; no browser-side purchase decisions.
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')refresh()});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
