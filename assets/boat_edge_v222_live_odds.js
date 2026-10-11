/* BOAT EDGE V222: refresh verified official odds on the visible race even if race data is unchanged.
   Display lifecycle only. No prediction weights, rankings, result collection, historical snapshots,
   ticket mutations, or formal-Fresh access. Odds are labelled as collection-time, not realtime. */
(()=>{'use strict';
if(window.BoatEdgeV222Odds)return;
const DAY=()=>new Date(Date.now()+9*3600000).toISOString().slice(0,10).replaceAll('-','');
const COMBO=/^[1-6]-[1-6]-[1-6]$/;
const KEY=/^20\d{6}-\d{2}-\d{2}$/;
const OFFICIAL=/^https:\/\/www\.boatrace\.jp\/owpc\/pc\/race\/odds3t\?/;
let currentKey='',signature='',quality='',busy=false;
const race=()=>{try{return typeof state!=='undefined'?state?.race||null:null;}catch(_){return null;}};
const due=r=>{
 const key=String(r?.race_key||''),clock=String(r?.meta?.deadline||'');
 if(!KEY.test(key)||!/^\d{1,2}:\d{2}$/.test(clock))return NaN;
 const t=Date.parse(`${key.slice(0,4)}-${key.slice(4,6)}-${key.slice(6,8)}T${clock.padStart(5,'0')}:00+09:00`);
 return Number.isFinite(t)?t:NaN;
};
const validate=(d,r,now)=>{
 if(!d||typeof d!=='object'||d.race_key!==r.race_key||d.schema_version!=='boat-edge-site-odds-v71'||
  d.phase!=='PRE_RESULT_PURCHASE_ONLY'||d.results_seen!==false||d.scoring!==false||
  !OFFICIAL.test(String(d.source_url||''))||String(d.deadline||'')!==String(r.meta?.deadline||''))return {quality:'invalid',signature:''};
 const t=Date.parse(d.fetched_at||''),deadline=due(r);
 if(!Number.isFinite(t)||!Number.isFinite(deadline)||t>deadline||t>now+30000)return {quality:'invalid',signature:''};
 const odds=d.trifecta_odds;
 if(!odds||Array.isArray(odds)||typeof odds!=='object')return {quality:'invalid',signature:''};
 const entries=Object.entries(odds);
 if(entries.length<80||entries.length>120||d.available_count!==entries.length||
   !entries.every(([k,v])=>{if(!COMBO.test(k)||new Set(k.split('-')).size!==3)return false;
      return typeof v==='number'&&Number.isFinite(v)&&v>0;}))return {quality:'invalid',signature:''};
 // This is a display fingerprint only, not a cryptographic or investment evidence hash.
 const sig=JSON.stringify([d.fetched_at,entries]);
 return {quality:now-t<=9*60000?'fresh':'stale',signature:sig};
};
async function poll(){
 if(busy||document.visibilityState!=='visible'||!document.querySelector('#raceView.active'))return;
 const r=race(),key=String(r?.race_key||''),now=Date.now(),deadline=due(r);
 if(!KEY.test(key)||key.slice(0,8)!==DAY()||!Number.isFinite(deadline)||now>=deadline)return;
 busy=true;
 try{
  let doc=null;
  try{
   const response=await fetch(`./data/site_odds/${key}.json?be222=${now}`,{cache:'no-store'});
   if(response.ok)doc=await response.json();
  }catch(_){/* Missing official source must never be substituted with odds estimates. */}
  const next=doc?validate(doc,r,Date.now()):{quality:'missing',signature:''};
  if(race()?.race_key!==key||document.visibilityState!=='visible')return;
  const changed=key!==currentKey||next.quality!==quality||next.signature!==signature;
  currentKey=key;quality=next.quality;signature=next.signature;
  if(!changed)return;
  // Reuse the site's audited display renderer; it never ranks tickets by odds.
  // Only existing public data is re-read. Local/frozen bet records are not edited here.
  if(typeof window.BoatEdgeV166Invalidate==='function')window.BoatEdgeV166Invalidate(key);
  if(typeof renderRace==='function')renderRace(race(),{silent:true});
 }catch(_){/* A failed refresh leaves existing safe display controls in place. */}
 finally{busy=false;}
}
function start(){
 poll();setInterval(()=>{if(document.visibilityState==='visible')poll();},30000);
 document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')poll();});
 document.querySelector('#refreshTopBtn')?.addEventListener('click',()=>setTimeout(poll,900));
 document.querySelector('#be166GlobalRefresh')?.addEventListener('click',()=>setTimeout(poll,900));
}
window.BoatEdgeV222Odds={poll,validate};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
