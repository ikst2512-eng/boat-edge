/* BOAT EDGE independent site-reference research dashboard, V219. Read-only. */
(()=>{'use strict';
 function init(){const root=document.querySelector('#panel-shadow');
  if(!root||document.getElementById('be219-validation'))return;
  const block=document.createElement('section');block.id='be219-validation';block.className='be219-validation';
  const heading=document.createElement('h3');heading.textContent='精度検証の自走状況（正式Freshと別管理）';block.append(heading);
  const info=document.createElement('div');info.className='be219-info';info.textContent='自動監査の記録を取得中';block.append(info);
  const main=document.createElement('div');main.className='be219-data';block.append(main);
  const note=document.createElement('p');note.className='be219-note';note.textContent='未見研究の観測値であり、精度改善・利益・正式採用の証明ではありません。10〜20倍区分は確定払戻による事後分類です。';block.append(note);
  root.prepend(block);
  function text(tag,value,cls){const e=document.createElement(tag);e.textContent=String(value);if(cls)e.className=cls;return e}
  function card(title,r){const el=text('div','', 'be219-card');el.append(text('strong',title));if(r.status!=='VERIFIED_UPSTREAM_SITE_ONLY'){el.append(text('p','原本の監査確認待ち／データ不足'));return el}
    el.append(text('p',`未見採点 ${r.verified_races}R ／ 検証日 ${r.race_dates}日 ／ 払戻10〜20倍 ${r.confirmed_payout_10_20x_races}R`));
    for(const [name,v] of Object.entries(r.candidate_comparisons||{})){
      const box=text('div','', 'be219-line');box.append(text('b',name+'（従来比）'));
      const all=v.all_races||{};
      box.append(text('span', [3,5,10].map(n=>`Top${n} ${all['top'+n]?.candidate_hits??'—'}/${r.verified_races}（差${all['top'+n]?.difference>0?'+':''}${all['top'+n]?.difference??'—'}）`).join(' · ')));
      if(v.top1_head)box.append(text('small',`頭1位 ${v.top1_head.candidate_hits}/${r.verified_races}（差${v.top1_head.difference>0?'+':''}${v.top1_head.difference}）`));
      el.append(box);
    }
    return el;
  }
  async function refresh(){try{
    const response=await fetch('./data/site_autovalidation/current.json?v='+Date.now(),{cache:'no-store'});
    if(!response.ok)throw Error('WAITING_FOR_FIRST_AUTONOMOUS_REPORT');
    const d=await response.json();if(d.schema!=='BOAT_EDGE_SITE_AUTOVALIDATION_V1')throw Error('SCHEMA');
    info.textContent=`集計対象 ${d.date_jst} ／ 状態：${d.performance_claim==='NOT_PROVEN'?'精度改善は未証明':'監査待ち'}`;
    main.replaceChildren(card('V185：3着役割候補',d.site_v185),card('V199：進入・頭・2着等の個別候補',d.site_v199));
    const formal=text('p',`正式Fresh：${d.formal?.readiness||'状態確認待ち'} ／ 正式凍結 ${d.formal?.formal_first100_frozen??0}R`,'be219-formal');main.append(formal);
    const rd=d.readiness||{};main.append(text('p',`直前監査：確認済 ${rd.observed_races??0}R（${rd.checked_at||'取得待ち'}）`,'be219-formal'));
  }catch(e){info.textContent='自動集計の初回実行待ち。数値を推定表示しません。';main.replaceChildren();}}
  refresh();document.querySelector('#simRefresh')?.addEventListener('click',refresh);
  document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')refresh()});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
