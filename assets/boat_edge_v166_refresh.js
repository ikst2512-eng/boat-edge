/* BOAT EDGE V166: manual visible page refresh; fetch only existing public site JSON.
   Does not dispatch collectors, touch formal lock, modify model, or invent odds. */
(()=>{'use strict';
  const $=s=>document.querySelector(s);
  const jstDay=()=>new Date(Date.now()+9*3600000).toISOString().slice(0,10).replaceAll('-','');
  let busy=false,toastTimer=null;
  const safeKey=v=>/^\d{8}-\d{2}-\d{2}$/.test(String(v||''));
  function button(){
    let b=$('#be166GlobalRefresh');
    if(b)return b;
    const top=$('.topbar');if(!top)return null;
    b=document.createElement('button');b.type='button';b.id='be166GlobalRefresh';
    b.setAttribute('aria-label','現在のページのデータを更新');
    b.textContent='↻ 更新';
    b.title='現在のページのデータと公開済みオッズを再読込';
    top.appendChild(b);b.addEventListener('click',refresh);
    /* A14: keep the existing handler, but expose just one real manual-refresh action. */
    const duplicate=$('#refreshTopBtn');
    if(duplicate){duplicate.hidden=true;duplicate.tabIndex=-1;duplicate.setAttribute('aria-hidden','true');}
    return b;
  }
  function info(msg){
    let el=$('#be166RefreshStatus');
    if(!el){el=document.createElement('div');el.id='be166RefreshStatus';el.setAttribute('role','status');el.setAttribute('aria-live','polite');document.body.appendChild(el);}
    el.textContent=msg;el.hidden=false;
    clearTimeout(toastTimer);toastTimer=setTimeout(()=>{el.hidden=true;},5500);
  }
  async function freshJson(url){
    const res=await fetch(url+(url.includes('?')?'&':'?')+'be166='+Date.now(),{cache:'no-store'});
    if(!res.ok)throw new Error('HTTP '+res.status);
    return res.json();
  }
  /* A13: values are source-reported, never a fresh collection triggered by this button. */
  function oddsLabel(doc,r,now=Date.now()){
    if(!doc||doc.race_key!==r?.race_key)return '公式3連単オッズ：取得元・時刻未確認';
    const proof=window.BoatEdgeV222Odds?.validate?.(doc,r,now);
    const q=proof?.quality;
    if(q==='past_deadline')return '公式3連単オッズ：締切済み・購入前の現在オッズとして表示不可';
    if(q!=='fresh'&&q!=='stale')return '公式3連単オッズ：証跡不一致・表示不可';
    const at=new Date(doc.fetched_at);
    if(!Number.isFinite(at.getTime()))return '公式3連単オッズ：取得時刻不正';
    const stamp=at.toLocaleTimeString('ja-JP',{timeZone:'Asia/Tokyo',hour:'2-digit',minute:'2-digit'});
    return '取得元 BOAT RACE公式 / '+stamp+' JST取得 / '+(q==='fresh'?'確認済み保存値（リアルタイムではない）':'古い保存値（最新として利用不可）');
  }
  async function refresh(){
    if(busy)return;
    busy=true;const b=button();if(b){b.disabled=true;b.textContent='更新中…';}
    info('データを確認中…');
    const problems=[];
    let oddsMessage='';
    try{
      if(typeof refreshAll==='function')await refreshAll(true);
      else problems.push('更新処理未接続');
    }catch(_){problems.push('サイト全体の更新に失敗');}
    try{await window.BoatEdgeV163?.refresh?.();}catch(_){problems.push('レース一覧の更新に失敗');}
    const active=$('.view.active')?.id;
    if(active==='homeView'){try{await window.BoatEdgeV166RefreshHome?.();}catch(_){problems.push('ホーム一覧の再描画に失敗');}}
    if(active==='raceView'){
      let race=null;try{race=typeof state!=='undefined'?state.race:null;}catch(_){}
      const key=String(race?.race_key||'');
      if(safeKey(key)&&key.slice(0,8)===jstDay()){
        try{
          window.BoatEdgeV166Invalidate?.(key);
          const incoming=await freshJson('./data/races/'+key+'.json');
          if(incoming.race_key!==key)throw new Error('race_key mismatch');
          if(incoming.meta?.results_seen!==false||incoming.meta?.unlock!==false||incoming.meta?.scoring!==false)throw new Error('PRE_RESULT guard');
          let overlay=null;
          if(typeof loadFormalOverlay==='function')overlay=await loadFormalOverlay(key);
          if(typeof state!=='undefined' && state.race?.race_key===key && typeof renderRace==='function'){
            const finalRace=typeof mergeFormalOverlay==='function'?mergeFormalOverlay(incoming,overlay):incoming;
            renderRace(finalRace,{silent:true});
          }
          // Re-fetch official odds file, without claiming that GitHub collector has run again.
          const odds=await freshJson('./data/site_odds/'+key+'.json').catch(()=>null);
          oddsMessage=oddsLabel(odds,incoming);
          try{await window.BoatEdgeV223Source?.refresh?.();}catch(_){problems.push('取得状態の表示更新に失敗');}
        }catch(_){problems.push('表示中レースの再読込に失敗');}
      }
    }
    if(problems.length)info('一部未更新：'+problems.join('・')+(oddsMessage?' ／ '+oddsMessage:''));
    else if(oddsMessage)info('公開済み情報を再読込。'+oddsMessage+'。新規収集は行いません');
    else info('公開済み情報を再読込。公式オッズの新規収集・保存済み買い目の変更は行いません');
    if(b){b.disabled=false;b.textContent='↻ 更新';}
    busy=false;
  }
  function init(){button();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
  window.BoatEdgeV166Refresh={refresh};
  window.BoatEdgeV166Refresh.oddsLabel=oddsLabel;
})();
