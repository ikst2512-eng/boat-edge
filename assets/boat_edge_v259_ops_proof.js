/* BOAT EDGE V259: live PRE_RESULT site-only snapshot evidence, never results or payouts.
   A published V220 status can lag behind later, valid immutable snapshot commits.
   Recompute read-only eligibility in the browser; never manufacture missing picks. */
(function(root){'use strict';
const KEY=/^20\d{6}-\d{2}-\d{2}$/;
const HEX=/^[a-f0-9]{64}$/;
const COMBO=/^[1-6]-[1-6]-[1-6]$/;
const within=(stamp,lo,hi)=>{const t=Date.parse(stamp||'');return Number.isFinite(t)&&Number.isFinite(lo)&&Number.isFinite(hi)&&lo<=t&&t<=hi};
const DAY=()=>new Date(Date.now()+9*3600000).toISOString().slice(0,10).replaceAll('-','');
function due(key,clock){
 if(!KEY.test(String(key||''))||!/^([01]?\d|2[0-3]):[0-5]\d$/.test(String(clock||'')))return NaN;
 const stamp=key.slice(0,4)+'-'+key.slice(4,6)+'-'+key.slice(6,8)+'T'+String(clock).padStart(5,'0')+':00+09:00';
 return Date.parse(stamp);
}
function upcoming(schedule,now,limit=3){
 if(!schedule||String(schedule.date||'').replaceAll('-','')!==new Date(now+9*3600000).toISOString().slice(0,10).replaceAll('-',''))return [];
 const rows=[];
 for(const venue of (schedule.venues||[]))for(const race of (venue.races||[])){
  const key=race.race_key,t=due(key,race.deadline),left=(t-now)/60000;
  if(!Number.isFinite(t)||!Number.isFinite(left)||left<0||left>35)continue;
  rows.push({key,deadline:race.deadline,venue:String(venue.venue||venue.name||''),left,t});
 }
 return rows.sort((a,b)=>a.t-b.t||a.key.localeCompare(b.key)).slice(0,limit);
}
function assess(key,deadline,snapshot,audit,evidence,sha){
 if(!snapshot)return {state:'missing',label:'公開先に固定記録なし（公開待ち・未保存を含む）'};
 if(snapshot.race_key!==key||snapshot.snapshot_window!=='FINAL_15M'||snapshot.schema_version!=='boat-edge-server-site-final-v123'||
    snapshot.prediction_kind!=='SITE_REFERENCE_V122'||!snapshot.guards||
    ['results_seen','unlock','scoring'].some(k=>snapshot.guards[k]!==false))return {state:'invalid',label:'保存内容・安全条件が不一致'};
 const saved=Date.parse(snapshot.saved_at||''),first=Date.parse(snapshot.first_saved_at||''),cutoff=due(key,deadline),lead=(cutoff-saved)/60000;
 if(!Number.isFinite(saved)||!Number.isFinite(first)||!Number.isFinite(cutoff)||first>saved||saved-first>10000||
    lead<2||lead>10||snapshot.deadline!==deadline)return {state:'invalid',label:'保存時刻・締切の照合不一致'};
 const stakeOk=snapshot.stake_plan_version==='V141-10000-PROSPECTIVE'&&
  ['hit','balance','hole','narrow'].every(mode=>{
   const rows=snapshot.modes?.[mode]?.tickets;
   return Array.isArray(rows)&&rows.length>0&&new Set(rows.map(r=>r.combo)).size===rows.length&&
    rows.every(r=>typeof r.combo==='string'&&COMBO.test(r.combo)&&new Set(r.combo.split('-')).size===3&&
     Number.isSafeInteger(r.stake_yen)&&r.stake_yen>=0&&r.stake_yen%100===0)&&
    rows.reduce((n,r)=>n+r.stake_yen,0)===10000;
  });
 if(!stakeOk)return {state:'invalid',label:'締切前配分の監査不一致'};
 if(!audit||!evidence||!HEX.test(String(sha||'')))return {state:'unverified',label:'保存あり・SHA監査待ち'};
 if(audit.race_key!==key||audit.pass!==true||audit.revision_count!==1||
    audit.latest_snapshot_sha256!==sha||Date.parse(audit.latest_snapshot_saved_at||'')!==saved||
    evidence.race_key!==key||evidence.snapshot_sha256!==sha||Date.parse(evidence.snapshot_saved_at||'')!==saved||
    evidence.schema!=='BOAT_EDGE_V229_ATOMIC_PRE_RESULT_SOURCE_EVIDENCE_V1'||
    evidence.scope!=='SITE_REFERENCE_ONLY_NO_FORMAL_OR_RESULT_ACCESS'||
    evidence.new_snapshot_created_this_run!==true||evidence.results_seen!==false||
    evidence.formal_fresh_unlock!==false||evidence.scoring!==false||
    evidence.odds_combinations!==120||evidence.stake_yen_per_mode!==10000||
    evidence.race_sha256!==snapshot.race_sha256||evidence.odds_sha256!==snapshot.odds_sha256||
    !HEX.test(String(snapshot.race_sha256||''))||!HEX.test(String(snapshot.odds_sha256||''))||
    !HEX.test(String(evidence.scratch_sha256||''))||
    !Array.isArray(audit.revisions)||audit.revisions.length!==1||
    audit.revisions[0]?.snapshot_sha256!==sha)
  return {state:'invalid',label:'SHA・保存時刻・出典の照合不一致'};
 // V260: timestamps belong to the original prospective operation, not to a later
 // upload. This is consistency validation, not independent Git commit-time proof.
 const capturedDeadline=Math.min(cutoff,saved+120000);
 if(!within(audit.first_audited_at,saved,capturedDeadline)||
    !within(evidence.evidence_captured_at,saved,capturedDeadline)||
    !within(evidence.official_race_card_fetched_at,saved-960000,saved)||
    !within(evidence.official_beforeinfo_fetched_at,saved-900000,saved)||
    !within(evidence.scratch_checked_at,saved-900000,saved)||
    !within(evidence.odds_fetched_at,saved-900000,saved))
   return {state:'invalid',label:'締切前の出典時刻が未検証'};
 return {state:'verified',label:'締切前の保存データ・SHA整合'};
}
/* V264: explain source-only blockers, without loading results or rewriting missed freezes.
 * A race can have a valid freeze committed AFTER an older V220 snapshot was generated.
 * These are observations only, never authorizations to bet or to unlock Formal Fresh.
 */
const ageOK=(stamp,now,maxMs)=>{
 const t=Date.parse(String(stamp||''));
 return Number.isFinite(t)&&t<=now&&now-t<=maxMs;
};
function missingReasons(key,deadline,race,scratch,odds,now=Date.now()){
 if(!KEY.test(String(key||'')))return ['レース指定不正'];
 const rem=(due(key,deadline)-now)/60000;
 if(!Number.isFinite(rem)||rem<0)return ['締切済み・未保存を後から復元しません'];
 if(rem>10)return ['締切10分前の固定時間帯待ち'];
 const reasons=[],meta=race?.meta||{},au=race?.source_audit||{};
 if(!race || race.race_key && race.race_key!==key ||
    meta.phase!=='PRE_RESULT'||['results_seen','unlock','scoring'].some(k=>meta[k]!==false)||
    !Array.isArray(race.racers)||race.racers.length!==6)
  reasons.push('6艇出走・結果未見データの確認待ち');
 const card=au.race_card||{};
 if(card.status!=='ok'||!ageOK(card.fetched_at,now,16*60000))
  reasons.push('出走表の再確認待ち');
 const before=au.beforeinfo||{};
 if(before.status!=='ok'||!ageOK(before.fetched_at,now,15*60000))
  reasons.push('公式直前情報の取得待ち');
 if(!scratch||scratch.race_key!==key||scratch.blocked!==false||
    scratch.race_card_source_status!=='ok'||scratch.official_beforeinfo_source_status!=='ok'||
    !ageOK(scratch.checked_at,now,15*60000))
  reasons.push('欠場・取消の安全確認待ち');
 const rows=odds?.trifecta_odds||{};
 const allCombinations=[];
 for(let a=1;a<=6;a++)for(let b=1;b<=6;b++)for(let c=1;c<=6;c++){
  if(a!==b&&a!==c&&b!==c)allCombinations.push(a+'-'+b+'-'+c);
 }
 const rowsReady=odds?.race_key===key&&odds.phase==='PRE_RESULT_PURCHASE_ONLY'&&
    odds.results_seen===false&&odds.scoring===false&&odds.available_count===120&&
    Object.keys(rows).length===120&&ageOK(odds.fetched_at,now,15*60000)&&
    allCombinations.every(combo=>typeof rows[combo]==='number'&&Number.isFinite(rows[combo])&&rows[combo]>0);
 if(!rowsReady)reasons.push('3連単120通り・保存時刻の確認待ち');
 else if(odds.verified_official_dom_v167!==true)
  reasons.push('公式DOM照合の記録待ち');
 if(!reasons.length)return [rem<2?'固定期限内の保存証跡なし（後付け禁止）':'入力は取得済み・固定予想の保存証跡待ち'];
 return reasons;
}
if(typeof module!=='undefined'&&module.exports)module.exports={due,upcoming,assess,missingReasons};
if(typeof document==='undefined'||typeof window==='undefined')return;
if(window.BoatEdgeV259Ops)return;
let inflight=false,epoch=0;
const $=s=>document.querySelector(s);
async function json(url){
 try{const res=await fetch(url+'?v259='+Date.now(),{cache:'no-store'});return res.ok?await res.json():null}catch(_){return null}
}
async function proof(r){
 const path='./data/site_prediction_snapshots/'+r.key+'.json';
 let res=null;
 try{res=await fetch(path+'?v259='+Date.now(),{cache:'no-store'})}catch(_){
  return {state:'unverified',label:'通信失敗・保存状況は未確認'};
 }
 if(!res)return {state:'unverified',label:'公開サーバーの応答なし・未確認'};
 if(!res.ok){
  if(res.status!==404)return {state:'unverified',label:'公開サーバー取得エラー・未確認'};
  // Read CURRENT pre-result sources for explanatory status only. Never fabricate
  // an immutable ticket that was absent at the original deadline.
  const [race,scratch,odds]=await Promise.all([
   json('./data/races/'+r.key+'.json'),
   json('./data/site_scratches_v182/'+r.key+'.json'),
   json('./data/site_odds/'+r.key+'.json')
  ]);
  const reasons=missingReasons(r.key,r.deadline,race,scratch,odds,Date.now());
  return {state:'missing',label:reasons.slice(0,2).join('・')};
 }
 let buffer,snapshot=null;
 try{buffer=await res.arrayBuffer();snapshot=JSON.parse(new TextDecoder().decode(buffer))}catch(_){return {state:'invalid',label:'保存JSONの読込不正'}}
 if(!window.crypto?.subtle)return assess(r.key,r.deadline,snapshot,null,null,null);
 let sha=null;
 try{const digest=await window.crypto.subtle.digest('SHA-256',buffer);
     sha=Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,'0')).join('')}
 catch(_){return {state:'unverified',label:'端末でSHA照合不可'}}
 const [audit,evidence]=await Promise.all([
  json('./data/site_prediction_audit/'+r.key+'.json'),
  json('./data/site_autopilot/v229_evidence/'+r.key+'.json')
 ]);
 const original=assess(r.key,r.deadline,snapshot,audit,evidence,sha);
 if(original.state!=='verified')return original;
 const official=window.BoatEdgeV263OddsProof;
 if(typeof official?.verify!=='function')return {state:'unverified',label:'保存オッズ照合モジュール未取得'};
 const full=await official.verify(r.key,snapshot,evidence);
 return full.state==='verified'?
   {state:'verified',label:'締切前保存・SHA・公式120通りと買い目倍率一致'}:full;
}
function mount(){
 const host=$('#be220Ops');if(!host)return null;
 let el=$('#be259OpsProof');if(el)return el;
 el=document.createElement('div');el.id='be259OpsProof';
 el.style.cssText='border-top:1px solid #d8e5ef;margin-top:7px;padding-top:6px;font-size:11px;line-height:1.5';
 const title=document.createElement('strong');title.textContent='直近レースの締切前固定（保存証跡を再照合）';
 title.title='保存ファイル・監査の整合性検査。Git登録時刻や正式Freshの審査とは別です';
 const msg=document.createElement('span');msg.id='be259OpsMessage';msg.style.marginLeft='8px';msg.textContent='確認中';
 const detail=document.createElement('div');detail.id='be259OpsRows';detail.style.marginTop='4px';
 el.append(title,msg,detail);host.appendChild(el);return el;
}
async function refresh(){
 if(inflight)return;
 const root=mount();if(!root)return;
 inflight=true;const sequence=++epoch,at=Date.now();
 try{
  const schedule=await json('./data/today.json');
  if(sequence!==epoch)return;
  const list=upcoming(schedule,at,3);
  const summary=$('#be259OpsMessage'),rows=$('#be259OpsRows');
  if(!summary||!rows)return;
  rows.replaceChildren();
  if(!list.length){summary.textContent='次の監査対象待ち';return}
  const outcomes=await Promise.all(list.map(async r=>r.left>10?
    {state:'waiting',label:'締切10分前の保存開始待ち'}:await proof(r)));
  if(sequence!==epoch||DAY()!==new Date(at+9*3600000).toISOString().slice(0,10).replaceAll('-',''))return;
  let verified=0,eligible=0;
  list.forEach((r,i)=>{
   const p=outcomes[i];if(r.left<=10)eligible++;
   if(p.state==='verified')verified++;
   const line=document.createElement('div');
   line.textContent=(r.venue?r.venue+' ':'')+Number(r.key.slice(-2))+'R '+r.deadline+'締切：'+p.label;
   if(p.state==='invalid'||(p.state==='missing'&&r.left<=10))line.style.color='#9b481e';
   rows.appendChild(line);
  });
  summary.textContent=eligible?verified+'/'+eligible+'R オッズ120通り・SHA照合済み':'保存時刻待ち';
 }catch(_){const el=$('#be259OpsMessage');if(el)el.textContent='照合データ未取得・合格扱いにしません'}
 finally{inflight=false}
}
function start(){if(!mount())return;refresh();
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});
 $('#be166GlobalRefresh')?.addEventListener('click',refresh);
 setInterval(()=>{if(!document.hidden)refresh()},90000);
}
window.BoatEdgeV259Ops={refresh,version:'V259-PROVENANCE-READ-ONLY'};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})(typeof window!=='undefined'?window:{});
