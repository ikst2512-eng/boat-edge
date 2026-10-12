/* BOAT EDGE V223: only visible source availability/freshness; never a pick, payout,
   permission, result, formal, or wager authority. Unverified states remain unverified. */
(()=>{'use strict';
if(window.BoatEdgeV223Source)return;
const KEY=/^20\d{6}-\d{2}-\d{2}$/;
const nowDay=()=>new Date(Date.now()+9*3600000).toISOString().slice(0,10).replaceAll('-','');
const validTime=s=>{const t=Date.parse(s||'');return Number.isFinite(t)?t:NaN;};
const due=r=>{const k=String(r?.race_key||''),h=String(r?.meta?.deadline||'');
 if(!KEY.test(k)||!/^\d{1,2}:\d{2}$/.test(h))return NaN;
 return Date.parse(k.slice(0,4)+'-'+k.slice(4,6)+'-'+k.slice(6,8)+'T'+h.padStart(5,'0')+':00+09:00');};
const jst=iso=>{const t=validTime(iso);return Number.isFinite(t)?new Date(t).toLocaleTimeString('ja-JP',{timeZone:'Asia/Tokyo',hour:'2-digit',minute:'2-digit'}):'時刻不明';};
function source(e,required,r,now,cutoffMinutes=20){
 if(e?.status!=='ok'){
  if(['not_in_window','published_wait','not_published'].includes(e?.status))return ['wait','公開待ち'];
  return ['unknown','未取得・未確認'];
 }
 const t=validTime(e.fetched_at),limit=due(r);
 if(!Number.isFinite(t)||!Number.isFinite(limit)||t>limit||t>now+30000)return ['unknown','取得時刻不正／締切後'];
 if(now-t>cutoffMinutes*60000)return ['stale','古い '+jst(e.fetched_at)];
 if(!required)return ['unknown','内容の照合不足'];
 return ['ok',jst(e.fetched_at)+'取得'];
}
/* A06: independent third-party collection must be explicitly logged, never inferred from CSV. */
function providerEvidence(record,hostPattern,r,now){
 if(record?.status!=='ok')return ['unknown','未取得（独立照合なし）'];
 const url=String(record.source||''),hash=String(record.sha256||''),at=validTime(record.fetched_at),end=due(r);
 if(!hostPattern.test(url)||!/^[a-f0-9]{64}$/i.test(hash)||!Number.isFinite(at)||
    !Number.isFinite(end)||at>end||at>now+30000)
   return ['unknown','取得証跡不一致・未確認'];
 if(now-at>25*60000)return ['stale','以前の照合 '+jst(record.fetched_at)+'（現在値ではない）'];
 return ['ok','独立取得 '+jst(record.fetched_at)+'（数値一致は別確認）'];
}
function inspect(r,scratch,odds,now=Date.now()){
 const key=String(r?.race_key||''),end=due(r),pre=KEY.test(key)&&r?.meta?.phase==='PRE_RESULT'&&
  r.meta.results_seen===false&&r.meta.unlock===false&&r.meta.scoring===false;
 if(!pre||!Number.isFinite(end))return {key,phase:'INVALID',rows:[],level:'stop',summary:'予想データの安全条件を確認できません'};
 if(now>=end)return {key,phase:'AFTER_DEADLINE',rows:[],level:'wait',summary:'締切後：現在の取得値を締切前の予想証跡として扱いません'};
 const audit=r.source_audit||{},before=r.beforeinfo||{};
 const hasEx=Array.isArray(before.racers)&&before.racers.length===6&&
   before.racers.every(x=>typeof x?.exhibition_time==='number'&&Number.isFinite(x.exhibition_time)&&x.exhibition_time>0);
 const orig=r.original_exhibition||{};
 const hasOrig=Array.isArray(orig.labels)&&orig.labels.length>=1&&Array.isArray(orig.boats)&&orig.boats.length===6&&
  orig.boats.filter(x=>Array.isArray(x.values)&&x.values.some(v=>typeof v==='number'&&Number.isFinite(v)&&v>0)).length===6;
 const starters=Array.isArray(r.actual_entry)?r.actual_entry:[];
 const entryCourses=starters.map(x=>Number(x?.course));
 const hasStt=starters.length===6&&entryCourses.slice().sort((a,b)=>a-b).join(',')==='1,2,3,4,5,6'&&
   starters.filter(x=>x.exhibition_f===true||typeof x.exhibition_st==='number'||typeof x.exhibition_st_raw==='number').length===6;
 const hasTkz=Array.isArray(before.racers)&&before.racers.filter(x=>typeof x.exhibition_time==='number'&&Number.isFinite(x.exhibition_time)&&x.exhibition_time>0).length===6;
 const rows=[
   ['公式直前',...source(audit.beforeinfo,hasEx,r,now)],
   ['展示ST・進入',...source(audit.stt,hasStt,r,now,25)],
   ['展示タイム',...source(audit.tkz,hasTkz,r,now,25)],
   ['オリ展',...source(audit.original_exhibition,hasOrig,r,now,25)]
 ];
 let sc=['unknown','欠場・取消 未照合'];
 if(scratch?.race_key===key&&scratch.blocked===true)sc=['stop','欠場・取消の疑い（買い目停止）'];
 else if(scratch?.race_key===key&&scratch.blocked===false){
  const t=validTime(scratch.checked_at);
  if(Number.isFinite(t)&&t<=now+30000&&t<=end&&now-t<=15*60000&&scratch.race_card_source_status==='ok')
   sc=['limited','取消信号なし '+jst(scratch.checked_at)+'（出走確定ではない）'];
  else sc=['stale','再照合待ち（出走確定ではない）'];
 }
 rows.push(['欠場・取消',...sc]);
 let odd=['unknown','公式オッズ未取得'];
 if(odds&&window.BoatEdgeV222Odds?.validate){
  const status=window.BoatEdgeV222Odds.validate(odds,r,now).quality;
  odd=status==='fresh'?['ok',jst(odds.fetched_at)+'取得（リアルタイムではない）']:
    status==='stale'?['stale','取得値が古い '+jst(odds.fetched_at)]:['unknown','照合不一致・表示不可'];
 }
 rows.push(['3連単オッズ',...odd]);
 rows.push(['BOATERSオリ展',...providerEvidence(audit.boaters_original_exhibition,
   /^https:\/\/(?:www\.)?boaters-boatrace\.com\//i,r,now)]);
 rows.push(['競艇日和オリ展',...providerEvidence(audit.keiteibiyori_original_exhibition,
   /^https:\/\/(?:www\.)?kyoteibiyori\.com\//i,r,now)]);
 const level=sc[0]==='stop'?'stop':rows.some(x=>x[1]==='unknown'||x[1]==='stale'||x[1]==='wait')?'wait':'limited';
 const ready=rows.filter(x=>x[1]==='ok').length;
 const remaining=Math.ceil((end-now)/60000);
 return {key,phase:'PRE_RESULT',level,rows,summary:sc[0]==='stop'?'欠場・取消疑い：予想に使わない':
    `締切${remaining}分前／取得確認 ${ready}/${rows.length}項目（取消・出走確定は別）`};
}
/* A31: collapsed chips preserve the exact PRE_RESULT six-boat evidence status;
 * third-party collection does NOT certify numerical agreement. */
function exhibitionFlags(result){
 return ['展示タイム','オリ展','BOATERSオリ展','競艇日和オリ展'].map(label=>{
  const row=(result?.rows||[]).find(x=>x[0]===label);
  return {label,quality:row?.[1]||'unknown',text:row?.[2]||'未取得・未確認'};
 });
}
/* Status labels are facts from the PRE_RESULT inspector, not certified live values. */
function sourceFlags(result){
 return ['欠場・取消','3連単オッズ'].map(label=>{
  const row=(result?.rows||[]).find(x=>x[0]===label);
  return {label,quality:row?.[1]||'unknown',text:row?.[2]||'未取得・未確認'};
 });
}
const race=()=>{try{return typeof state!=='undefined'?state?.race:null}catch(_){return null}};
let working=false,lastKey='';
async function json(path){try{const r=await fetch(path+'?v223='+Date.now(),{cache:'no-store'});return r.ok?await r.json():null;}catch(_){return null;}}
async function refresh(){
 if(working||document.visibilityState==='hidden'||!document.querySelector('#raceView.active'))return;
 const r=race(),key=String(r?.race_key||'');
 const prior=document.querySelector('#be223Source');
 if(prior?.dataset?.raceKey&&prior.dataset.raceKey!==key)prior.hidden=true;
 if(!KEY.test(key)||key.slice(0,8)!==nowDay())return;
 working=true;
 try{
  const [latest,scratch,odds]=await Promise.all([
    json('./data/races/'+key+'.json'),json('./data/site_scratches_v182/'+key+'.json'),json('./data/site_odds/'+key+'.json')]);
  if(race()?.race_key!==key||!document.querySelector('#raceView.active'))return;
  const result=inspect(latest?.race_key===key?latest:r,scratch,odds);
  const host=document.querySelector('#raceView .race-summary');if(!host)return;
  let node=document.querySelector('#be223Source');
  if(!node){node=document.createElement('details');node.id='be223Source';node.className='be223-source';
   node.innerHTML='<summary><b>直前情報の取得状況</b><span class="be223-state" role="status"></span><span class="be223-flags" aria-label="欠場・取消と3連単オッズの取得状況"><span data-be223-flag="scratch"></span><span data-be223-flag="odds"></span></span><span class="be223-exhibition-flags" aria-label="展示6艇と独立オリ展取得状態"><span data-be223-ex="time"></span><span data-be223-ex="original"></span><span data-be223-ex="boaters"></span><span data-be223-ex="biyori"></span></span></summary><div class="be223-rows"></div><p>取得時点の監査表示。欠場・取消の確定証明、買い目の推奨、未見Fresh合格ではありません。オリ展の取得時刻は当サイトへの取り込み時刻です。</p>';
   host.prepend(node);
  }
  // V321: a race-view re-render can replace its summary host. Reattach the
  // existing source panel instead of silently updating a detached old node.
  if(node.parentElement!==host)host.prepend(node);
  if(lastKey!==key){node.open=false;lastKey=key;}
  node.hidden=false;
  node.dataset.raceKey=key; // V250: prevent a previous race's source chip being reused for the selected race
  node.dataset.level=result.level;
  node.querySelector('.be223-state').textContent=result.summary;
  const flags=sourceFlags(result);
  const scratchFlag=node.querySelector('[data-be223-flag="scratch"]');
  const oddsFlag=node.querySelector('[data-be223-flag="odds"]');
  for(const [el,flag] of [[scratchFlag,flags[0]],[oddsFlag,flags[1]]]){
   if(!el)continue;
   el.textContent=flag.label+'：'+flag.text;
   el.dataset.quality=flag.quality;
  }
  const ex=exhibitionFlags(result);
  for(const [id,flag] of [['time',ex[0]],['original',ex[1]],['boaters',ex[2]],['biyori',ex[3]]]){
   const el=node.querySelector('[data-be223-ex="'+id+'"]');
   if(!el)continue;
   el.textContent=flag.label+'：'+flag.text;
   el.dataset.quality=flag.quality;
  }
  const data=node.querySelector('.be223-rows');data.replaceChildren();
  for(const [label,status,value] of result.rows){const row=document.createElement('div');row.className='be223-row';
   const l=document.createElement('span'),v=document.createElement('span');l.textContent=label;v.textContent=value;v.dataset.quality=status;
   row.append(l,v);data.append(row);}
 }finally{working=false;}
}
function start(){refresh();setInterval(refresh,30000);document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')refresh();});
 document.querySelector('#refreshTopBtn')?.addEventListener('click',()=>setTimeout(refresh,1000));}
window.BoatEdgeV223Source={inspect,refresh,sourceFlags,exhibitionFlags,providerEvidence};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
