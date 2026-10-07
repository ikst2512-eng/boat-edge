/* BOAT_EDGE_V104_BOATERS_NAV */
(()=>{"use strict";
const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=v=>String(v??"－").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const STORE_DATE="boatEdgeV104Date";
const STORE_VENUE="boatEdgeV104Venue";
const NAV_STACK="boatEdgeV104NavStack";
const cache=new Map();
let archiveIndex=null;
let selectedDate=null;
let selectedVenue=null;

async function J(u){
  const key=u.replace(/\?.*$/,"");
  const hit=cache.get(key);
  if(hit&&Date.now()-hit.at<15000)return hit.v;
  try{
    const r=await fetch(u+(u.includes("?")?"&":"?")+"t="+Date.now(),{cache:"no-store"});
    if(!r.ok)return null;
    const v=await r.json();cache.set(key,{at:Date.now(),v});return v;
  }catch(_){return null}
}
function activeView(){return $(".view.active")?.id||"homeView"}
function currentCtx(){return {view:activeView(),scroll:window.scrollY||0,date:selectedDate,venue:selectedVenue}}
function navStack(){try{return JSON.parse(sessionStorage.getItem(NAV_STACK)||"[]")}catch(_){return []}}
function saveStack(v){try{sessionStorage.setItem(NAV_STACK,JSON.stringify(v.slice(-40)))}catch(_){}}
function pushCtx(){
  const s=navStack(),c=currentCtx(),p=s[s.length-1];
  if(p&&p.view===c.view&&p.date===c.date&&p.venue===c.venue&&Math.abs((p.scroll||0)-(c.scroll||0))<24)return;
  s.push(c);saveStack(s);
}
function activateView(id){
  $$(".view").forEach(v=>v.classList.toggle("active",v.id===id));
  $$(".bottomnav [data-view]").forEach(v=>v.classList.toggle("on",v.dataset.view===id));
}
function saveSelection(){
  try{
    if(selectedDate)localStorage.setItem(STORE_DATE,selectedDate);
    if(selectedVenue)localStorage.setItem(STORE_VENUE,selectedVenue);
  }catch(_){}
}
async function goBack(){
  const s=navStack(),p=s.pop();saveStack(s);
  if(!p){activateView("homeView");await renderHub();window.scrollTo({top:0,behavior:"smooth"});return}
  selectedDate=p.date||selectedDate;
  selectedVenue=p.venue||selectedVenue;
  saveSelection();
  activateView(p.view||"homeView");
  if((p.view||"homeView")==="homeView")await renderHub();
  setTimeout(()=>window.scrollTo({top:p.scroll||0,behavior:"smooth"}),40);
}
function dateObj(ymd){
  const s=String(ymd||"");
  if(!/^\d{8}$/.test(s))return null;
  return new Date(Number(s.slice(0,4)),Number(s.slice(4,6))-1,Number(s.slice(6,8)));
}
function sameToday(ymd){
  const d=dateObj(ymd),n=new Date();
  return d&&d.getFullYear()===n.getFullYear()&&d.getMonth()===n.getMonth()&&d.getDate()===n.getDate();
}
function dateLabel(ymd){
  const d=dateObj(ymd);if(!d)return String(ymd||"");
  const wd=["日","月","火","水","木","金","土"][d.getDay()];
  return `${d.getMonth()+1}月${d.getDate()}日(${wd})`;
}
function dateTitle(ymd){return `${sameToday(ymd)?"本日":""}${dateLabel(ymd)}`}
async function loadIndex(){if(archiveIndex)return archiveIndex;archiveIndex=await J("./data/site_archive/index.json");return archiveIndex}
async function loadDay(ymd){return await J(`./data/site_archive/${ymd}.json`)}
function indexDates(){return [...(archiveIndex?.dates||[])].map(x=>x.ymd).sort()}
function ensureHub(){
  const home=$("#homeView");if(!home)return null;
  let sec=$("#be104Hub");
  if(!sec){sec=document.createElement("section");sec.id="be104Hub";sec.className="be104-hub";home.insertBefore(sec,home.firstChild)}
  return sec;
}
function statusText(r){
  if(r.result_status==="confirmed"){
    const pay=r.payout?` ${Number(r.payout).toLocaleString("ja-JP")}円`:"";
    return `結果 ${esc(r.trifecta||"確定")}${pay}`;
  }
  if(r.has_odds)return "オッズあり";
  return "保存データ";
}
function raceMini(r,active=false){
  return `<button type="button" class="be104-race-mini ${active?"on":""}" data-race-file="${esc(r.file)}" data-race-jcd="${esc(r.jcd)}"><b>${esc(r.race_no)}R</b><span>${esc(r.deadline||"－")}</span></button>`;
}
function raceRow(r){
  return `<button type="button" class="be104-race-row" data-race-file="${esc(r.file)}" data-race-jcd="${esc(r.jcd)}"><div class="be104-rno"><b>${esc(r.race_no)}R</b><small>予選</small></div><div class="be104-rmeta"><strong>締切 ${esc(r.deadline||"－")}</strong><span>${statusText(r)}</span></div><div class="be104-open">見る ›</div></button>`;
}
function venueCard(v){
  return `<button type="button" class="be104-venue ${selectedVenue===v.jcd?"on":""}" data-venue="${esc(v.jcd)}"><span class="be104-badge">一般</span><b>${esc(v.venue)}</b><small>${(v.races||[]).length}R</small></button>`;
}
function selectedVenueHtml(day){
  const v=(day?.venues||[]).find(x=>String(x.jcd)===String(selectedVenue));
  if(!v)return "";
  return `<div class="be104-venue-panel"><div class="be104-venue-head"><div><b>${esc(v.venue)}</b><span>${esc(v.event||"開催中")}</span></div><button type="button" id="be104CloseVenue">場一覧へ</button></div><div class="be104-race-strip">${(v.races||[]).map(r=>raceMini(r)).join("")}</div><div class="be104-race-list">${(v.races||[]).map(raceRow).join("")}</div></div>`;
}
function dateNavHtml(dates){
  const i=Math.max(0,dates.indexOf(selectedDate));
  const prev=dates[i-1]||null,next=dates[i+1]||null;
  return `<div class="be104-date-nav"><button type="button" data-day="${prev||""}" ${prev?"":"disabled"}>‹ 前日</button><div><b>${esc(dateTitle(selectedDate))}のレース</b><span>保存済みデータ</span></div><button type="button" data-day="${next||""}" ${next?"":"disabled"}>翌日 ›</button></div>`;
}
async function renderHub(){
  const sec=ensureHub();if(!sec)return;
  await loadIndex();
  const dates=indexDates();
  if(!dates.length){sec.innerHTML='<div class="be104-empty">保存済みレースを準備中です。</div>';return}
  if(!selectedDate||!dates.includes(selectedDate))selectedDate=dates[dates.length-1];
  const day=await loadDay(selectedDate);
  if(selectedVenue&&!(day?.venues||[]).some(v=>String(v.jcd)===String(selectedVenue)))selectedVenue=null;
  saveSelection();
  sec.innerHTML=`<div class="be104-shell">${dateNavHtml(dates)}<div class="be104-venue-grid">${(day?.venues||[]).map(venueCard).join("")}</div>${selectedVenueHtml(day)}</div>`;
  $$("[data-day]",sec).forEach(b=>b.onclick=async()=>{const d=b.dataset.day;if(!d)return;selectedDate=d;selectedVenue=null;saveSelection();await renderHub();window.scrollTo({top:0,behavior:"smooth"})});
  $$("[data-venue]",sec).forEach(b=>b.onclick=async()=>{selectedVenue=b.dataset.venue;saveSelection();await renderHub();setTimeout(()=>$(".be104-venue-panel",sec)?.scrollIntoView({behavior:"smooth",block:"start"}),30)});
  $("#be104CloseVenue",sec)?.addEventListener("click",async()=>{selectedVenue=null;saveSelection();await renderHub()});
  $$("[data-race-file]",sec).forEach(b=>b.onclick=()=>{pushCtx();selectedVenue=b.dataset.raceJcd||selectedVenue;saveSelection();if(typeof loadRace==="function")loadRace(b.dataset.raceFile,b.dataset.raceJcd)});
}
async function renderRaceHeader(){
  let race=null;try{race=state?.race||null}catch(_){}
  if(!race?.race_key)return;
  const ymd=String(race.race_key).slice(0,8),jcd=String(race.meta?.venue_code||"").padStart(2,"0");
  selectedDate=ymd;selectedVenue=jcd;saveSelection();
  const day=await loadDay(ymd);
  const v=(day?.venues||[]).find(x=>String(x.jcd)===jcd);
  if(!v)return;
  const summary=$(".race-summary");if(!summary)return;
  let wrap=$("#be104RaceTop");
  if(!wrap){wrap=document.createElement("div");wrap.id="be104RaceTop";const top=$(".summary-top",summary);top?.insertAdjacentElement("afterend",wrap)}
  wrap.innerHTML=`<div class="be104-race-backrow"><button type="button" id="be104Back">← ${esc(v.venue)} ${dateLabel(ymd)}へ</button><span>${esc(v.event||"")}</span></div><div class="be104-race-strip">${(v.races||[]).map(r=>raceMini(r,r.race_key===race.race_key)).join("")}</div>`;
  $("#be104Back",wrap).onclick=goBack;
  $$("[data-race-file]",wrap).forEach(b=>b.onclick=()=>{if(typeof loadRace==="function")loadRace(b.dataset.raceFile,b.dataset.raceJcd)});
  const tabs=$("#raceTabs");
  if(tabs){summary.appendChild(tabs);tabs.classList.add("be104-tabs")}
}
function installOtherBack(){
  for(const [id,label] of [["dataView","データ状況"],["auditView","監査"]]){
    const view=$("#"+id);if(!view)continue;
    let bar=$(".be104-view-back",view);
    if(!bar){bar=document.createElement("div");bar.className="be104-view-back";bar.innerHTML=`<button type="button">← 戻る</button><span>${label}</span>`;view.insertBefore(bar,view.firstChild)}
    $("button",bar).onclick=goBack;
  }
}
function captureNavigation(){
  document.addEventListener("click",e=>{const v=e.target.closest?.(".bottomnav [data-view]");if(v&&v.dataset.view!==activeView())pushCtx()},true);
}
async function init(){
  try{selectedDate=localStorage.getItem(STORE_DATE)||null;selectedVenue=localStorage.getItem(STORE_VENUE)||null}catch(_){}
  await renderHub();installOtherBack();renderRaceHeader();
}
captureNavigation();
new MutationObserver(()=>{installOtherBack();renderRaceHeader()}).observe(document.documentElement,{subtree:true,childList:true});
setInterval(()=>renderRaceHeader(),1500);
init();
})();
