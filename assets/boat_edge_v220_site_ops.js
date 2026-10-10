/* V220: live operational evidence only; no browser-side prediction, wagering or gate approval. */
(()=>{'use strict';
const labels={today_schedule_not_confirmed:'当日の出走表待ち',collector_index_stale:'出走表の更新遅延',odds_index_stale:'オッズ更新の遅延',predeadline_incomplete:'直前データ不足',site_validation_report_unavailable:'自動検証レポート未取得',predeadline_diagnostics_not_today:'本日の直前診断未更新',paper_budget_policy_mismatch:'仮想資金設定の監査異常',formal_status_requires_manual_safety_review:'正式Freshの安全状態要確認'};
const query=(s)=>document.querySelector(s);
const jstDay=()=>new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Tokyo',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date()).replaceAll('-','');
function mount(){let host=query('#nextRaceBar')||query('#systemBanner');if(!host||query('#be220Ops'))return;
  let box=document.createElement('section');box.id='be220Ops';box.className='be220-ops';
  box.innerHTML='<div class="be220-line"><strong>サイト自走監視</strong><span id="be220Status" aria-live="polite">情報取得中</span><a href="./ai-simulation.html" aria-label="AI仮想運用と未見検証を見る">検証を見る <span aria-hidden="true">›</span></a></div><p id="be220Info">更新状況を確認中</p>';
  host.insertAdjacentElement('afterend',box);
  async function refresh(){try{let r=await fetch('./data/site_ops_v220/current.json?t='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('missing');let x=await r.json();
    if(x.schema!=='BOAT_EDGE_V220_SITE_AUTONOMOUS_OPERATIONS_V1'||x.scope!=='SITE_ONLY_PRE_RESULT_OPERATIONS_NOT_FORMAL_FRESH'||x.formal_results_read_by_this_runner!==false)throw Error('unverified');
    let outdated=x.day_jst!==jstDay(),status=query('#be220Status'),info=query('#be220Info');
    status.textContent=outdated?'本日の監視記録待ち':(x.status==='NEEDS_ATTENTION'?'データ確認が必要':x.status==='MONITORING_PREDEADLINE'?'直前データを監視中':'直前監視の開始待ち');
    status.className=(outdated||x.status==='NEEDS_ATTENTION')?'be220-issue':'be220-ok';
    const reasons=(x.issues||[]).slice(0,3).map(t=>labels[t]||t);
    let nxt=x.next_race?`${x.next_race.venue} ${String(x.next_race.race_key).slice(-2)}R ${x.next_race.deadline_jst}締切`:'当日の対象レースなし';
    info.textContent=outdated?'本日の保存情報がまだ取得できていません。正常稼働とは判定しません。':`出走 ${x.scheduled_races||0}R ／ 次 ${nxt}${reasons.length?' ／ '+reasons.join('・'):''}。未取得は合格扱いにしません。`;
  }catch(e){const st=query('#be220Status'),info=query('#be220Info');if(st){st.textContent='監視記録未取得';st.className='be220-issue'}if(info)info.textContent='サイトの自動監視データを確認できません。予想精度やオッズの正確性は保証していません。'} }
  refresh();query('#refreshTopBtn')?.addEventListener('click',refresh);document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')refresh();});
  setInterval(()=>{if(document.visibilityState==='visible')refresh()},180000);
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});else mount();
})();
