/* BOAT_EDGE_V105_BOATERS_HOME */
(()=>{"use strict";
const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=v=>String(v??"－").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const VENUES=[["01","桐生"],["02","戸田"],["03","江戸川"],["04","平和島"],["05","多摩川"],["06","浜名湖"],["07","蒲郡"],["08","常滑"],["09","津"],["10","三国"],["11","びわこ"],["12","住之江"],["13","尼崎"],["14","鳴門"],["15","丸亀"],["16","児島"],["17","宮島"],["18","徳山"],["19","下関"],["20","若松"],["21","芦屋"],["22","福岡"],["23","唐津"],["24","大村"]];
let idx=null,date=null,venue=null;
const KDATE="boatEdgeV105Date",KVENUE="boatEdgeV105Venue";
async function J(u){try{const r=await fetch(u+(u.includes("?")?"&":"?")+"t="+Date.now(),{cache:"no-store"});return r.ok?await r.json():null}catch(_){return null}}
function dObj(s){return /^\d{8}$/.test(String(s||""))?new Date(+s.slice(0,4),+s.slice(4,6)-1,+s.slice(6,8)):null}
function dLabel(s){const d=dObj(s);if(!d)return s;const w=["日","月","火","水","木","金","土"][d.getDay()];return `${d.getMonth()+1}月${d.getDate()}日(${w})`}
function todayYmd(){const d=new Date();return `${d.getFullYear()}${String(d.getMonth()+1).padStart(2,"0")}${String(d.getDate()).padStart(2,"0")}`}
function activeView(){return $(".view.active")?.id||"homeView"}
function ensure(){
  const home=$("#homeView");if(!home)return null;
  let el=$("#be105Hub");
  if(!el){el=document.createElement("section");el.id="be105Hub";el.className="be105-hub";home.insertBefore(el,home.firstChild)}
  return el;
}
function save(){try{if(date)localStorage.setItem(KDATE,date);if(venue)localStorage.setItem(KVENUE,venue);else localStorage.removeItem(KVENUE)}catch(_){}}
function raceStatus(r){
  if(r.result_status==="confirmed"){
    const p=r.payout?` ${Number(r.payout).toLocaleString("ja-JP")}円`:"";
    return `結果 ${r.trifecta||"確定"}${p}`;
  }
  if(r.has_odds)return "オッズあり";
  return "保存データ";
}
function raceStrip(v,currentKey=null){
  return `<div class="be105-race-strip">${(v?.races||[]).map(r=>`<button type="button" class="be105-race-chip ${r.race_key===currentKey?"on":""}" data-file="${esc(r.file)}" data-jcd="${esc(r.jcd)}"><b>${r.race_no}R</b><span>${esc(r.deadline||"－")}</span></button>`).join("")}</div>`;
}
function venueGrid(day){
  const m=new Map((day?.venues||[]).map(v=>[String(v.jcd),v]));
  return `<div class="be105-venue-grid">${VENUES.map(([code,name])=>{
    const v=m.get(code),on=String(venue)===code;
    return `<button type="button" class="be105-venue ${v?"active":"off"} ${on?"selected":""}" ${v?`data-venue="${code}"`:"disabled"}>
      ${v?'<span class="be105-grade">一般</span>':""}<b>${name}</b>
      <small>${v?(v.races?.length||0)+"R":"非開催"}</small>
    </button>`;
  }).join("")}</div>`;
}
function venuePanel(day){
  const v=(day?.venues||[]).find(x=>String(x.jcd)===String(venue));if(!v)return "";
  return `<section class="be105-place">
    <div class="be105-place-head"><div><b>${esc(v.venue)}</b><span>${esc(v.event||"開催中")}</span></div><button id="be105VenueClose" type="button">場一覧</button></div>
    ${raceStrip(v)}
    <div class="be105-race-list">${(v.races||[]).map(r=>`<button type="button" class="be105-race-row" data-file="${esc(r.file)}" data-jcd="${esc(r.jcd)}">
      <div><b>${r.race_no}R</b><small>予選</small></div>
      <div><strong>締切 ${esc(r.deadline||"－")}</strong><span>${esc(raceStatus(r))}</span></div>
      <em>開く ›</em>
    </button>`).join("")}</div>
  </section>`;
}
async function render(){
  const el=ensure();if(!el)return;
  idx=idx||await J("./data/site_archive/index.json");
  const dates=[...(idx?.dates||[])].map(x=>x.ymd).sort();
  if(!dates.length){el.innerHTML='<div class="be105-empty">保存データ準備中</div>';return}
  if(!date||!dates.includes(date))date=dates.includes(todayYmd())?todayYmd():dates[dates.length-1];
  const day=await J(`./data/site_archive/${date}.json`);
  if(venue&&!(day?.venues||[]).some(v=>String(v.jcd)===String(venue)))venue=null;
  const i=dates.indexOf(date),prev=dates[i-1]||"",next=dates[i+1]||"";
  el.innerHTML=`<div class="be105-shell">
    <div class="be105-date-nav">
      <button type="button" data-day="${prev}" ${prev?"":"disabled"}>‹ 前日</button>
      <div><b>${date===todayYmd()?"本日 ":""}${dLabel(date)}のレース</b><span>保存済みのレースを日付で切替</span></div>
      <button type="button" data-day="${next}" ${next?"":"disabled"}>翌日 ›</button>
    </div>
    ${venueGrid(day)}
    ${venuePanel(day)}
  </div>`;
  save();
  $$("[data-day]",el).forEach(b=>b.onclick=async()=>{if(!b.dataset.day)return;date=b.dataset.day;venue=null;save();await render();window.scrollTo({top:0,behavior:"smooth"})});
  $$("[data-venue]",el).forEach(b=>b.onclick=async()=>{venue=b.dataset.venue;save();await render();setTimeout(()=>$(".be105-place",el)?.scrollIntoView({behavior:"smooth",block:"start"}),30)});
  $("#be105VenueClose",el)?.addEventListener("click",async()=>{venue=null;save();await render()});
  $$("[data-file]",el).forEach(b=>b.onclick=()=>{venue=b.dataset.jcd;save();if(typeof loadRace==="function")loadRace(b.dataset.file,b.dataset.jcd)});
}
async function enhanceRace(){
  let race=null;try{race=state?.race||null}catch(_){}
  if(!race?.race_key)return;
  const ymd=String(race.race_key).slice(0,8),jcd=String(race.meta?.venue_code||"").padStart(2,"0");
  date=ymd;venue=jcd;save();
  const day=await J(`./data/site_archive/${ymd}.json`);
  const v=(day?.venues||[]).find(x=>String(x.jcd)===jcd);if(!v)return;
  const summary=$(".race-summary");if(!summary)return;
  let nav=$("#be105RaceNav");
  if(!nav){nav=document.createElement("div");nav.id="be105RaceNav";nav.className="be105-race-nav";const top=$(".summary-top",summary);top?.insertAdjacentElement("afterend",nav)}
  nav.innerHTML=`<div class="be105-race-nav-head"><button id="be105BackPlace" type="button">← ${esc(v.venue)} ${dLabel(ymd)}</button><span>${esc(v.event||"")}</span></div>${raceStrip(v,race.race_key)}`;
  $("#be105BackPlace",nav).onclick=()=>{document.querySelectorAll(".view").forEach(x=>x.classList.toggle("active",x.id==="homeView"));venue=jcd;date=ymd;save();render();setTimeout(()=>$(".be105-place")?.scrollIntoView({behavior:"smooth",block:"start"}),60)};
  $$("[data-file]",nav).forEach(b=>b.onclick=()=>{if(typeof loadRace==="function")loadRace(b.dataset.file,b.dataset.jcd)});
  const tabs=$("#raceTabs");if(tabs){summary.appendChild(tabs);tabs.classList.add("be105-tabs")}
}
function hideOldHome(){
  const home=$("#homeView");if(!home)return;
  [...home.children].forEach(ch=>{if(ch.id!=="be105Hub")ch.classList.add("be105-old-home")});
}
function repairOtherBack(){
  for(const [id,label] of [["dataView","データ状況"],["auditView","監査"]]){
    const v=$("#"+id);if(!v)continue;
    let b=$(".be105-back",v);
    if(!b){b=document.createElement("button");b.className="be105-back";b.type="button";b.textContent="← 戻る";v.insertBefore(b,v.firstChild)}
    b.onclick=()=>history.length>1?history.back():document.querySelector('.bottomnav [data-view="homeView"]')?.click();
  }
}
try{date=localStorage.getItem(KDATE)||null;venue=localStorage.getItem(KVENUE)||null}catch(_){}
hideOldHome();render();repairOtherBack();enhanceRace();
new MutationObserver(()=>{hideOldHome();repairOtherBack();enhanceRace()}).observe(document.documentElement,{subtree:true,childList:true});
setInterval(enhanceRace,1500);
})();
