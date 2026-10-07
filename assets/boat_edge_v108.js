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
  hit:{name:"的中重視",desc:"候補を広めに残して取りこぼしを減らす",icon:"◎"},
  balance:{name:"バランス重視",desc:"確率とオッズの両方を見て選ぶ",icon:"◐"},
  hole:{name:"穴重視",desc:"予想候補内で高配当寄りを優先",icon:"◆"},
  narrow:{name:"激絞り重視",desc:"確率上位だけを3点に絞る",icon:"⚡"}
};

const KDATE="boatEdgeV108Date";
const KVENUE="boatEdgeV108Venue";
const KSCROLL="boatEdgeV108HomeScroll";
const KVIEW="boatEdgeV108ViewStack";
const SNAP="boatEdgeV113FinalSnapshot:";
const HISTORY="boatEdgeV113FinalHistory";
const ACTIVE_MODE="boatEdgeV101ActiveMode";

let archiveIndex=null;
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
    return `結果 ${r.trifecta||"確定"}${pay}`;
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
async function renderHomeHub(){
  const host=ensureHomeHub();if(!host)return;
  const idx=await loadArchiveIndex();
  const dates=[...(idx?.dates||[])].map(x=>x.ymd).sort();
  if(!dates.length){host.innerHTML='<div class="be108-empty">保存データ準備中</div>';return}
  if(!selectedDate||!dates.includes(selectedDate))selectedDate=dates.includes(todayYmd())?todayYmd():dates[dates.length-1];
  const day=await loadArchiveDay(selectedDate);
  if(selectedVenue&&!(day?.venues||[]).some(v=>String(v.jcd)===String(selectedVenue)))selectedVenue=null;
  const i=dates.indexOf(selectedDate),prev=dates[i-1]||"",next=dates[i+1]||"";
  host.innerHTML=`<div class="be108-shell">
    <div class="be108-date-nav">
      <button type="button" data-be108-day="${prev}" ${prev?"":"disabled"}>‹ 前日</button>
      <div><b>${selectedDate===todayYmd()?"本日 ":""}${dateLabel(selectedDate)}のレース</b><span>日付 → 場 → レース</span></div>
      <button type="button" data-be108-day="${next}" ${next?"":"disabled"}>翌日 ›</button>
    </div>
    ${venueGrid(day)}
    ${venuePanel(day)}
  </div>`;
  saveSelection();

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
function confidence(pred,mode,rows){
  const map={S:90,"S+":93,A:82,"A+":86,B:72,"B+":76,C:62,D:52};
  let base=map[String(pred?.grade||"").toUpperCase()]??68;
  const all=allTickets(pred),sum=all.reduce((s,x)=>s+x.p,0),top=all.slice(0,3).reduce((s,x)=>s+x.p,0);
  base+=Math.round(((sum?top/sum:0)-.35)*18)+({hit:5,balance:0,hole:-9,narrow:-5}[mode]||0);
  if(rows.length<=3)base-=2;
  return Math.max(35,Math.min(94,Math.round(base)));
}
function selectModes(pred,odds){
  const all=allTickets(pred),od=x=>{const v=n(odds?.[x.combo]);return Number.isFinite(v)&&v>0?v:null};
  const vals=all.map(od).filter(Number.isFinite).sort((a,b)=>a-b),med=vals.length?vals[Math.floor(vals.length/2)]:null;
  const modes={
    hit:all.slice(0,Math.min(10,all.length)),
    balance:[...all].sort((a,b)=>(b.p*Math.sqrt(Math.min(od(b)??1,80)))-(a.p*Math.sqrt(Math.min(od(a)??1,80)))).slice(0,Math.min(6,all.length)),
    hole:[...all].filter(x=>od(x)!=null&&(med==null||od(x)>=med)).sort((a,b)=>(b.p*Math.pow(Math.min(od(b)??1,120),.72))-(a.p*Math.pow(Math.min(od(a)??1,120),.72))).slice(0,Math.min(6,all.length)),
    narrow:all.slice(0,Math.min(3,all.length))
  };
  if(!modes.hole.length)modes.hole=all.slice(Math.min(3,all.length),Math.min(9,all.length));
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
  const hits=(readLocal(HISTORY,[])||[]).filter(x=>x.hit_any&&x.snapshot_window==="FINAL_15M"&&x.snapshot_schema==="boat-edge-v113-final-snapshot-v1");
  if(!hits.length)return '<div class="be108-emptyline">締切15分前の最終予想による🎯履歴はまだありません。</div>';
  return hits.slice(0,30).map(x=>`<div class="be108-history-row"><div><b>🎯 ${esc(x.venue)} ${esc(x.race_no)}R</b><span>${esc(x.winning_combo)}</span></div><div><small>${Object.entries(x.mode_hits||{}).filter(([,v])=>v).map(([k])=>LABELS[k]?.name||k).join(" / ")}</small>${x.payout?`<strong>${yen(x.payout)}/100円</strong>`:""}</div></div>`).join("");
}
function renderTicketRows(rows,win){
  return rows.map((x,i)=>`<div class="be108-ticket ${win===x.combo?"hit":""}"><span>${i+1}</span><b>${win===x.combo?"🎯 ":""}${esc(x.combo)}</b><em>${pct(x.p)}</em><small>${x.odds?x.odds.toFixed(1)+"倍":"オッズ－"}</small></div>`).join("");
}
async function renderPredictionModes(race,pred){
  const key=race?.race_key;if(!key||!pred)return;
  const stack=$("#tab-pred .section.stack");if(!stack)return;

  const [odds,result]=await Promise.all([oddsFor(key),resultFor(key)]);
  const modes=selectModes(pred,odds);
  const mins=raceMinutesToDeadline(race);
  const resultConfirmed=result?.status==="confirmed";
  const inFinalWindow=!resultConfirmed && mins!==null && mins>=0 && mins<=15;

  let snap=readLocal(snapKey(key));
  if(inFinalWindow){
    snap=saveFinalSnapshot(key,race,pred,modes,mins);
  }

  const finalSnap=isFinalSnapshot(snap)?snap:null;
  const settled=finalSnap&&resultConfirmed?settle(finalSnap,result):null;
  const win=settled?.winning_combo||null;

  let mode=localStorage.getItem(ACTIVE_MODE)||"balance";
  if(!LABELS[mode])mode="balance";

  const frozenRows=finalSnap?.modes?.[mode]?.tickets||null;
  const baseRows=(resultConfirmed&&frozenRows)?frozenRows:modes[mode]||[];
  const rows=baseRows.map(x=>({
    ...x,
    odds:x.odds??(Number.isFinite(n(odds[x.combo]))?n(odds[x.combo]):null)
  }));
  const conf=(resultConfirmed&&finalSnap?.modes?.[mode]?.confidence!=null)
    ? finalSnap.modes[mode].confidence
    : confidence(pred,mode,rows);

  let snapStatus="🎯履歴は締切15分前から保存";
  if(inFinalWindow){
    snapStatus=`🎯 最終予想を保存中・締切まで${mins}分`;
  }else if(resultConfirmed&&finalSnap){
    snapStatus=`🎯 締切前最終予想で判定・${esc(finalSnap.saved_at||"")}`;
  }else if(resultConfirmed&&!finalSnap){
    snapStatus="この端末に締切前の最終スナップショットなし・🎯判定対象外";
  }else if(mins!==null&&mins<0){
    snapStatus=finalSnap
      ?"締切済み・保存した最終予想を固定中"
      :"締切済み・締切前スナップショットなし";
  }

  let panel=$("#be108PredictionModes");
  if(!panel){
    panel=document.createElement("section");
    panel.id="be108PredictionModes";
    panel.className="be108-panel";
    stack.prepend(panel);
  }

  panel.innerHTML=`<div class="be108-head"><div><h3>予想スタイル</h3><p>目的別に買い目を切替</p></div><button id="be108HistoryBtn" type="button">🎯 的中履歴</button></div>
  <div class="be108-snapshot-status">${snapStatus}</div>
  <div class="be108-mode-tabs">${Object.entries(LABELS).map(([k,v])=>`<button type="button" data-be108-mode="${k}" class="${k===mode?"on":""}">${settled?.mode_hits?.[k]?"🎯 ":""}${v.name}</button>`).join("")}</div>
  <div class="be108-mode-card ${settled?.mode_hits?.[mode]?"hit":""}"><div class="be108-mode-top"><div><b>${settled?.mode_hits?.[mode]?"🎯 ":""}${LABELS[mode].icon} ${LABELS[mode].name}</b><span>${LABELS[mode].desc}</span></div><div><small>内部信頼度</small><strong>${conf}%</strong></div></div><div class="be108-ticket-list">${renderTicketRows(rows,win)}</div></div>
  <div id="be108History" class="be108-history" hidden>${historyHtml()}</div>`;

  $$("[data-be108-mode]",panel).forEach(b=>b.onclick=()=>{
    localStorage.setItem(ACTIVE_MODE,b.dataset.be108Mode);
    renderPredictionModes(race,pred);
  });
  $("#be108HistoryBtn",panel).onclick=()=>{
    const h=$("#be108History",panel);
    h.hidden=!h.hidden;
  };
}
function renderMainPick(race,pred){
  const stack=$("#tab-pred .section.stack");if(!stack||!pred)return;
  const top=allTickets(pred)[0];if(!top)return;
  let box=$("#be108MainPick");if(!box){box=document.createElement("div");box.id="be108MainPick";box.className="be108-mainpick";stack.prepend(box)}
  box.innerHTML=`<div><small>メイン予想</small><b>${esc(top.combo)}</b><span>${pct(top.p)} / 勝負度 ${esc(pred.grade||"－")}</span></div><em>${pred.mode==="formal"?"正式CURRENT":"暫定"}</em>`;
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
function showHeadPrediction(boat){
  const lane=Number(boat.dataset.be108Lane),pred=predOf();if(!lane||!pred)return;
  const rows=allTickets(pred).filter(x=>String(x.combo).startsWith(lane+"-")).slice(0,5);
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
  cleanTabs();fixBottom();installBackButtons();enhanceRaceNav(race);
  const pred=predOf(race);
  renderMainPick(race,pred);
  markStandouts();
  await Promise.all([renderPredictionModes(race,pred),augmentBuyBoard(race)]);
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
  const p=predOf(r);
  renderPredictionModes(r,p);
  augmentBuyBoard(r);
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
        const r=raceOf(),p=predOf(r);
        renderMainPick(r,p);
        renderPredictionModes(r,p);
        augmentBuyBoard(r);
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
if(raceOf())afterRace(raceOf());
})();
