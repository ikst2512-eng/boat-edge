/* V170: BOAT EDGE prediction performance by venue, audited website reference ONLY. */
(()=>{'use strict';
 const $=(s,r=document)=>r.querySelector(s),esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const MODES={hit:'的中重視',balance:'バランス',hole:'波乱展開',narrow:'激絞り'};
 let data=null,until=0,pending=null,choice='hit',sort='races',renderKey='';
 const num=v=>(v===null||v===undefined||!Number.isFinite(Number(v)))?null:Number(v);
 const pct=v=>num(v)===null?'－':Number(v).toFixed(1)+'%';
 const money=v=>num(v)===null?'－':Math.round(v).toLocaleString('ja-JP')+'円';
 const activeRace=()=>{try{return typeof state==='undefined'?null:state.race}catch(_){return null}};
 async function load(force=false){
  if(!force&&data&&Date.now()<until)return data;
  if(pending)return pending;
  pending=(async()=>{try{const r=await fetch('./data/site_learning/mode_venue_accuracy_v170.json?v=170&t='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);
   const v=await r.json();if(v.schema_version!=='boat-edge-site-prediction-venue-v170'||v.scope!=='SITE_REFERENCE_POST_SETTLEMENT_ONLY_NOT_FORMAL_FRESH'||v.production_prediction_weights_changed!==false||v.formal_fresh_scoring!==false||!v.venues)throw Error('bad source');
   data=v;until=Date.now()+150000;return data;
  }catch(e){return data}finally{pending=null}})();return pending;
 }
 function prepare(){
  let global=$('#be170PredictionVenueGlobal');
  if(!global){const host=$('#dataView .section');if(host){global=document.createElement('section');global.id='be170PredictionVenueGlobal';global.className='be170-panel';host.insertAdjacentElement('afterbegin',global)}}
  let race=$('#be170PredictionVenueRace');
  if(!race){const host=$('#tab-pred .section.stack');if(host){race=document.createElement('section');race.id='be170PredictionVenueRace';race.className='be170-panel';host.insertAdjacentElement('afterbegin',race)}}
  return {global,race};
 }
 function renderGlobal(root){
  if(!root)return;
  if(!data){root.innerHTML='<h3>BOAT EDGE 予想の場別成績</h3><p>集計待ち（推定表示はしません）</p>';return;}
  const v=Object.values(data.venues);
  v.sort((a,b)=>{const x=a.modes[choice],y=b.modes[choice];if(sort==='hit_rate')return (b.races&&b.races>=5?num(y.hit_rate_pct):-1)-(a.races&&a.races>=5?num(x.hit_rate_pct):-1)||b.races-a.races;
   if(sort==='roi')return (b.races>=5?num(y.roi_pct):-1)-(a.races>=5?num(x.roi_pct):-1)||b.races-a.races;
   return b.races-a.races||a.venue_code.localeCompare(b.venue_code)});
  root.innerHTML='<h3>BOAT EDGE 予想の得意場・場別成績</h3>'+ 
   '<p class="be170-caution">選手の得意場とは別。サイト参考予想の締切前保存買い目と公式確定払戻を照合。<b>本当に得意と認定した場はまだありません。</b> 凍結済み正式Freshとは別集計。</p>'+
   '<div class="be170-summary">集計 '+data.audited_races+'R / '+data.distinct_days+'日 / '+v.filter(x=>x.races>0).length+'場 · 除外 '+data.excluded+'R</div>'+
   '<div class="be170-modes">'+Object.entries(MODES).map(([key,name])=>'<button type="button" data-be170-mode="'+key+'" class="'+(key===choice?'on':'')+'">'+name+'</button>').join('')+'</div>'+
   '<label class="be170-sort-label">並べ替え <select id="be170VenueSort"><option value="races" '+(sort==='races'?'selected':'')+'>検証R数</option><option value="hit_rate" '+(sort==='hit_rate'?'selected':'')+'>的中率（5R以上）</option><option value="roi" '+(sort==='roi'?'selected':'')+'>回収率（5R以上）</option></select></label>'+
   '<div class="be170-table-scroll"><table class="be170-table"><thead><tr><th>場</th><th>検証</th><th>的中率</th><th>回収率</th><th>収支</th><th>非1頭的中</th></tr></thead><tbody>'+
   v.map(x=>{const m=x.modes[choice],observed=x.races>=5;const status=x.status==='REFERENCE_COMPARABLE'?'比較候補':'参考・標本少';
    return '<tr><th>'+esc(x.name)+'<small>'+esc(x.status==='NO_DATA'?'未検証':status)+'</small></th><td>'+x.races+'R / '+x.distinct_days+'日</td><td>'+ (observed?pct(m.hit_rate_pct):'－')+'<small>'+m.hits+'/'+x.races+' 的中</small></td><td>'+(observed?pct(m.roi_pct):'－')+'</td><td>'+(observed?money(m.net_yen):'－')+'</td><td>'+(observed&&x.winning_non1_races?m.non1_hits+'/'+x.winning_non1_races+' ('+pct(m.non1_hit_rate_pct)+')':'－')+'</td></tr>';
   }).join('')+'</tbody></table></div><p class="be170-caution">5R未満は率を非表示。30Rかつ3日以上で「比較候補」とするが、正式な得意場認定は別日の未見検証が必要。回収率は各R1万円の保存済み参考配分、実購入ではありません。</p>';
  root.querySelectorAll('[data-be170-mode]').forEach(b=>b.addEventListener('click',()=>{choice=b.dataset.be170Mode;renderKey='';draw(true)}));
  $('#be170VenueSort',root)?.addEventListener('change',e=>{sort=e.target.value;renderKey='';draw(true)});
 }
 function renderRace(root){
  if(!root)return;
  const race=activeRace(),code=String(race?.meta?.venue_code||'').padStart(2,'0');if(!data||!data.venues[code]){root.innerHTML='';return;}
  const x=data.venues[code];
  root.innerHTML='<h4>BOAT EDGEのこの場での予想実績 <small>参考・未認定</small></h4>'+ 
   '<p>'+esc(x.name)+'：監査済み '+x.races+'R / '+x.distinct_days+'日。'+(x.races<5?'標本が少ないため的中率・回収率は非表示。':'4モードの実績比較。')+'</p>'+ 
   (x.races>=5?'<div class="be170-race-grid">'+Object.entries(MODES).map(([k,name])=>'<span><b>'+name+'</b> 的中 '+pct(x.modes[k].hit_rate_pct)+' / 回収 '+pct(x.modes[k].roi_pct)+'</span>').join('')+'</div>':'')+
   '<p class="be170-caution">予想自体の順位や確率は変更しません。選手の得意場とは別の、過去の参考予想実績。</p>';
 }
 async function draw(force=false){
  const {global,race}=prepare(),cur=activeRace(),signature=[data?.audited_races,data?.distinct_days,cur?.race_key,choice,sort].join('|');
  if(!force&&renderKey===signature)return;
  renderKey=signature;renderGlobal(global);renderRace(race);
 }
 async function refresh(force=false){const d=await load(force);await draw(force);return d}
 function start(){prepare();refresh(true);document.addEventListener('click',e=>{if(e.target.closest('[data-view],#raceTabs [data-tab],.be163-race'))setTimeout(()=>draw(true),150)});
  setInterval(()=>{refresh(Date.now()>until);},30000);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh(true)});
 }
 window.BoatEdgeV170={refresh:()=>refresh(true)};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
