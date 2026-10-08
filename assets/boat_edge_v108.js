/* BOAT_EDGE_V108_PERFORMANCE_CONSOLIDATED */
(()=>{"use strict";

const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=v=>String(v??"－").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const n=v=>Number(v);
const pct=v=>Number.isFinite(n(v))?(n(v)<=1?n(v)*100:n(v)).toFixed(1)+"%":"－";
const yen=v=>Number.isFinite(n(v))?Math.round(n(v)).toLocaleString("ja-JP")+"円":"－";

const VENUES=[["01","桐生"],["02","戸田"],["03","江戸川"],["04","平和島"],["05","多摩川"],["06","浜名湖"],["07","蒲郡"],["08","常滑"],["09","津"],["10","三国"],["11","びわこ"],["12","住之江"],["13","尼崎"],["14","鳴門"],["15","丸亀"],["16","児島"],["17","宮島"],["18","徳山"],["19","下関"],["20","若松"],["21","芦屋"],["22","福岡"],["23","唐津"],["24","大村"]];

const LABELS={
  hit:{name:"的中重視",desc:"展開確率の上位を広めに残して取りこぼしを減らす",icon:"◎"},
  balance:{name:"バランス",desc:"上位7点＋別頭/別展開3点を基本に10点。オッズでは順位を変えない",icon:"◐"},
  hole:{name:"波乱展開",desc:"別頭を先に、頭の分散で12・15・18点。オッズでは増減しない",icon:"◆"},
  narrow:{name:"激絞り3点",desc:"展開確率の上位3点だけに絞る",icon:"⚡"}
};

const KDATE="boatEdgeV108Date";
const KVENUE="boatEdgeV108Venue";
const KSCROLL="boatEdgeV108HomeScroll";
const KVIEW="boatEdgeV108ViewStack";
const SNAP="boatEdgeV113FinalSnapshot:";
const HISTORY="boatEdgeV113FinalHistory";
const ACTIVE_MODE="boatEdgeV119ActiveMode";

let archiveIndex=null;
let serverHistoryByKey={};
let selectedDate=null;
let selectedVenue=null;
let lastRaceKey=null;
const jsonCache=new Map();

async function J(url,ttl=30000){
  const key=url.replace(/\?.*$/,"");
  const hit=jsonCache.get(key);
  if(hit && Date.now()-hit.at<ttl) return hit.value;
  try{
    const r=await fetch(url,{cache:"no-store"});
    if(!r.ok)return null;
    const value=await r.json();
    jsonCache.set(key,{at:Date.now(),value});
    return value;
  }catch(_){return null}
}
function clearRaceCache(key){
  if(!key)return;
  jsonCache.delete(`./data/site_odds/${key}.json`);
  jsonCache.delete(`./data/site_results/${key}.json`);
  jsonCache.delete(`./data/site_prediction_history/${key}.json`);
  jsonCache.delete("./data/site_prediction_history/index.json");
  serverHistoryByKey={};
}
function raceOf(){try{return state?.race||null}catch(_){return null}}
function predOf(r=raceOf()){try{return r&&typeof getPrediction==="function"?getPrediction(r):null}catch(_){return null}}
function activeView(){return $(".view.active")?.id||"homeView"}
function todayYmd(){const d=new Date();return `${d.getFullYear()}${String(d.getMonth()+1).padStart(2,"0")}${String(d.getDate()).padStart(2,"0")}`}
function raceMinutesToDeadline(race){
  const date=String(race?.meta?.date||"");
  const deadline=String(race?.meta?.deadline||"");
  const dm=/^(\d{4})-(\d{2})-(\d{2})$/.exec(date);
  const tm=/^(\d{1,2}):(\d{2})$/.exec(deadline);
  if(!dm||!tm)return null;
  const iso=`${dm[1]}-${dm[2]}-${dm[3]}T${String(tm[1]).padStart(2,"0")}:${tm[2]}:00+09:00`;
  const ts=new Date(iso).getTime();
  if(!Number.isFinite(ts))return null;
  return Math.floor((ts-Date.now())/60000);
}
function dateObj(s){return /^\d{8}$/.test(String(s||""))?new Date(+s.slice(0,4),+s.slice(4,6)-1,+s.slice(6,8)):null}
function dateLabel(s){const d=dateObj(s);if(!d)return String(s||"");const w=["日","月","火","水","木","金","土"][d.getDay()];return `${d.getMonth()+1}月${d.getDate()}日(${w})`}
function saveSelection(){
  try{
    if(selectedDate)localStorage.setItem(KDATE,selectedDate);
    if(selectedVenue)localStorage.setItem(KVENUE,selectedVenue);else localStorage.removeItem(KVENUE);
  }catch(_){}
}
function getViewStack(){try{return JSON.parse(sessionStorage.getItem(KVIEW)||"[]")}catch(_){return []}}
function setViewStack(v){try{sessionStorage.setItem(KVIEW,JSON.stringify(v.slice(-20)))}catch(_){}}
function pushView(id=activeView()){
  const s=getViewStack();
  if(s[s.length-1]!==id){s.push(id);setViewStack(s)}
}
function showInternal(id){
  if(typeof window.showView==="function"){window.showView(id);return}
  $$(".view").forEach(v=>v.classList.toggle("active",v.id===id));
  $$(".bottomnav [data-view]").forEach(v=>v.classList.toggle("on",v.dataset.view===id));
  window.scrollTo({top:0,behavior:"smooth"});
}
function siteBack(){
  const s=getViewStack();
  const id=s.pop()||"homeView";
  setViewStack(s);
  showInternal($("#"+id)?id:"homeView");
  if(id==="homeView"){
    renderHomeHub().then(()=>{
      const y=Number(sessionStorage.getItem(KSCROLL)||0);
      requestAnimationFrame(()=>window.scrollTo({top:y,behavior:"auto"}));
    });
  }
}

/* ---------- archive / BOATERS-like home ---------- */
async function loadArchiveIndex(){
  if(archiveIndex)return archiveIndex;
  archiveIndex=await J("./data/site_archive/index.json",60000);
  return archiveIndex;
}
async function loadArchiveDay(ymd){return await J(`./data/site_archive/${ymd}.json`,60000)}
function ensureHomeHub(){
  const home=$("#homeView");if(!home)return null;
  let el=$("#be108Hub");
  if(!el){el=document.createElement("section");el.id="be108Hub";el.className="be108-hub";home.insertBefore(el,home.firstChild)}
  [...home.children].forEach(ch=>{if(ch!==el)ch.classList.add("be108-old-home")});
  return el;
}
function resultText(r){
  if(r.result_status==="confirmed"){
    const pay=r.payout?` ${Number(r.payout).toLocaleString("ja-JP")}円`:"";
    const hit=serverHistoryByKey?.[r.race_key]?.hit_any?" 🎯":"";
    return `結果 ${r.trifecta||"確定"}${pay}${hit}`;
  }
  return r.has_odds?"オッズあり":"保存データ";
}
function venueGrid(day){
  const m=new Map((day?.venues||[]).map(v=>[String(v.jcd),v]));
  return `<div class="be108-venue-grid">${VENUES.map(([code,name])=>{
    const v=m.get(code),sel=String(selectedVenue)===code;
    return `<button type="button" class="be108-venue ${v?"active":"off"} ${sel?"selected":""}" ${v?`data-be108-venue="${code}"`:"disabled"}>
      ${v?'<span class="be108-grade">一般</span>':""}
      <b>${name}</b><small>${v?(v.races?.length||0)+"R":"非開催"}</small>
    </button>`;
  }).join("")}</div>`;
}
function raceStrip(v,currentKey=null){
  return `<div class="be108-race-strip">${(v?.races||[]).map(r=>`<button type="button" class="be108-race-chip ${r.race_key===currentKey?"on":""}" data-be108-file="${esc(r.file)}" data-jcd="${esc(r.jcd)}">
    <b>${r.race_no}R</b><span>${esc(r.deadline||"－")}</span>
  </button>`).join("")}</div>`;
}
function venuePanel(day){
  const v=(day?.venues||[]).find(x=>String(x.jcd)===String(selectedVenue));
  if(!v)return "";
  return `<section class="be108-place">
    <div class="be108-place-head">
      <div><b>${esc(v.venue)}</b><span>${esc(v.event||"開催中")}</span></div>
      <button type="button" id="be108CloseVenue">場一覧</button>
    </div>
    ${raceStrip(v)}
    <div class="be108-race-list">
      ${(v.races||[]).map(r=>`<button type="button" class="be108-race-row" data-be108-file="${esc(r.file)}" data-jcd="${esc(r.jcd)}">
        <div><b>${r.race_no}R</b><small>予選</small></div>
        <div><strong>締切 ${esc(r.deadline||"－")}</strong><span>${esc(resultText(r))}</span></div>
        <em>開く ›</em>
      </button>`).join("")}
    </div>
  </section>`;
}

/* BOAT_EDGE_V135_HOME_NEXT3 */
let be135Timer=null,be135Serial=0;
function be135JstIsoDate(){
  return new Date(Date.now()+9*3600000).toISOString().slice(0,10);
}
function be135UpcomingThree(doc,now,isoDay){
  if(String(doc?.date||"")!==isoDay)return [];
  const rows=[];
  for(const v of doc.venues||[]){
    const jcd=String(v.jcd||"").padStart(2,"0");
    if(!/^\d{2}$/.test(jcd))continue;
    for(const r of v.races||[]){
      const time=String(r.deadline||"");
      if(!/^\d{1,2}:\d{2}$/.test(time))continue;
      const [h,m]=time.split(":").map(Number);
      if(h>23||m>59)continue;
      const ts=Date.parse(`${isoDay}T${String(h).padStart(2,"0")}:${String(m).padStart(2,"0")}:00+09:00`);
      if(!Number.isFinite(ts)||ts<=now)continue;
      const file=String(r.file||"");
      if(!/^data\/races\/\d{8}-\d{2}-\d{2}\.json$/.test(file))continue;
      rows.push({file,jcd,venue:String(v.venue||""),no:Number(r.race_no),deadline:time,ts});
    }
  }
  rows.sort((a,b)=>a.ts-b.ts||a.jcd.localeCompare(b.jcd)||a.no-b.no);
  return rows.slice(0,3);
}
async function be135RefreshUpcoming(){
  const host=document.getElementById("be135Upcoming");
  if(!host)return;
  if(be135Timer){clearTimeout(be135Timer);be135Timer=null}
  const serial=++be135Serial, grid=host.querySelector(".be135-upcoming-grid");
  if(!grid)return;
  try{
    const resp=await fetch(`./data/today.json?next3=${Math.floor(Date.now()/30000)}`,{cache:"no-store"});
    if(!resp.ok)throw new Error("today fetch failed");
    const doc=await resp.json();
    if(serial!==be135Serial||!host.isConnected)return;
    const now=Date.now(),rows=be135UpcomingThree(doc,now,be135JstIsoDate());
    grid.innerHTML=rows.length?rows.map((r,i)=>`<button type="button" class="be135-card ${i===0?"nearest":""}" data-be135-file="${esc(r.file)}" data-be135-jcd="${esc(r.jcd)}">
      <span class="be135-rank">${i+1}</span><b>${esc(r.venue)} ${r.no}R</b>
      <strong>締切 ${esc(r.deadline)}</strong><small>あと${Math.max(1,Math.ceil((r.ts-now)/60000))}分 ›</small>
    </button>`).join(""):'<div class="be135-empty">本日の締切予定はありません</div>';
    grid.querySelectorAll("[data-be135-file]").forEach(b=>b.onclick=()=>{
      try{sessionStorage.setItem(KSCROLL,String(window.scrollY||0))}catch(_){}
      pushView("homeView");
      selectedDate=be135JstIsoDate().replaceAll("-","");
      selectedVenue=b.dataset.be135Jcd;saveSelection();
      if(typeof loadRace==="function")loadRace(b.dataset.be135File,b.dataset.be135Jcd);
    });
  }catch(e){
    if(serial===be135Serial&&host.isConnected)grid.innerHTML='<div class="be135-empty">締切情報が取得できません（再読み込みで更新）</div>';
  }
  if(serial===be135Serial&&document.visibilityState==="visible"&&activeView()==="homeView")
    be135Timer=setTimeout(be135RefreshUpcoming,30000);
}

async function renderHomeHub(){
  const host=ensureHomeHub();if(!host)return;
  await loadServerHistoryIndex();
  const idx=await loadArchiveIndex();
  const dates=[...(idx?.dates||[])].map(x=>x.ymd).sort();
  if(!dates.length){host.innerHTML='<div class="be108-empty">保存データ準備中</div>';return}
  if(!selectedDate||!dates.includes(selectedDate))selectedDate=dates.includes(todayYmd())?todayYmd():dates[dates.length-1];
  const day=await loadArchiveDay(selectedDate);
  if(selectedVenue&&!(day?.venues||[]).some(v=>String(v.jcd)===String(selectedVenue)))selectedVenue=null;
  const i=dates.indexOf(selectedDate),prev=dates[i-1]||"",next=dates[i+1]||"";
  host.innerHTML=`<div class="be108-shell">
    <section id="be135Upcoming" class="be135-upcoming" aria-label="締切が近い3レース">
      <div class="be135-upcoming-head"><b>締切が近いレース</b><small>本日の次の3レース</small></div>
      <div class="be135-upcoming-grid"><span class="be135-empty">読み込み中…</span></div>
    </section>
    <div class="be108-date-nav">
      <button type="button" data-be108-day="${prev}" ${prev?"":"disabled"}>‹ 前日</button>
      <div><b>${selectedDate===todayYmd()?"本日 ":""}${dateLabel(selectedDate)}のレース</b><span>日付 → 場 → レース</span></div>
      <button type="button" data-be108-day="${next}" ${next?"":"disabled"}>翌日 ›</button>
    </div>
    ${venueGrid(day)}
    ${venuePanel(day)}
  </div>`;
  saveSelection();
  be135RefreshUpcoming();

  $$("[data-be108-day]",host).forEach(b=>b.onclick=async()=>{
    if(!b.dataset.be108Day)return;
    selectedDate=b.dataset.be108Day;selectedVenue=null;saveSelection();
    await renderHomeHub();window.scrollTo({top:0,behavior:"smooth"});
  });
  $$("[data-be108-venue]",host).forEach(b=>b.onclick=async()=>{
    selectedVenue=b.dataset.be108Venue;saveSelection();
    await renderHomeHub();
    requestAnimationFrame(()=>$(".be108-place",host)?.scrollIntoView({behavior:"smooth",block:"start"}));
  });
  $("#be108CloseVenue",host)?.addEventListener("click",async()=>{selectedVenue=null;saveSelection();await renderHomeHub()});
  $$("[data-be108-file]",host).forEach(b=>b.onclick=()=>{
    try{sessionStorage.setItem(KSCROLL,String(window.scrollY||0))}catch(_){}
    pushView("homeView");
    selectedVenue=b.dataset.jcd;saveSelection();
    if(typeof loadRace==="function")loadRace(b.dataset.be108File,b.dataset.jcd);
  });
}

/* ---------- tabs / navigation ---------- */
const TAB_ORDER=["pred","scenario","card","before","data","audit"];
const TAB_LABEL={pred:"予想",scenario:"展開",card:"選手",before:"直前",data:"データ",audit:"監査"};
function cleanTabs(){
  const tabs=$("#raceTabs");if(!tabs)return;
  const buttons=new Map($$("[data-tab]",tabs).map(b=>[b.dataset.tab,b]));
  buttons.get("direct")?.remove();
  const direct=$("#tab-direct");if(direct){direct.classList.remove("active");direct.style.display="none"}
  for(const k of TAB_ORDER){
    const b=buttons.get(k);if(!b)continue;
    b.textContent=TAB_LABEL[k];tabs.appendChild(b);
  }
  tabs.classList.add("be108-tabs");
}
function fixBottom(){
  const b=$('.bottomnav [data-view="raceView"]');
  if(b)b.innerHTML='<span class="navicon">◎</span>予想';
}
function installBackButtons(){
  for(const [id,label] of [["dataView","データ状況"],["auditView","監査"]]){
    const v=$("#"+id);if(!v)continue;
    let b=$(".be108-back",v);
    if(!b){b=document.createElement("button");b.type="button";b.className="be108-back";b.textContent="← 戻る";v.insertBefore(b,v.firstChild)}
    b.onclick=siteBack;
  }
}
function enhanceRaceNav(race){
  const key=race?.race_key;if(!key)return;
  const ymd=String(key).slice(0,8),jcd=String(race.meta?.venue_code||"").padStart(2,"0");
  selectedDate=ymd;selectedVenue=jcd;saveSelection();
  loadArchiveDay(ymd).then(day=>{
    const v=(day?.venues||[]).find(x=>String(x.jcd)===jcd);if(!v)return;
    const summary=$(".race-summary");if(!summary)return;
    let nav=$("#be108RaceNav");
    if(!nav){nav=document.createElement("div");nav.id="be108RaceNav";const top=$(".summary-top",summary);top?.insertAdjacentElement("afterend",nav)}
    nav.innerHTML=`<div class="be108-race-nav-head"><button type="button" id="be108BackPlace">← ${esc(v.venue)} ${dateLabel(ymd)}</button><span>${esc(v.event||"")}</span></div>${raceStrip(v,key)}`;
    $("#be108BackPlace",nav).onclick=()=>{
      showInternal("homeView");renderHomeHub().then(()=>requestAnimationFrame(()=>$(".be108-place")?.scrollIntoView({behavior:"smooth",block:"start"})));
    };
    $$("[data-be108-file]",nav).forEach(b=>b.onclick=()=>{if(typeof loadRace==="function")loadRace(b.dataset.be108File,b.dataset.jcd)});
    const tabs=$("#raceTabs");if(tabs && tabs.parentElement!==summary)summary.appendChild(tabs);
    cleanTabs();
  });
}

/* ---------- prediction helpers ---------- */
function normalizeCombo(v){
  if(Array.isArray(v))return v.slice(0,3).join("-");
  const m=String(v||"").match(/([1-6])\D+([1-6])\D+([1-6])/);
  return m?`${m[1]}-${m[2]}-${m[3]}`:null;
}
function allTickets(pred){
  const out=[],seen=new Set();
  for(const [wi,w] of (pred?.worlds||[]).entries()){
    for(const [i,t] of (w?.tickets||[]).entries()){
      const combo=normalizeCombo(t?.combo||t?.trifecta||t?.order);
      if(!combo||seen.has(combo))continue;
      seen.add(combo);
      const raw=n(t?.probability??t?.confidence??t?.prob??t?.p);
      out.push({combo,p:Number.isFinite(raw)?(raw<=1?raw*100:raw):0,amount:Number.isFinite(n(t?.amount))?n(t.amount):0,world:w?.key||(wi===0?"A":"B"),rank:i+1});
    }
  }
  return out.sort((a,b)=>b.p-a.p);
}
async function oddsFor(key){return (await J(`./data/site_odds/${key}.json`,30000))?.trifecta_odds||{}}
async function resultFor(key){return await J(`./data/site_results/${key}.json`,30000)}
async function courseStatsFor(jcd){
  const code=String(jcd||"").padStart(2,"0");
  if(!/^[0-9]{2}$/.test(code)||code==="00")return null;
  return await J(`./data/site_course_stats/${code}.json`,86400000);
}
async function loadServerHistoryIndex(){
  const d=await J("./data/site_prediction_history/index.json",30000);
  serverHistoryByKey=d?.races||{};
  return d||{races:{}};
}
async function serverHistoryFor(key){
  if(!key)return null;
  return await J(`./data/site_prediction_history/${key}.json`,30000);
}
function confidence(pred,mode,rows){
  const map={S:90,"S+":93,A:82,"A+":86,B:72,"B+":76,C:62,D:52};
  let base=map[String(pred?.grade||"").toUpperCase()]??68;
  const all=allTickets(pred),sum=all.reduce((s,x)=>s+x.p,0),top=all.slice(0,3).reduce((s,x)=>s+x.p,0);
  base+=Math.round(((sum?top/sum:0)-.35)*18)+({hit:5,balance:0,hole:-5,narrow:-5}[mode]||0);
  if(rows.length<=3)base-=2;
  return Math.max(35,Math.min(94,Math.round(base)));
}

function be122Clamp(v,a,b){return Math.max(a,Math.min(b,v))}
function be122Mean(arr){
  const v=arr
    .filter(x=>x!==null&&x!==undefined&&String(x).trim()!=="")
    .map(Number)
    .filter(Number.isFinite);
  return v.length?v.reduce((a,b)=>a+b,0)/v.length:null;
}
function be122ActualCourseMap(race){
  const m=new Map();
  for(const x of race?.actual_entry||[]){
    const lane=Number(x?.lane),course=Number(x?.course??x?.actual_course??x?.entry_course);
    if(lane>=1&&lane<=6&&course>=1&&course<=6)m.set(lane,course);
  }
  return m;
}
function be122ExStMap(race){
  const m=new Map();
  for(const x of race?.actual_entry||[]){
    const lane=Number(x?.lane),v=n(x?.exhibition_st);
    if(lane>=1&&lane<=6&&Number.isFinite(v))m.set(lane,v);
  }
  for(const x of race?.beforeinfo?.start_exhibition||[]){
    const lane=Number(x?.lane),v=n(x?.st);
    if(lane>=1&&lane<=6&&Number.isFinite(v)&&!m.has(lane))m.set(lane,v);
  }
  return m;
}
function be122ExTimeMap(race){
  const m=new Map();
  for(const x of race?.beforeinfo?.racers||[]){
    const lane=Number(x?.lane),v=n(x?.exhibition_time);
    if(lane>=1&&lane<=6&&Number.isFinite(v))m.set(lane,v);
  }
  return m;
}
function be122OriginalMap(race){
  const labels=(race?.original_exhibition?.labels||[]).map(x=>String(x||""));
  const out=new Map();
  for(const b of race?.original_exhibition?.boats||[]){
    const lane=Number(b?.lane);if(!(lane>=1&&lane<=6))continue;
    const row={};
    (b?.values||[]).forEach((v,i)=>{
      const x=n(v);
      if(Number.isFinite(x))row[labels[i]||`metric_${i}`]=x;
    });
    out.set(lane,row);
  }
  return {labels,out};
}
function be122MetricScores(map,label){
  const rows=[];
  for(const [lane,row] of map.entries()){
    const v=n(row?.[label]);
    if(Number.isFinite(v))rows.push({lane,v});
  }
  const score=new Map();
  if(rows.length<2)return score;
  const lo=Math.min(...rows.map(x=>x.v)),hi=Math.max(...rows.map(x=>x.v));
  const range=Math.max(hi-lo,.001);
  rows.forEach(x=>score.set(x.lane,1-((x.v-lo)/range)));
  return score;
}
function be122MethodFit(c,course){
  if(!c)return null;
  if(course===1)return n(c.escape);
  if(course===2)return Math.max(n(c.sashi)??0,n(c.makuri)??0);
  if(course===3||course===4)return Math.max(n(c.makuri)??0,n(c.makuri_sashi)??0);
  return n(c.makuri_sashi);
}
async function be122ScenarioAdjusted(race,pred){
  const all=allTickets(pred);
  if(!all.length)return {tickets:[],stage:"NO_TICKETS",used:[],applied:false};
  if(pred?.mode==="formal")return {tickets:all,stage:"FORMAL_CURRENT",used:["正式CURRENT"],applied:false};

  const jcd=String(race?.meta?.venue_code||race?.race_key?.split("-")?.[1]||"").padStart(2,"0");
  const stats=await courseStatsFor(jcd).catch(()=>null);
  const actual=be122ActualCourseMap(race),useActual=actual.size===6;
  const exSt=be122ExStMap(race);
  const exTime=be122ExTimeMap(race);
  const orig=be122OriginalMap(race);
  const racers=new Map((race?.racers||[]).map((r,i)=>[Number(r?.lane??i+1),r]));

  const avgStMean=be122Mean([...racers.values()].map(r=>n(r?.avg_st)));
  const exStMean=be122Mean([...exSt.values()]);
  const exTimeVals=[...exTime.values()].filter(Number.isFinite);
  const exTimeMean=be122Mean(exTimeVals);
  const exTimeRange=exTimeVals.length?Math.max(...exTimeVals)-Math.min(...exTimeVals):0;

  const origScores=new Map();
  for(const lab of orig.labels){
    const metric=be122MetricScores(orig.out,lab);
    for(const [lane,sc] of metric.entries()){
      if(!origScores.has(lane))origScores.set(lane,[]);
      origScores.get(lane).push(sc);
    }
  }

  const courseToLane=new Map();
  for(let lane=1;lane<=6;lane++)courseToLane.set(useActual?actual.get(lane):lane,lane);

  const used=[];
  if(stats?.courses)used.push("当地3か月コース");
  if(useActual)used.push("実進入");
  if(exSt.size>=4)used.push("展示ST");
  if(exTime.size>=4)used.push("展示タイム");
  if(orig.out.size>=4)used.push("オリ展");

  const neighborStFactor=(lane,course)=>{
    const own=exSt.get(lane);
    if(!Number.isFinite(own))return 1;
    const vals=[];
    for(const c of [course-1,course+1]){
      const other=courseToLane.get(c);
      const v=exSt.get(other);
      if(Number.isFinite(v))vals.push(v);
    }
    const mean=be122Mean(vals);
    if(!Number.isFinite(mean))return 1;
    return 1+be122Clamp((mean-own)*.45,-.04,.05);
  };

  const laneFactor=lane=>{
    const r=racers.get(Number(lane))||{};
    const course=useActual?actual.get(Number(lane)):Number(lane);
    const c=stats?.courses?.[String(course)]||null;
    let f=1;

    if(c){
      const first=n(c.first_rate);
      if(Number.isFinite(first)){
        const rates=Object.values(stats.courses||{}).map(x=>n(x.first_rate)).filter(Number.isFinite);
        const mean=be122Mean(rates);
        if(Number.isFinite(mean))f*=1+be122Clamp(((first-mean)/100)*.45,-.10,.18);
      }
      const fit=be122MethodFit(c,course);
      if(Number.isFinite(fit)){
        f*=1+be122Clamp(((fit/100)-.45)*.15,-.05,.08);
        if(course===4&&Math.max(n(c.makuri)??0,n(c.makuri_sashi)??0)>=50)f*=1.035;
      }
    }

    const ast=n(r?.avg_st);
    if(Number.isFinite(ast)&&Number.isFinite(avgStMean)){
      f*=1+be122Clamp((avgStMean-ast)*.90,-.06,.06);
    }

    const est=exSt.get(Number(lane));
    if(Number.isFinite(est)&&Number.isFinite(exStMean)){
      f*=1+be122Clamp((exStMean-est)*.65,-.08,.08);
      f*=neighborStFactor(Number(lane),course);
    }

    const et=exTime.get(Number(lane));
    if(Number.isFinite(et)&&Number.isFinite(exTimeMean)&&exTimeRange>.001){
      f*=1+be122Clamp(((exTimeMean-et)/exTimeRange)*.07,-.05,.07);
    }

    const os=origScores.get(Number(lane))||[];
    if(os.length){
      const m=be122Mean(os);
      if(Number.isFinite(m))f*=1+be122Clamp((m-.5)*.12,-.06,.06);
    }

    return be122Clamp(f,.78,1.30);
  };

  const enriched=all.map(x=>{
    const parts=String(x.combo||"").split("-").map(Number);
    const f1=laneFactor(parts[0]),f2=laneFactor(parts[1]),f3=laneFactor(parts[2]);
    const factor=Math.pow(f1,.70)*Math.pow(f2,.19)*Math.pow(f3,.11);
    return {...x,scenario_factor:factor,raw:Math.max(.001,x.p)*factor};
  });

  const oldSum=all.reduce((a,b)=>a+b.p,0)||100;
  const rawSum=enriched.reduce((a,b)=>a+b.raw,0)||1;
  const tickets=enriched.map(x=>({...x,p:(x.raw/rawSum)*oldSum})).sort((a,b)=>b.p-a.p);

  let stage="ENTRY";
  if(stats?.courses)stage="COURSE";
  if(useActual)stage="ACTUAL_ENTRY";
  if(exSt.size>=4)stage="START";
  if(exTime.size>=4)stage="EXHIBITION";
  if(orig.out.size>=4)stage="ORIGINAL_EXHIBITION";
  return {tickets,stage,used,applied:true};
}

function be131ExpandedReferencePrediction(race,pred){
  if(!pred||pred.mode==="formal")return pred;
  const scores=computeScores(race);
  if(!scores?.length)return pred;

  const one=scores.find(x=>x.lane===1)||scores[0];
  const challengers=[...scores].filter(x=>x.lane!==1).sort((a,b)=>b.attackScore-a.attackScore);
  const supporters=[...scores].sort((a,b)=>b.baseScore-a.baseScore);

  const worldA=pred.worlds?.find(x=>x.key==="A")||pred.worlds?.[0]||{};
  const worldB=pred.worlds?.find(x=>x.key==="B")||pred.worlds?.[1]||{};
  const pa=n(worldA.probability)??50;
  const pb=n(worldB.probability)??(100-pa);

  const aCandidates=[];
  const seconds=supporters.filter(x=>x.lane!==1);
  for(let i=0;i<seconds.length;i++){
    for(let j=0;j<seconds.length;j++){
      if(i===j)continue;
      const sec=seconds[i],third=seconds[j];
      const weight=(one.insideScore*1.2)+sec.baseScore+third.baseScore+(sec.lane<third.lane?.5:0);
      aCandidates.push({combo:`1-${sec.lane}-${third.lane}`,weight});
    }
  }
  const aTop=topNUnique(aCandidates.sort((a,b)=>b.weight-a.weight),10);
  const aSum=aTop.reduce((x,y)=>x+y.weight,0)||1;
  const aTickets=aTop.map((x,i)=>({rank:i+1,combo:x.combo,probability:(x.weight/aSum)*pa,amount:null}));

  const bCandidates=[];
  for(const h of challengers.slice(0,3)){
    const others=supporters.filter(x=>x.lane!==h.lane);
    const pref=others.find(x=>x.lane===1);
    const rest=others.filter(x=>x.lane!==1);
    for(const sec of others.slice(0,5)){
      for(const third of others.slice(0,5)){
        if(third.lane===sec.lane)continue;
        const preferIn=(sec.lane===1?1.2:0)+(third.lane===1?.8:0);
        const weight=h.attackScore*1.25+sec.baseScore+third.baseScore+preferIn+((h.actualCourse||0)>=3?1.5:0);
        bCandidates.push({combo:`${h.lane}-${sec.lane}-${third.lane}`,weight});
      }
    }
    if(pref){
      for(const r of rest.slice(0,3)){
        bCandidates.push({combo:`${h.lane}-1-${r.lane}`,weight:h.attackScore*1.35+pref.baseScore+r.baseScore+3});
        bCandidates.push({combo:`${h.lane}-${r.lane}-1`,weight:h.attackScore*1.2+pref.baseScore+r.baseScore+2.2});
      }
    }
  }
  const bTop=topNUnique(bCandidates.sort((a,b)=>b.weight-a.weight),10);
  const bSum=bTop.reduce((x,y)=>x+y.weight,0)||1;
  const bTickets=bTop.map((x,i)=>({rank:i+1,combo:x.combo,probability:(x.weight/bSum)*pb,amount:null}));

  return {...pred,worlds:[
    {...worldA,key:"A",probability:pa,tickets:aTickets},
    {...worldB,key:"B",probability:pb,tickets:bTickets}
  ]};
}
function be131WaveRows(all){
  if(!all?.length)return [];
  const total=all.reduce((a,b)=>a+(Number(b?.p)||0),0)||1;
  const headMass=new Map();
  for(const x of all){
    const h=String(x?.combo||"").split("-")[0];
    if(!h)continue;
    headMass.set(h,(headMass.get(h)||0)+(Number(x?.p)||0));
  }
  const shares=[...headMass.entries()]
    .map(([head,mass])=>({head,mass,share:mass/total}))
    .sort((a,b)=>b.mass-a.mass);

  const primaryHead=shares[0]?.head||String(all[0]?.combo||"").split("-")[0]||null;
  const primaryShare=shares[0]?.share??1;
  const meaningfulHeads=shares.filter(x=>x.share>=.10).length;

  let target=12;
  if(meaningfulHeads>=4||primaryShare<=.42)target=18;
  else if(meaningfulHeads>=3||primaryShare<=.58)target=15;

  const alt=primaryHead?all.filter(x=>String(x.combo||"").split("-")[0]!==primaryHead):[];
  const primary=primaryHead?all.filter(x=>String(x.combo||"").split("-")[0]===primaryHead):all;
  const ordered=[...alt,...primary];
  const out=[],seen=new Set();
  for(const x of ordered){
    if(!x?.combo||seen.has(x.combo))continue;
    seen.add(x.combo);out.push(x);
    if(out.length>=Math.min(target,all.length))break;
  }
  return out;
}


function be132BalanceRows(all,waveAll=all){
  const out=[],seen=new Set();
  const add=x=>{
    if(!x?.combo||seen.has(x.combo)||out.length>=10)return;
    seen.add(x.combo);out.push(x);
  };
  all.slice(0,7).forEach(add);
  const primaryHead=String(all[0]?.combo||"").split("-")[0]||null;
  const alt=(waveAll||[]).filter(x=>String(x?.combo||"").split("-")[0]!==primaryHead);
  for(const x of alt){
    add(x);
    if(out.length>=10)break;
  }
  for(const x of all){
    add(x);
    if(out.length>=10)break;
  }
  for(const x of waveAll||[]){
    add(x);
    if(out.length>=10)break;
  }
  return out;
}
function be122ModesFromTickets(all,odds,waveAll=all){
  const od=x=>{const v=n(odds?.[x.combo]);return Number.isFinite(v)&&v>0?v:null};
  const modes={
    hit:all.slice(0,Math.min(10,all.length)),
    balance:be132BalanceRows(all,waveAll),
    hole:be131WaveRows(waveAll),
    narrow:all.slice(0,Math.min(3,all.length))
  };
  for(const k of Object.keys(modes))modes[k]=modes[k].map(x=>({...x,odds:od(x)}));
  return modes;
}
function be122PredictionFromAdjusted(pred,adjusted){
  if(pred?.mode==="formal"||!adjusted?.tickets?.length)return pred;
  const base=pred?.worlds||[];
  const worlds=base.map((w,wi)=>{
    const key=w?.key||(wi===0?"A":"B");
    const tickets=adjusted.tickets.filter(x=>x.world===key).map((x,i)=>({
      rank:i+1,combo:x.combo,probability:x.p,amount:x.amount??0
    }));
    const probability=tickets.reduce((a,b)=>a+(Number(b.probability)||0),0);
    return {...w,probability,tickets};
  });
  return {...pred,worlds};
}
function selectModes(pred,odds){
  const all=allTickets(pred);
  const od=x=>{const v=n(odds?.[x.combo]);return Number.isFinite(v)&&v>0?v:null};
  const primaryHead=all[0]?.combo?.split("-")?.[0]||null;
  const altHead=primaryHead?all.filter(x=>String(x.combo||"").split("-")[0]!==primaryHead):[];
  const variancePool=altHead.length?altHead:all.slice(3);
  const modes={
    hit:all.slice(0,Math.min(10,all.length)),
    balance:all.slice(0,Math.min(6,all.length)),
    hole:variancePool.slice(0,Math.min(8,variancePool.length)),
    narrow:all.slice(0,Math.min(3,all.length))
  };
  if(!modes.hole.length)modes.hole=all.slice(0,Math.min(6,all.length));
  for(const k of Object.keys(modes))modes[k]=modes[k].map(x=>({...x,odds:od(x)}));
  return modes;
}
function snapKey(k){return SNAP+k}
function readLocal(k,f=null){try{return JSON.parse(localStorage.getItem(k)||"null")??f}catch(_){return f}}
function writeLocal(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(_){}}
function saveFinalSnapshot(key,race,pred,modes,mins){
  const snap={
    schema:"boat-edge-v113-final-snapshot-v1",
    snapshot_window:"FINAL_15M",
    race_key:key,
    saved_at:new Date().toISOString(),
    minutes_to_deadline:mins,
    venue:race?.meta?.venue||"",
    race_no:race?.meta?.race_no||"",
    deadline:race?.meta?.deadline||null,
    grade:pred?.grade||null,
    modes:Object.fromEntries(Object.entries(modes).map(([k,rows])=>[
      k,
      {
        confidence:confidence(pred,k,rows),
        tickets:rows.map(x=>({combo:x.combo,p:x.p,odds:x.odds??null}))
      }
    ]))
  };
  writeLocal(snapKey(key),snap);
  return snap;
}
function isFinalSnapshot(snap){
  return snap?.schema==="boat-edge-v113-final-snapshot-v1"
    && snap?.snapshot_window==="FINAL_15M";
}
function settle(snapshot,result){
  if(!snapshot||result?.status!=="confirmed")return null;
  const win=normalizeCombo(result.trifecta||result.finish_order);if(!win)return null;
  const mode_hits={};for(const [k,v] of Object.entries(snapshot.modes||{}))mode_hits[k]=(v.tickets||[]).some(x=>x.combo===win);
  const item={race_key:snapshot.race_key,venue:snapshot.venue,race_no:snapshot.race_no,deadline:snapshot.deadline??null,final_saved_at:snapshot.saved_at??null,snapshot_schema:snapshot.schema,snapshot_window:snapshot.snapshot_window,winning_combo:win,payout:result.trifecta_payout_yen_per_100??null,mode_hits,hit_any:Object.values(mode_hits).some(Boolean)};
  const h=(readLocal(HISTORY,[])||[]).filter(x=>x.race_key!==item.race_key);h.unshift(item);writeLocal(HISTORY,h.slice(0,120));return item;
}
function historyHtml(){
  const local=(readLocal(HISTORY,[])||[]).filter(
    x=>x.hit_any
      && x.snapshot_window==="FINAL_15M"
      && x.snapshot_schema==="boat-edge-v113-final-snapshot-v1"
  );
  const server=Object.values(serverHistoryByKey||{})
    .filter(x=>x?.hit_any)
    .map(x=>({
      race_key:x.race_key,
      venue:x.venue,
      race_no:x.race_no,
      winning_combo:x.winning_combo,
      payout:x.payout,
      mode_hits:x.mode_hits||{},
      hit_any:true,
      settled_at:x.settled_at||null,
      source:"server"
    }));

  const merged=new Map();
  for(const x of server){
    if(x?.race_key)merged.set(x.race_key,x);
  }
  for(const x of local){
    if(x?.race_key&&!merged.has(x.race_key))merged.set(x.race_key,x);
  }

  const hits=[...merged.values()].sort((a,b)=>{
    const at=String(a.settled_at||a.final_saved_at||a.race_key||"");
    const bt=String(b.settled_at||b.final_saved_at||b.race_key||"");
    return bt.localeCompare(at);
  });

  if(!hits.length){
    return '<div class="be108-emptyline">締切15分前の最終予想による🎯履歴はまだありません。</div>';
  }

  return hits.slice(0,60).map(x=>{
    const modes=Object.entries(x.mode_hits||{})
      .filter(([,v])=>v)
      .map(([k])=>LABELS[k]?.name||k)
      .join(" / ");
    const shared=x.source==="server"?"共有 / ":"";
    return `<div class="be108-history-row">
      <div><b>🎯 ${esc(x.venue)} ${esc(x.race_no)}R</b><span>${esc(x.winning_combo)}</span></div>
      <div><small>${shared}${esc(modes)}</small>${x.payout?`<strong>${yen(x.payout)}/100円</strong>`:""}</div>
    </div>`;
  }).join("");
}
function renderTicketRows(rows,win){
  return rows.map((x,i)=>`<div class="be108-ticket ${win===x.combo?"hit":""}"><span>${i+1}</span><b>${win===x.combo?"🎯 ":""}${esc(x.combo)}</b><em>${pct(x.p)}</em><small>${x.odds?x.odds.toFixed(1)+"倍":"オッズ－"}</small></div>`).join("");
}
async function renderPredictionModes(race,pred){
  const key=race?.race_key;if(!key||!pred)return;
  const stack=$("#tab-pred .section.stack");if(!stack)return;

  const [odds,result]=await Promise.all([oddsFor(key),resultFor(key)]);
  await loadServerHistoryIndex();
  const adjusted=await be122ScenarioAdjusted(race,pred);
  let waveAdjusted=adjusted;
  if(pred.mode!=="formal"){
    const wavePred=be131ExpandedReferencePrediction(race,pred);
    waveAdjusted=await be122ScenarioAdjusted(race,wavePred);
  }
  const modes=be122ModesFromTickets(adjusted.tickets,odds,waveAdjusted.tickets);
  const mins=raceMinutesToDeadline(race);
  const resultConfirmed=result?.status==="confirmed";
  const serverSummary=resultConfirmed?(serverHistoryByKey?.[key]||null):null;
  const serverRecord=serverSummary?await serverHistoryFor(key):null;
  const inFinalWindow=!resultConfirmed && mins!==null && mins>=0 && mins<=15;

  let snap=readLocal(snapKey(key));
  if(inFinalWindow)snap=saveFinalSnapshot(key,race,pred,modes,mins);

  const finalSnap=isFinalSnapshot(snap)?snap:null;
  const serverSnap=serverRecord?.snapshot||null;
  const effectiveSnap=resultConfirmed?(serverSnap||finalSnap):finalSnap;
  const settled=resultConfirmed?(serverRecord?.settlement||(finalSnap?settle(finalSnap,result):null)):null;
  const win=settled?.winning_combo||null;
  const officialResult=resultConfirmed?normalizeCombo(result?.trifecta||result?.finish_order):null;

  let mode=localStorage.getItem(ACTIVE_MODE)||"hit";
  if(!LABELS[mode])mode="hit";

  const frozenRows=effectiveSnap?.modes?.[mode]?.tickets||null;
  const baseRows=(resultConfirmed&&frozenRows)?frozenRows:modes[mode]||[];
  const rows=baseRows.map(x=>({...x,odds:x.odds??(Number.isFinite(n(odds[x.combo]))?n(odds[x.combo]):null)}));
  const conf=(resultConfirmed&&effectiveSnap?.modes?.[mode]?.confidence!=null)?effectiveSnap.modes[mode].confidence:confidence(pred,mode,rows);

  let snapStatus="🎯履歴は締切15分前から保存";
  if(inFinalWindow)snapStatus=`🎯 最終予想を保存中・締切まで${mins}分`;
  else if(resultConfirmed&&serverSnap)snapStatus=`サーバー保存の締切前最終予想で判定・${esc(serverSnap.saved_at||"")}`;
  else if(resultConfirmed&&finalSnap)snapStatus=`この端末の締切前最終予想で判定・${esc(finalSnap.saved_at||"")}`;
  else if(resultConfirmed&&!effectiveSnap)snapStatus="締切前の最終スナップショットなし・的中判定対象外";
  else if(mins!==null&&mins<0)snapStatus=finalSnap?"締切済み・保存した最終予想を固定中":"締切済み・締切前スナップショットなし";

  const modeHit=Boolean(settled?.mode_hits?.[mode]);
  let cls="pending",status="🎯 判定待ち",detail="締切15分前に最終予想を保存して判定",resultText="結果未確定";
  if(inFinalWindow){
    status="🎯 判定待ち・最終予想保存中";
    detail=`締切まで${mins}分 / 保存済み最終予想で判定`;
  }else if(!resultConfirmed&&mins!==null&&mins<0){
    status="🎯 判定待ち・結果待ち";
    detail=effectiveSnap?"締切前の最終予想は保存済み":"締切前snapshotなし";
  }else if(resultConfirmed){
    const pay=Number(result?.trifecta_payout_yen_per_100);
    const payText=Number.isFinite(pay)?`${pay.toLocaleString("ja-JP")}円 / 100円`:"払戻未取得";
    resultText=`結果 ${esc(officialResult||"確定")}`;
    if(settled){
      status=modeHit?"🎯 的中":"✕ 不的中";
      detail=`${LABELS[mode]?.name||mode} / ${payText}`;
      cls=modeHit?"hit":"miss";
    }else{
      status="— 判定対象外";
      detail=`締切前の最終予想snapshotなし / ${payText}`;
      cls="neutral";
    }
  }
  const resultBar=`<div id="be128HitStatus" class="be118-resultbar ${cls}" data-hit-status="${modeHit?"hit":resultConfirmed?"settled":"pending"}"><div><small>🎯 判定ステータス</small><b>${status}</b></div><div><strong>${resultText}</strong><span>${detail}</span></div></div>`;

  const stageText=adjusted.used.length?adjusted.used.join(" → "):"出走表";
  const sourceBar=pred.mode==="formal"
    ? `<div class="be118-source formal">正式CURRENTを使用中</div>`
    : `<div class="be118-source reference"><b>最新予想CURRENT方針・参考</b><span>${esc(stageText)}</span><small>取得済み入力だけ使用。未取得値は補完しません。正式CURRENT接続時はそちらを最優先。オッズは順位に使いません。</small></div>`;

  let panel=$("#be108PredictionModes");
  if(!panel){panel=document.createElement("section");panel.id="be108PredictionModes";panel.className="be108-panel";stack.prepend(panel)}

  panel.innerHTML=`${sourceBar}${resultBar}<div class="be108-head"><div><h3>予想スタイル</h3><p>展開確率を軸に表示</p></div><button id="be108HistoryBtn" type="button">過去の🎯履歴</button></div><div class="be108-snapshot-status">${snapStatus}</div><div class="be108-mode-tabs">${Object.entries(LABELS).map(([k,v])=>`<button type="button" data-be108-mode="${k}" class="${k===mode?"on":""}">${settled?.mode_hits?.[k]?"🎯 ":""}${v.name}</button>`).join("")}</div><div class="be108-mode-card ${modeHit?"hit":""}"><div class="be108-mode-top"><div><b>${modeHit?"🎯 ":""}${LABELS[mode].icon} ${LABELS[mode].name}</b><span>${LABELS[mode].desc}</span></div><div><small>内部信頼度</small><strong>${conf}%</strong></div></div><div class="be108-ticket-list">${renderTicketRows(rows,win)}</div></div><div id="be108History" class="be108-history" hidden>${historyHtml()}</div>`;

  $$("[data-be108-mode]",panel).forEach(b=>b.onclick=()=>{localStorage.setItem(ACTIVE_MODE,b.dataset.be108Mode);renderPredictionModes(race,pred)});
  $("#be108HistoryBtn",panel).onclick=()=>{const h=$("#be108History",panel);h.hidden=!h.hidden};
}
async function renderMainPick(race,pred,preAdjusted=null){
  const stack=$("#tab-pred .section.stack");if(!stack||!pred)return;
  const adjusted=preAdjusted||await be122ScenarioAdjusted(race,pred);
  const top=adjusted.tickets[0];if(!top)return;
  let box=$("#be108MainPick");
  if(!box){box=document.createElement("div");box.id="be108MainPick";box.className="be108-mainpick";stack.prepend(box)}
  const formal=pred.mode==="formal";
  const stage=adjusted.used.length?adjusted.used.join(" → "):"出走表";
  box.classList.toggle("be118-reference",!formal);
  box.innerHTML=`<div><small>${formal?"正式CURRENT メイン予想":"最新予想CURRENT方針・参考"}</small><b>${esc(top.combo)}</b><span>${pct(top.p)} / 勝負度 ${esc(pred.grade||"－")} / ${esc(stage)}</span></div><em>${formal?"正式CURRENT":"参考"}</em>`;
}
async function augmentBuyBoard(race){
  const key=race?.race_key;if(!key)return;
  const odds=await oddsFor(key);
  const rows=$$("#buyBoard .buy-ticket");
  if(!rows.length)return;
  let total=0;
  for(const row of rows){
    const stake=Number(String($(".buy-money",row)?.textContent||"").replace(/[^0-9.]/g,""));
    if(Number.isFinite(stake))total+=stake;
  }
  for(const row of rows){
    const combo=$(".buy-combo",row)?.textContent?.trim();
    const stake=Number(String($(".buy-money",row)?.textContent||"").replace(/[^0-9.]/g,""));
    const o=n(odds?.[combo]);
    let box=$(".be108-odds",row);if(!box){box=document.createElement("div");box.className="be108-odds";row.appendChild(box)}
    if(!Number.isFinite(o)||!Number.isFinite(stake)||stake<=0){box.textContent="オッズ未取得";continue}
    const payout=stake*o,profit=payout-total,roi=total?payout/total*100:0;
    box.innerHTML=`<span>${o.toFixed(1)}倍</span><b>払戻 ${yen(payout)}</b><small>損益 ${profit>=0?"+":""}${yen(profit)} / ${Math.round(roi)}%</small>`;
  }
}

/* ---------- official venue course stats ---------- */
function be117ActualCourseMap(race){
  const m=new Map();
  for(const x of race?.actual_entry||[]){
    const lane=Number(x?.lane);
    const course=Number(x?.course??x?.actual_course??x?.entry_course);
    if(lane>=1&&lane<=6&&course>=1&&course<=6)m.set(lane,course);
  }
  return m;
}
function be117DominantMethod(c){
  const rows=[
    ["逃げ",c?.escape],["まくり",c?.makuri],["差し",c?.sashi],["まくり差し",c?.makuri_sashi]
  ].filter(x=>Number.isFinite(Number(x[1])));
  rows.sort((a,b)=>Number(b[1])-Number(a[1]));
  return rows[0]||["－",null];
}
function be117Strongest(nodes,minGap,minRelative){
  const rows=[...nodes].map(n=>({n,v:Number(n.dataset.value)}))
    .filter(x=>Number.isFinite(x.v)).sort((a,b)=>b.v-a.v);
  rows.forEach(x=>x.n.classList.remove("be117-best"));
  if(rows.length<2)return;
  const gap=rows[0].v-rows[1].v;
  const rel=gap/Math.max(Math.abs(rows[1].v),1);
  if(gap>=minGap&&rel>=minRelative)rows[0].n.classList.add("be117-best");
}
function be117Pct(v){
  const n=Number(v);
  return Number.isFinite(n)?n.toFixed(1)+"%":"－";
}
async function renderCourseStats(race){
  const key=race?.race_key;if(!key)return;
  const jcd=String(race?.meta?.venue_code||key.split("-")[1]||"").padStart(2,"0");
  const stats=await courseStatsFor(jcd).catch(()=>null);
  const stack=$("#tab-scenario .section.stack");if(!stack)return;

  let panel=$("#be117CourseStats");
  if(!panel){
    panel=document.createElement("section");
    panel.id="be117CourseStats";
    panel.className="be117-course";
    const title=stack.querySelector(":scope > .title");
    if(title)title.insertAdjacentElement("afterend",panel);else stack.prepend(panel);
  }

  if(!stats?.courses){
    panel.innerHTML='<div class="be117-head"><div><b>当地コース傾向</b><span>公式データ未取得</span></div></div>';
    return;
  }

  const actual=be117ActualCourseMap(race),actualReady=actual.size===6,rows=[];
  for(let lane=1;lane<=6;lane++){
    const course=actual.get(lane)||lane,c=stats.courses[String(course)]||{};
    rows.push({lane,course,c,dom:be117DominantMethod(c)});
  }

  const period=stats.period?`${esc(stats.period.from)}〜${esc(stats.period.to)}`:"最近3か月";
  panel.innerHTML=`<div class="be117-head">
    <div><b>当地コース傾向</b><span>${esc(stats.venue||race?.meta?.venue||"")} / ${period}</span></div>
    <em>${actualReady?"実進入で表示":"枠＝想定コース"}</em>
  </div>
  <div class="be117-grid">${rows.map(x=>`<article class="be117-card">
    <div class="be117-card-head"><b>${x.lane}号艇</b><span>${x.course}コース</span></div>
    <div class="be117-first" data-be117-first data-value="${Number(x.c.first_rate)}">
      <small>当地コース1着率</small><strong>${be117Pct(x.c.first_rate)}</strong>
    </div>
    <div class="be117-dominant">
      <small>勝った時の主な決まり手</small><strong>${esc(x.dom[0])} ${be117Pct(x.dom[1])}</strong>
    </div>
    <div class="be117-methods">
      <span data-be117-method="escape" data-value="${Number(x.c.escape)}">逃 ${be117Pct(x.c.escape)}</span>
      <span data-be117-method="makuri" data-value="${Number(x.c.makuri)}">捲 ${be117Pct(x.c.makuri)}</span>
      <span data-be117-method="sashi" data-value="${Number(x.c.sashi)}">差 ${be117Pct(x.c.sashi)}</span>
      <span data-be117-method="makuri_sashi" data-value="${Number(x.c.makuri_sashi)}">捲差 ${be117Pct(x.c.makuri_sashi)}</span>
    </div>
  </article>`).join("")}</div>
  <p class="be117-note">BOAT RACE公式・最近3か月。決まり手%は「そのコースが勝った時」の内訳。現時点では予想ロジック未使用。</p>`;

  be117Strongest(panel.querySelectorAll("[data-be117-first]"),5,.08);
  for(const m of ["escape","makuri","sashi","makuri_sashi"]){
    be117Strongest(panel.querySelectorAll(`[data-be117-method="${m}"]`),8,.10);
  }
}

/* ---------- racer tap + standout ---------- */
function markStandouts(){
  const boats=$$("#boats .boat");if(boats.length!==6)return;
  const pred=predOf(),scores=pred?.scores||[];
  boats.forEach((b,i)=>{b.dataset.be108Lane=String(scores[i]?.lane??i+1);b.classList.add("be108-clickable")});
  for(const metricIndex of [0,1,2]){
    const vals=boats.map(b=>({b,el:$$(".metric",b)[metricIndex]?.querySelector(".m-value")})).map(x=>({...x,v:Number.parseFloat(x.el?.textContent)})).filter(x=>Number.isFinite(x.v)).sort((a,b)=>b.v-a.v);
    vals.forEach(x=>x.el?.classList.remove("be108-best"));
    if(vals.length>=4&&vals[1]){
      const gap=vals[0].v-vals[1].v,rel=gap/Math.max(Math.abs(vals[1].v),1);
      const need=metricIndex===2?8:.55;
      if(gap>=need&&rel>=.08)vals[0].el?.classList.add("be108-best");
    }
  }
}
async function showHeadPrediction(boat){
  const lane=Number(boat.dataset.be108Lane),pred=predOf(),race=raceOf();if(!lane||!pred||!race)return;
  const adjusted=await be122ScenarioAdjusted(race,pred);
  const rows=adjusted.tickets.filter(x=>String(x.combo).startsWith(lane+"-")).slice(0,5);
  let box=$(".be108-headpick",boat);
  if(box){box.remove();return}
  box=document.createElement("div");box.className="be108-headpick";
  box.innerHTML=`<b>${lane}号艇が1着の予想</b>${rows.length?rows.map((x,i)=>`<div><strong>#${i+1} ${esc(x.combo)}</strong><span>${pct(x.p)}</span></div>`).join(""):"<p>この艇頭の候補はありません。</p>"}`;
  boat.appendChild(box);
}

/* ---------- event-driven lifecycle ---------- */
async function afterRace(race){
  if(!race?.race_key)return;
  lastRaceKey=race.race_key;
  window.BoatEdgeInputAuditV139?.render(race); // V139 UI only; predictor unchanged
  cleanTabs();fixBottom();installBackButtons();enhanceRaceNav(race);
  const pred=predOf(race);
  markStandouts();

  const adjusted=await be122ScenarioAdjusted(race,pred);
  const adjustedPred=be122PredictionFromAdjusted(pred,adjusted);

  await Promise.all([
    renderMainPick(race,pred,adjusted),
    renderCourseStats(race)
  ]);
  await renderPredictionModes(race,pred);

  if(typeof renderBuyBoard==="function")renderBuyBoard(race,adjustedPred);
  if(typeof renderDirectMode==="function")renderDirectMode(race,adjustedPred);
  const diff=$("#predictionDiff");if(diff)diff.style.display="none";
  await augmentBuyBoard(race);
}
function wrapRenderRace(){
  const original=window.renderRace;
  if(typeof original!=="function"||original.__be108Wrapped)return;
  const wrapped=function(d){const out=original.apply(this,arguments);Promise.resolve().then(()=>afterRace(d));return out};
  wrapped.__be108Wrapped=true;window.renderRace=wrapped;
}
async function refreshCurrentRaceData(){
  const r=raceOf();
  if(!r?.race_key)return;
  clearRaceCache(r.race_key);
  if(typeof loadRace==="function"){
    await loadRace(`data/races/${r.race_key}.json`,r.meta?.venue_code||"");
    return;
  }
  await afterRace(r);
}
function installEvents(){
  document.addEventListener("click",e=>{
    const bottom=e.target.closest?.(".bottomnav [data-view]");
    if(bottom&&bottom.dataset.view!==activeView())pushView(activeView());

    const boat=e.target.closest?.("#boats .boat.be108-clickable");
    if(boat){e.preventDefault();showHeadPrediction(boat)}

    const tab=e.target.closest?.("#raceTabs [data-tab]");
    if(tab&&raceOf())requestAnimationFrame(()=>{
      cleanTabs();
      if(tab.dataset.tab==="pred"){
        afterRace(raceOf());
      }
    });
  },true);

  document.addEventListener("visibilitychange",()=>{
    if(document.visibilityState==="visible"&&raceOf()){
      refreshCurrentRaceData();
    }
  });

  $("#refreshTopBtn")?.addEventListener("click",()=>{
    setTimeout(()=>refreshCurrentRaceData(),800);
  });
}

try{selectedDate=localStorage.getItem(KDATE)||null;selectedVenue=localStorage.getItem(KVENUE)||null}catch(_){}
wrapRenderRace();
installEvents();
fixBottom();cleanTabs();installBackButtons();
renderHomeHub();
document.addEventListener("visibilitychange",()=>{
  if(document.visibilityState==="visible"&&activeView()==="homeView")be135RefreshUpcoming();
});
document.addEventListener("click",e=>{
  if(e.target.closest?.('.bottomnav [data-view="homeView"]'))
    requestAnimationFrame(()=>be135RefreshUpcoming());
});
window.addEventListener("pageshow",e=>{
  if(e.persisted&&activeView()==="homeView")be135RefreshUpcoming();
});
if(raceOf())afterRace(raceOf());
})();
