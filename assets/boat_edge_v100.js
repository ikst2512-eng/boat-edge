/* BOAT_EDGE_V100_TOP_NAVIGATION_UX */
(()=>{"use strict";
const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=v=>String(v??"－").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const yen=v=>Number.isFinite(Number(v))?Math.round(Number(v)).toLocaleString("ja-JP")+"円":"－";
const ptxt=v=>{const n=Number(v);if(!Number.isFinite(n))return "－";return (n<=1?n*100:n).toFixed(1)+"%"};

function currentRace(){try{return typeof state!=="undefined"?state.race:null}catch(_){return null}}
function currentPrediction(){
  try{const r=currentRace();return r&&typeof getPrediction==="function"?getPrediction(r):null}catch(_){return null}
}
function topTicket(pred){
  const rows=[];
  for(const [wi,w] of (pred?.worlds||[]).entries()){
    for(const [i,t] of (w?.tickets||[]).entries()){
      const p=Number(t?.probability??t?.prob??t?.p);
      rows.push({combo:t?.combo||t?.trifecta||t?.order||"－",p:Number.isFinite(p)?p:-1,amount:Number(t?.amount||0),world:w?.key||(wi===0?"A":"B"),rank:i+1});
    }
  }
  rows.sort((a,b)=>b.p-a.p);
  return rows[0]||null;
}
function ensureBack(){
  const top=$("#raceView .summary-top"); if(!top)return;
  let b=$(".be100-back",top);
  if(!b){
    b=document.createElement("button");b.className="be100-back";b.type="button";b.innerHTML="← 戻る";
    top.insertBefore(b,top.firstChild);
  }
  b.onclick=()=>{
    try{
      if(typeof showView==="function"){
        showView("homeView");
        const y=Number(sessionStorage.getItem("be100HomeScroll")||0);
        setTimeout(()=>window.scrollTo({top:y,behavior:"instant"}),30);
        return;
      }
    }catch(_){}
    history.back();
  };
}
function rememberHomePosition(){
  document.addEventListener("click",e=>{
    const btn=e.target.closest?.("[data-file]");
    if(!btn)return;
    if(btn.closest("#raceNav"))return;
    if($("#homeView")?.classList.contains("active")){
      try{sessionStorage.setItem("be100HomeScroll",String(window.scrollY||0))}catch(_){}
    }
  },true);
}
function ensureNavShell(){
  const summary=$("#raceView .race-summary"), top=$("#raceView .summary-top");
  const raceNav=$("#raceNav"), tabs=$("#raceTabs");
  if(!summary||!top||!raceNav||!tabs)return null;
  let shell=$("#be100NavShell");
  if(!shell){
    shell=document.createElement("div");shell.id="be100NavShell";shell.className="be100-nav-shell";
    top.insertAdjacentElement("afterend",shell);
  }
  if(raceNav.parentElement!==shell)shell.appendChild(raceNav);
  if(tabs.parentElement!==shell)shell.appendChild(tabs);
  return shell;
}
function tuneTabs(){
  const tabs=$("#raceTabs"); if(!tabs)return;
  const names={pred:"予想",scenario:"展開",card:"選手",before:"直前",data:"データ",audit:"監査",direct:"直前モード"};
  $$('[data-tab]',tabs).forEach(b=>{
    const k=b.dataset.tab;
    if(names[k])b.textContent=names[k];
    b.classList.toggle("be100-hidden-tab",k==="direct");
  });
  const active=$("[data-tab].on",tabs);
  if(active?.dataset.tab==="direct"){
    const p=$("[data-tab='pred']",tabs); if(p)p.click();
  }
}
function scrollActiveRace(){
  const nav=$("#raceNav"); if(!nav)return;
  const active=$(".before",nav)||$(".on",nav)||$(".active",nav);
  if(active)try{active.scrollIntoView({behavior:"smooth",inline:"center",block:"nearest"})}catch(_){}
}
function renderMainPick(){
  const shell=ensureNavShell(); if(!shell)return;
  let box=$("#be100MainPick");
  if(!box){box=document.createElement("div");box.id="be100MainPick";box.className="be100-mainpick";shell.insertAdjacentElement("afterend",box)}
  const r=currentRace(), pred=currentPrediction(), t=topTicket(pred);
  const mode=pred?.mode==="formal"?"正式CURRENT":"暫定メイン";
  const venue=r?.meta?.venue||"レース", no=r?.meta?.race_no?`${r.meta.race_no}R`:"";
  if(!pred||!t){
    box.innerHTML=`<div class="be100-main-label">メイン予想</div><div class="be100-main-empty">予想データ待ち</div>`;return;
  }
  box.innerHTML=`
    <div class="be100-main-top"><span class="be100-main-label">メイン予想</span><span class="be100-mode ${pred.mode==="formal"?"formal":"temp"}">${mode}</span></div>
    <div class="be100-main-row">
      <div><div class="be100-race-name">${esc(venue)} ${esc(no)}</div><div class="be100-combo">${esc(t.combo)}</div></div>
      <div class="be100-main-metrics"><span><small>確率</small><b>${ptxt(t.p)}</b></span><span><small>配分</small><b>${t.amount>0?yen(t.amount):"－"}</b></span></div>
    </div>
    <div class="be100-main-sub"><b>${esc(pred?.decision||"判断待ち")}</b><span>勝負度 ${esc(pred?.grade||"－")}</span></div>`;
}
function prioritizePredictionDetail(){
  const stack=$("#tab-pred .section.stack"), buy=$("#buyBoard");
  if(stack&&buy&&stack.firstElementChild!==buy)stack.insertBefore(buy,stack.firstElementChild);
}
function compactTop(){
  for(const id of ["summaryStrip","raceCommand","raceMasthead","urgencyRibbon","freshnessStrip","raceQuickNav"]){const el=$("#"+id);if(el)el.classList.add("be100-hide-top")}
  const decision=$("#decision"); if(decision)decision.classList.add("be100-hide-duplicate");
}
function enhance(){
  if(!$("#raceView"))return;
  ensureBack();
  ensureNavShell();
  tuneTabs();
  compactTop();
  prioritizePredictionDetail();
  renderMainPick();
  setTimeout(scrollActiveRace,40);
}
let timer=null;
function schedule(){clearTimeout(timer);timer=setTimeout(enhance,40)}
rememberHomePosition();
new MutationObserver(schedule).observe(document.documentElement,{subtree:true,childList:true,characterData:true});
document.addEventListener("click",e=>{if(e.target.closest?.("#raceNav [data-file],#raceTabs [data-tab]"))setTimeout(enhance,120)},true);
setInterval(()=>{if($("#raceView")?.classList.contains("active"))enhance()},1200);
enhance();
})();
