(()=>{"use strict";
const q=s=>document.querySelector(s), qa=s=>[...document.querySelectorAll(s)];
const esc=v=>String(v??"—").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const value=v=>(v===null||v===undefined||v==="")?"—":v;
const laneNo=(r,i)=>Number(r?.lane??(i+1));
const lane=l=>`<span class="be48-lane l${l}">${l}</span>`;
function S(){try{return typeof state!=="undefined"?state:null}catch(_){return null}}
function rawRace(){return S()?.race||null}
/* Source .world-prob already contains percent units. 0.5 means 0.5%, not 50%. */
function normPct(v){
 if(v===null||v===undefined||String(v).trim()==='')return null;
 const n=Number(v);
 return Number.isFinite(n)&&n>=0&&n<=100?n:null;
}
function decorateWorlds(){
  qa("#worlds .world").forEach((w,wi)=>{
    const key=wi===0?"A":"B";
    const h=w.querySelector("h3"); if(h)h.textContent=key==="A"?"イン逃げ成立":"イン逃げ不成立";
    w.querySelectorAll(".badge").forEach(x=>x.style.display="none");
    const pr=w.querySelector(".world-prob");
    if(pr){
      // Never interpret an already-formatted percent as a fractional probability.
      const m=String(pr.textContent||'').trim().match(/^(\d+(?:\.\d+)?)%$/);
      if(m){const n=normPct(m[1]);if(n!==null)pr.textContent=`${n.toFixed(n%1?1:0)}%`;}
    }
    const tickets=[...w.querySelectorAll(".ticket")];
    tickets.forEach((t,i)=>{
      const c=t.querySelector(".combo"); if(c&&!c.dataset.be48){const parts=c.textContent.trim().split(/[-–—>＞\s]+/).filter(x=>/^[1-6]$/.test(x));if(parts.length===3)c.innerHTML=parts.map(x=>lane(Number(x))).join('<span class="be48-sep">–</span>');c.dataset.be48="1";}
      const rank=t.querySelector(".rank");if(rank)rank.style.display="none";
      if(i===0)t.classList.add("be48-best");
      if(i>=3)t.classList.add("be48-extra");
    });
    if(tickets.length>3&&!w.querySelector(".be48-more")){const b=document.createElement("button");b.className="be48-more";b.textContent=`他の買い目を見る（${tickets.length-3}点）`;b.onclick=()=>{w.classList.toggle("be48-open");b.textContent=w.classList.contains("be48-open")?"買い目を閉じる":`他の買い目を見る（${tickets.length-3}点）`};w.querySelector(".ticketlist")?.after(b);}
  });
}
function renderRacers(d){
  const host=q("#be48Racers");if(!host)return;
  host.innerHTML=(d?.racers||[]).map((r,i)=>{const l=laneNo(r,i),n=r.national||{},loc=r.local||{},m=r.motor||{},b=r.boat||{};
    const p=x=>{if(x===null||x===undefined||String(x).trim()==='')return '—';
      const n=Number(x);return Number.isFinite(n)?`${n.toFixed(1)}%`:'—'};
    return `<article class="be48-racer">${lane(l)}<div class="be48-rmain"><b>${esc(value(r.name))}</b><span>${esc(value(r.class))} / 平均ST ${esc(value(r.avg_st))}</span><span>全国 ${esc(value(n.win_rate))}　当地 ${esc(value(loc.win_rate))}</span></div><div class="be48-rside"><span>M2<b>${p(m.quinella_rate)}</b></span><span>B2<b>${p(b.quinella_rate)}</b></span></div></article>`}).join("")||'<div class="be48-empty">選手データがありません</div>';
}
/* UI-only source boundary: no result, odds, or post-deadline field is inferred. */
function sourceReady(d,kind){
 const key=String(d?.race_key||''),m=d?.meta||{},a=d?.source_audit?.[kind];
 if(!/^20\d{6}-(?:0[1-9]|1\d|2[0-4])-(?:0[1-9]|1[0-2])$/.test(key)||
    m.phase!=='PRE_RESULT'||m.results_seen!==false||m.unlock!==false||m.scoring!==false||
    m.date!==key.slice(0,4)+'-'+key.slice(4,6)+'-'+key.slice(6,8)||
    String(m.venue_code||'').padStart(2,'0')!==key.slice(9,11)||
    Number(m.race_no)!==Number(key.slice(12,14))||
    !/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(String(m.deadline||''))||
    a?.status!=='ok'||!/^[a-f0-9]{64}$/i.test(String(a.sha256||'')))return false;
 const due=Date.parse(m.date+'T'+m.deadline+':00+09:00'),fetched=Date.parse(a.fetched_at||'');
 return Number.isFinite(due)&&Number.isFinite(fetched)&&fetched<=due&&fetched<=Date.now()+60000;
}
function uniqueBeforeLanes(items){
 const found=new Map(),duplicates=new Set();
 for(const item of Array.isArray(items)?items:[]){
  const lane=Number(item?.lane);
  if(!Number.isInteger(lane)||lane<1||lane>6||typeof item?.lane==='boolean')continue;
  if(found.has(lane))duplicates.add(lane);else found.set(lane,item);
 }
 for(const lane of duplicates)found.delete(lane);
 return found;
}
function beforeMaps(d){
 const official=sourceReady(d,'beforeinfo'),sttReady=sourceReady(d,'stt');
 const bf=official?d.beforeinfo||{}:{};
 const starts=official?uniqueBeforeLanes(bf.start_exhibition):new Map();
 const by=official?uniqueBeforeLanes(bf.racers):new Map();
 const stt=sttReady?uniqueBeforeLanes(d.actual_entry):new Map();
 const actual=new Map(),entryCounts=new Map();
 for(let l=1;l<=6;l++){
  const s=starts.get(l),t=stt.get(l);
  const raw=s?.course??t?.course??t?.actual_course??t?.entry_course;
  if(raw===null||raw===undefined||typeof raw==='boolean'||String(raw).trim()==='')continue;
  const course=Number(raw);
  if(Number.isInteger(course)&&course>=1&&course<=6){
   actual.set(l,course);entryCounts.set(course,(entryCounts.get(course)||0)+1);
  }
 }
 // Duplicate exhibition positions are ambiguous; never label either as confirmed.
 for(const [lane,course] of actual)if(entryCounts.get(course)>1)actual.delete(lane);
 return {bf,starts,by,stt,actual,official,sttReady};
}
function renderBeforeCompact(d){
 const host=q("#be48Before");if(!host)return;
 const {starts,by,stt,actual,official,sttReady}=beforeMaps(d);
 const names=uniqueBeforeLanes(d?.racers);
 const en=[...actual.entries()].sort((a,b)=>a[0]-b[0]);
 let s=`<div class="be48-entry"><span>展示進入（枠→コース・保存値）</span><b>${esc(en.length?en.map(([l,c])=>`${l}→${c}`).join("　"):"—")}</b></div><div class="be48-bhead"><span>艇</span><span>選手</span><span>展示ST</span><span>展示タイム</span><span>チルト</span></div>`;
 for(let l=1;l<=6;l++){
  const row=by.get(l)||{},start=starts.get(l)||{},fallback=stt.get(l)||{};
  const rawSt=start.st??start.start_timing??start.start??fallback.exhibition_st_raw??fallback.exhibition_st;
  s+=`<div class="be48-brow">${lane(l)}<b>${esc(value(names.get(l)?.name))}</b><span>${esc(value(rawSt))}</span><span>${esc(value(row.exhibition_time))}</span><span>${esc(value(row.tilt))}</span></div>`;
 }
 host.innerHTML=s+'<div class="be48-note">'+
   (official||sttReady?'締切前の取得証跡を照合した保存値のみ表示。':'直前情報の締切前取得・SHA証跡が未確認のため数値を非表示。')+
   ' 未取得・進入不一致・艇番重複は「—」。展示進入は本番進入とは異なります。</div>';
}
function compactDetails(d){
  const card=q("#tab-card .section"),before=q("#tab-before .section");
  if(card&&!q("#be48Racers")){const x=document.createElement("div");x.className="be48-compact";x.innerHTML='<div class="be48-title">選手・6艇比較</div><div id="be48Racers"></div>';card.prepend(x)}
  if(before&&!q("#be48Before")){const x=document.createElement("div");x.className="be48-compact";x.innerHTML='<div class="be48-title">直前情報</div><div id="be48Before"></div>';before.prepend(x)}
  renderRacers(d);renderBeforeCompact(d);
}
function detailBar(){
  const pred=q("#tab-pred .section");if(!pred||q("#be48DetailBar"))return;
  const bar=document.createElement("div");bar.id="be48DetailBar";bar.className="be48-detailbar";
  [["scenario","展開"],["card","選手"],["before","直前"],["data","データ"],["audit","監査"]].forEach(([id,label])=>{const b=document.createElement("button");b.textContent=label;b.onclick=()=>{const tab=q(`#raceTabs [data-tab="${id}"]`);if(tab)tab.click();else{qa(".subview").forEach(x=>x.classList.toggle("active",x.id===`tab-${id}`));}};bar.appendChild(b)});
  pred.appendChild(bar);
}
/* A frozen-looking budget can exist in legacy world markup while verified
 * V207 tickets are stopped; only the current race's visible tickets permit
 * an actionable navigation label. No stake or prediction is changed. */
function actionBar(d){
  let x=q("#be48Action");
  if(!x){x=document.createElement("div");x.id="be48Action";x.className="be48-action";q("#raceView")?.appendChild(x)}
  const title=q("#raceTitle")?.textContent?.trim()||"レース";
  const deadline=q("#deadlineBig")?.textContent?.trim()||"—";
  const pick=q("#be207Top");
  const sameRace=Boolean(d?.race_key&&rawRace()?.race_key===d.race_key);
  const ready=Boolean(sameRace&&pick?.classList?.contains("ready")&&
    !pick.querySelector(".be207-stop")&&pick.querySelector(".be207-ticket")&&
    !document.documentElement.classList.contains("be306-race-await")&&
    !q("#raceView")?.classList?.contains("be03-race-loading"));
  x.dataset.be48TicketState=ready?"ready":"stopped";
  const status=ready?"買い目を表示中（購入ではありません）":
    "買い目停止・直前情報または保存状態を確認中";
  x.innerHTML=`<div><b>${esc(title)}</b><span>締切 ${esc(deadline)} / ${status}</span></div><button type="button">${ready?"買い目を確認":"取得状況を見る"}</button>`;
  x.querySelector("button").onclick=()=>{
    (q("#be207Top")||q("#tab-pred"))?.scrollIntoView({behavior:"smooth",block:"start"});
  };
}
let be48ActionQueued=false;
function scheduleActionBar(){
  if(be48ActionQueued)return;
  be48ActionQueued=true;
  queueMicrotask(()=>{be48ActionQueued=false;if(rawRace())actionBar(rawRace())});
}
function raceRefresh(d){decorateWorlds();compactDetails(d);detailBar();actionBar(d)}
function install(){
  if(typeof renderRace==="function"&&!renderRace.__be48){const orig=renderRace;const wrapped=function(d){const r=orig.apply(this,arguments);queueMicrotask(()=>raceRefresh(d));return r};wrapped.__be48=true;renderRace=wrapped}
  if(typeof showView==="function"&&!showView.__be48){const orig=showView;const wrapped=function(id){const r=orig.apply(this,arguments);document.body.classList.toggle("be48-race-active",id==="raceView");return r};wrapped.__be48=true;showView=wrapped}
  // V207 refreshes its ticket rows after the base race render.
  // Follow changes without ever reusing another race's legacy budget.
  const predPanel=q("#tab-pred");
  if(predPanel&&typeof MutationObserver==="function"){
    new MutationObserver(scheduleActionBar).observe(predPanel,{
      subtree:true,childList:true,attributes:true,attributeFilter:["class","data-status"]
    });
  }
  if(rawRace())raceRefresh(rawRace());
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});else install();
})();