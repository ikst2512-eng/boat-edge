(()=>{"use strict";
const q=s=>document.querySelector(s), qa=s=>[...document.querySelectorAll(s)];
const esc=v=>String(v??"—").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const value=v=>(v===null||v===undefined||v==="")?"—":v;
const laneNo=(r,i)=>Number(r?.lane??(i+1));
const lane=l=>`<span class="be48-lane l${l}">${l}</span>`;
function S(){try{return typeof state!=="undefined"?state:null}catch(_){return null}}
function rawRace(){return S()?.race||null}
function normPct(v){const n=Number(v);if(!Number.isFinite(n))return null;return n>=0&&n<=1?n*100:n}
function decorateWorlds(){
  qa("#worlds .world").forEach((w,wi)=>{
    const key=wi===0?"A":"B";
    const h=w.querySelector("h3"); if(h)h.textContent=key==="A"?"イン逃げ成立":"イン逃げ不成立";
    w.querySelectorAll(".badge").forEach(x=>x.style.display="none");
    const pr=w.querySelector(".world-prob");
    if(pr){const m=pr.textContent.match(/-?\d+(?:\.\d+)?/);if(m){const n=normPct(m[0]);if(n!==null)pr.textContent=`${Math.max(0,Math.min(100,n)).toFixed(n%1?1:0)}%`;}}
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
    const p=x=>{const n=Number(x);return Number.isFinite(n)?`${n.toFixed(1)}%`:"—"};
    return `<article class="be48-racer">${lane(l)}<div class="be48-rmain"><b>${esc(value(r.name))}</b><span>${esc(value(r.class))} / 平均ST ${esc(value(r.avg_st))}</span><span>全国 ${esc(value(n.win_rate))}　当地 ${esc(value(loc.win_rate))}</span></div><div class="be48-rside"><span>M2<b>${p(m.quinella_rate)}</b></span><span>B2<b>${p(b.quinella_rate)}</b></span></div></article>`}).join("")||'<div class="be48-empty">選手データがありません</div>';
}
function beforeMaps(d){const bf=d?.beforeinfo||{},starts=new Map(),actual=new Map();(bf.start_exhibition||[]).forEach((x,i)=>starts.set(Number(x.lane??(i+1)),x.st??x.start_timing??x.start));(d?.actual_entry||[]).forEach((x,i)=>{if(typeof x==="number")actual.set(i+1,x);else actual.set(Number(x?.lane??(i+1)),x?.course??x?.actual_course??x?.entry_course)});return{bf,starts,actual}}
function renderBeforeCompact(d){
  const host=q("#be48Before");if(!host)return;const {bf,starts,actual}=beforeMaps(d),names=new Map((d?.racers||[]).map((r,i)=>[laneNo(r,i),r.name])),by=new Map((bf.racers||[]).map((r,i)=>[Number(r.lane??(i+1)),r]));
  const en=[...actual.entries()].sort((a,b)=>a[0]-b[0]);let s=`<div class="be48-entry"><span>実進入</span><b>${esc(en.length?en.map(([l,c])=>`${l}→${value(c)}`).join("　"):"—")}</b></div><div class="be48-bhead"><span>艇</span><span>選手</span><span>展示ST</span><span>展示タイム</span><span>チルト</span></div>`;
  for(let l=1;l<=6;l++){const r=by.get(l)||{};s+=`<div class="be48-brow">${lane(l)}<b>${esc(value(names.get(l)))}</b><span>${esc(value(starts.get(l)))}</span><span>${esc(value(r.exhibition_time))}</span><span>${esc(value(r.tilt))}</span></div>`}
  host.innerHTML=s+'<div class="be48-note">未取得値は補完せず「—」で表示</div>';
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
function actionBar(d){
  let x=q("#be48Action");if(!x){x=document.createElement("div");x.id="be48Action";x.className="be48-action";q("#raceView")?.appendChild(x)}
  const title=q("#raceTitle")?.textContent?.trim()||"レース",deadline=q("#deadlineBig")?.textContent?.trim()||"—",decision=q("#decision")?.textContent?.replace(/\s+/g," ").trim()||"予想確認";
  let total=0;qa("#worlds .world-budget b").forEach(b=>{const n=Number((b.textContent||"").replace(/[^\d]/g,""));if(Number.isFinite(n))total+=n});
  x.innerHTML=`<div><b>${esc(title)}${total?`　合計 ${total.toLocaleString()}円`:""}</b><span>締切 ${esc(deadline)} / ${esc(decision.slice(0,28))}</span></div><button type="button">買い目を見る</button>`;
  x.querySelector("button").onclick=()=>q("#worlds")?.scrollIntoView({behavior:"smooth",block:"start"});
}
function raceRefresh(d){decorateWorlds();compactDetails(d);detailBar();actionBar(d)}
function install(){
  if(typeof renderRace==="function"&&!renderRace.__be48){const orig=renderRace;const wrapped=function(d){const r=orig.apply(this,arguments);queueMicrotask(()=>raceRefresh(d));return r};wrapped.__be48=true;renderRace=wrapped}
  if(typeof showView==="function"&&!showView.__be48){const orig=showView;const wrapped=function(id){const r=orig.apply(this,arguments);document.body.classList.toggle("be48-race-active",id==="raceView");return r};wrapped.__be48=true;showView=wrapped}
  if(rawRace())raceRefresh(rawRace());
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",install,{once:true});else install();
})();