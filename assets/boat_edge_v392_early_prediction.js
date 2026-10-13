/* V392: Pre-result racelist-only preview. Never a frozen final, calibrated
 * probability, formal CURRENT, official odds, result, payout, or stake. */
(()=>{'use strict';
if(window.BoatEdgeV392)return;
const MODEL='V392-CARD-HEURISTIC-UNCALIBRATED',SCHEMA='BOAT_EDGE_V392_CARD_ONLY_PREVIEW_V1';
const keyOK=k=>/^20\d{6}-(?:0[1-9]|1\d|2[0-4])-(?:0[1-9]|1[0-2])$/.test(String(k||''));
const shaOK=k=>/^[a-f0-9]{64}$/.test(String(k||''));
const comboOK=s=>/^[1-6]-[1-6]-[1-6]$/.test(String(s||''))&&new Set(s.split('-')).size===3;
const $=(s,r=document)=>r.querySelector(s);
const text=(el,value)=>{if(el)el.textContent=String(value??'');};
let serial=0,activeKey='',shown=10;
function cardSafety(r,now=Date.now()){
 const key=r?.race_key,meta=r?.meta||{};
 if(!keyOK(key)||String(meta.venue_code||'').padStart(2,'0')!==key.slice(9,11)||
    meta.race_no!==Number(key.slice(12,14)))return {ok:false,reason:'レースID照合待ち'};
 const date=key.slice(0,4)+'-'+key.slice(4,6)+'-'+key.slice(6,8);
 if(meta.date!==date||!/^([01]\d|2[0-3]):[0-5]\d$/.test(String(meta.deadline||'')))
  return {ok:false,reason:'日付・締切予定の照合待ち'};
 const due=Date.parse(date+'T'+meta.deadline+':00+09:00');
 if(!Number.isFinite(due)||now>=due)return {ok:false,reason:'締切済み（後付け暫定予想なし）'};
 if(meta.phase!=='PRE_RESULT'||meta.results_seen!==false||meta.unlock!==false||meta.scoring!==false)
  return {ok:false,reason:'結果未見の条件を確認できません'};
 const source=r?.source_audit?.race_card||{},fetched=Date.parse(String(source.fetched_at||''));
 if(source.status!=='ok'||!shaOK(source.sha256)||!Number.isFinite(fetched)||
    fetched>now+60000||fetched>=due)return {ok:false,reason:'公式出走表の取得証跡が未確認'};
 const racers=r?.racers;
 if(!Array.isArray(racers)||racers.length!==6)return {ok:false,reason:'6艇の出走表が未取得'};
 const lanes=racers.map(x=>x?.lane).sort((a,b)=>a-b);
 const regs=racers.map(x=>String(x?.registration_no||''));
 if(lanes.join(',')!=='1,2,3,4,5,6'||new Set(regs).size!==6||
    regs.some(x=>!/^\d{4}$/.test(x)))return {ok:false,reason:'6艇の登録番号・枠番に不一致'};
 for(const row of racers){
  if(['scratched','withdrawn','absent','cancelled','canceled'].some(k=>row?.[k]===true)||
    /欠場|出走取消|取消|不出走|scratched|withdrawn/i.test(
      [row?.raw_text,row?.status,row?.entry_status,row?.race_status].filter(x=>typeof x==='string').join(' ')))
   return {ok:false,reason:'出走取消・欠場の表示あり'};
 }
 if(r?.scratch_audit?.blocked===true)return {ok:false,reason:'公式欠場・取消確認で停止'};
 return {ok:true,due};
}
function inputs(r){
 return [...r.racers].sort((a,b)=>a.lane-b.lane).map(x=>[
  x.lane,x.registration_no,x.class,x.avg_st??null,
  x.national?.win_rate??null,x.local?.win_rate??null,x.motor?.quinella_rate??null
 ]);
}
function previewSafety(r,p,now=Date.now()){
 const c=cardSafety(r,now);if(!c.ok)return c;
 if(!p||p.schema!==SCHEMA||p.model_id!==MODEL||p.race_key!==r.race_key||
    p.prediction_kind!=='EARLY_CARD_ONLY_REFERENCE_NOT_FINAL'||
    p.source_date!==r.meta.date||p.deadline!==r.meta.deadline||
    p.guards?.results_seen!==false||p.guards?.unlock!==false||p.guards?.scoring!==false||
    p.formal_fresh_claim!==false||p.score_is_calibrated_probability!==false||
    p.odds_used!==false||p.betting_enabled!==false||p.stake_yen!==null)
  return {ok:false,reason:'暫定予想のソース・モデル照合待ち'};
 const produced=Date.parse(p.produced_at),fetched=Date.parse(p.source_card_fetched_at);
 if(!Number.isFinite(produced)||!Number.isFinite(fetched)||produced>now+60000||
    produced>=c.due||fetched>produced+60000||!shaOK(p.source_card_sha256)||
    !shaOK(p.card_fingerprint_sha256)||
    p.source_card_sha256!==r.source_audit.race_card.sha256||
    p.source_card_fetched_at!==r.source_audit.race_card.fetched_at)
  return {ok:false,reason:'予想の生成時刻・公式出走表SHAが未確認'};
 if(JSON.stringify(p.racer_inputs_by_lane)!==JSON.stringify(inputs(r)))
  return {ok:false,reason:'出走表が更新済み：暫定予想を再計算中'};
 const rows=p.ranked_120;
 if(!Array.isArray(rows)||rows.length!==120)return {ok:false,reason:'120通りの参考順位が未確認'};
 const combos=rows.map(x=>x?.combo);
 if(combos.some(x=>!comboOK(x))||new Set(combos).size!==120||
    rows.some((x,i)=>x.rank!==i+1||typeof x.relative_score!=='number'||
      !Number.isFinite(x.relative_score)||
      (i>0&&x.relative_score>rows[i-1].relative_score+1e-8)))
  return {ok:false,reason:'順位・重複の検証で不一致'};
 for(const [n,field] of [[3,'top3'],[5,'top5'],[10,'top10']]){
  if(!Array.isArray(p[field])||JSON.stringify(p[field])!==JSON.stringify(combos.slice(0,n)))
   return {ok:false,reason:'Top3・Top5・Top10の順位が不一致'};
 }
 if(p.head_candidate!==Number(combos[0][0]))return {ok:false,reason:'頭候補とTop1の不一致'};
 return {ok:true,due:c.due,produced};
}
function ensure(){
 const stack=$('#tab-pred .section.stack');if(!stack)return null;
 let box=$('#be392EarlyPreview');
 if(!box){
  box=document.createElement('section');box.id='be392EarlyPreview';box.className='be392-preview';
  box.setAttribute('aria-label','出走表ベースの前日・暫定予想');
  const anchor=$('#predictionAlert',stack);
  if(anchor)anchor.insertAdjacentElement('afterend',box);else stack.prepend(box);
 }
 return box;
}
function style(){
 if($('#be392EarlyStyle'))return;
 const el=document.createElement('style');el.id='be392EarlyStyle';
 el.textContent=[
 '.be392-preview{display:none;background:#f0f6ff;border:1px solid #bed4f1;border-radius:14px;padding:14px;color:#122f54}',
 '.be392-preview[data-ready="true"],.be392-preview[data-ready="status"]{display:block}',
 '.be392-header{display:flex;gap:8px;flex-wrap:wrap;align-items:center;justify-content:space-between}',
 '.be392-header strong{font-size:17px}.be392-tag{font-size:11px;font-weight:800;color:#6d4300;background:#fff0c9;padding:5px 8px;border-radius:5px}',
 '.be392-meta{font-size:12px;line-height:1.6;color:#345371;margin-top:8px}',
 '.be392-tabs{display:flex;gap:6px;margin-top:12px}',
 '.be392-tabs button{flex:1;font:inherit;font-size:13px;font-weight:800;border:1px solid #a6bfdd;color:#234b73;background:#fff;padding:9px 3px;border-radius:7px;cursor:pointer}',
 '.be392-tabs button[aria-pressed="true"]{background:#174c83;color:#fff;border-color:#174c83}',
 '.be392-lines{margin:10px 0 0;padding:0;list-style:none;display:grid;gap:5px}',
 '.be392-lines li{display:flex;justify-content:space-between;gap:12px;border:1px solid #dae6f6;background:#fff;padding:9px 12px;border-radius:8px}',
 '.be392-lines .combo{font-weight:900;font-variant-numeric:tabular-nums;font-size:17px;letter-spacing:.05em}',
 '.be392-lines .rank{color:#59738f;font-size:12px;font-weight:800}',
 '.be392-note{font-size:11px;line-height:1.6;color:#456582;margin-top:12px}',
 '@media(max-width:580px){.be392-preview{padding:11px}.be392-header strong{font-size:15px}.be392-lines .combo{font-size:16px}}'
 ].join('');
 document.head.appendChild(el);
}
function drawRows(box,p){
 const list=$('.be392-lines',box);if(!list)return;
 list.replaceChildren();
 for(const row of p.ranked_120.slice(0,shown)){
  const li=document.createElement('li'),rank=document.createElement('span'),combo=document.createElement('span');
  rank.className='rank';combo.className='combo';text(rank,'#'+row.rank);text(combo,row.combo);
  li.append(rank,combo);list.append(li);
 }
 for(const btn of box.querySelectorAll('.be392-tabs button[data-count]'))
  btn.setAttribute('aria-pressed',String(Number(btn.dataset.count)===shown));
}
function showStatus(r,reason){
 const box=ensure();if(!box)return;
 box.replaceChildren();
 box.dataset.ready='status';
 box.dataset.raceKey=String(r?.race_key||'');
 box.setAttribute('role','status');
 box.innerHTML='<div class="be392-header"><strong>出走表ベースの暫定予想</strong>'+
  '<span class="be392-tag">未凍結・参考順位</span></div><div class="be392-meta"></div>'+
  '<div class="be392-note">締切前の正式予想・購入配分・的中判定とは別です。</div>';
 text($('.be392-meta',box),reason);
}
function showPreview(r,p){
 const box=ensure();if(!box)return;
 box.dataset.ready='true';box.dataset.raceKey=r.race_key;box.removeAttribute('role');
 if(!$('.be392-header',box)){
  box.innerHTML='<div class="be392-header"><strong>出走表ベースの暫定予想</strong><span class="be392-tag">未凍結・参考順位</span></div>'+
   '<div class="be392-meta"></div><div class="be392-tabs" role="group" aria-label="暫定予想の買い目件数">'+
   '<button type="button" data-count="3">Top3</button><button type="button" data-count="5">Top5</button>'+
   '<button type="button" data-count="10">Top10</button></div>'+
   '<ol class="be392-lines" aria-label="出走表ベース参考3連単順位"></ol>'+
   '<div class="be392-note">120通りを全国勝率・級別・モーター・平均ST・仮の枠なり進入で評価した参考順位。展示ST・実進入・オッズ未反映。確率は未校正。購入配分・想定払戻・的中判定・正式CURRENTとは連動しません。</div>';
  $('.be392-tabs',box).addEventListener('click',e=>{
   const button=e.target.closest('button[data-count]');if(!button)return;
   const value=Number(button.dataset.count);if(![3,5,10].includes(value))return;
   shown=value;drawRows(box,p);
  });
 }
 const stamp=new Date(p.produced_at).toLocaleString('ja-JP',{
  timeZone:'Asia/Tokyo',month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'});
 text($('.be392-meta',box),'出走表 '+stamp+'時点の試算 ／ 頭候補 '+p.head_candidate+
    '号艇（Top1の1着） ／ Top3・Top5・Top10は同じ120通り順位の先頭部分');
 drawRows(box,p);
}
function hide(){
 const box=$('#be392EarlyPreview');if(box){box.dataset.ready='false';box.replaceChildren();box.dataset.raceKey='';box.removeAttribute('role');}
}
async function render(r){
 const ticket=++serial,key=String(r?.race_key||'');activeKey=key;
 const guard=cardSafety(r);
 if(!guard.ok){
  if(keyOK(key)&&r?.meta?.phase==='PRE_RESULT'&&guard.reason!=='締切済み（後付け暫定予想なし）'){
   style();showStatus(r,guard.reason);
  }else hide();
  return;
 }
 style();
 if(!ensure())return;
 showStatus(r,'暫定予想の保存データを確認中です。');
 try{
  const res=await fetch('./data/site_early_previews/'+key+'.json?early='+Date.now(),{cache:'no-store'});
  if(!res.ok){
   if(res.status===404)throw new Error('PREVIEW_NOT_PUBLISHED');
   throw new Error('PREVIEW_HTTP_'+res.status);
  }
  const p=await res.json();
  if(ticket!==serial||activeKey!==key)return;
  const checked=previewSafety(r,p);
  if(!checked.ok){showStatus(r,checked.reason);return;}
  showPreview(r,p);
 }catch(e){
  if(ticket!==serial||activeKey!==key)return;
  const reason=String(e?.message||'');
  showStatus(r,reason==='PREVIEW_NOT_PUBLISHED'
   ?'暫定予想データはまだ公開されていません。出走表の収集・予想生成後に再表示してください。'
   :'暫定予想データを読み込めませんでした。通信または公開データを確認して再読み込みしてください。');
 }
}
function tick(){
 const box=$('#be392EarlyPreview');if(!box||!['true','status'].includes(box.dataset.ready))return;
 const key=box.dataset.raceKey;
 const r=(()=>{try{return typeof state!=='undefined'?state?.race:null;}catch(_){return null;}})();
 if(key!==r?.race_key||!cardSafety(r).ok)hide();
}
function init(){style();setInterval(tick,30000);}
window.BoatEdgeV392={render,cardSafety,previewSafety,hide,version:'V392-CARD-ONLY-UNFROZEN'};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();