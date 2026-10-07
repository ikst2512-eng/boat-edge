/* BOAT_EDGE_V107_TAB_BACK_CLEANUP */
(()=>{"use strict";
const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>[...r.querySelectorAll(s)];
const STACK_KEY="boatEdgeV107ViewStack";
const ORDER=["pred","scenario","card","before","data","audit"];
const LABEL={pred:"予想",scenario:"展開",card:"選手",before:"直前",data:"データ",audit:"監査"};

function getStack(){
  try{return JSON.parse(sessionStorage.getItem(STACK_KEY)||"[]")}catch(_){return []}
}
function setStack(v){
  try{sessionStorage.setItem(STACK_KEY,JSON.stringify(v.slice(-30)))}catch(_){}
}
function activeView(){return $(".view.active")?.id||"homeView"}
function pushView(id){
  const s=getStack(),last=s[s.length-1];
  if(last!==id){s.push(id);setStack(s)}
}
function goView(id){
  if(typeof window.showView==="function"){window.showView(id);return}
  $$(".view").forEach(v=>v.classList.toggle("active",v.id===id));
  $$(".bottomnav [data-view]").forEach(v=>v.classList.toggle("on",v.dataset.view===id));
  window.scrollTo({top:0,behavior:"smooth"});
}
function siteBack(){
  const s=getStack();
  let id=s.pop()||"homeView";
  setStack(s);
  if(!$("#"+id))id="homeView";
  goView(id);
}
function fixBottom(){
  const b=$('.bottomnav [data-view="raceView"]');
  if(b){
    const icon=$(".navicon",b)?.outerHTML||'<span class="navicon">◎</span>';
    b.innerHTML=icon+"予想";
  }
}
function fixTabs(){
  const tabs=$("#raceTabs");if(!tabs)return;
  const map=new Map($$("[data-tab]",tabs).map(b=>[b.dataset.tab,b]));
  const direct=map.get("direct");
  if(direct)direct.remove();
  const dview=$("#tab-direct");
  if(dview){
    dview.classList.remove("active");
    dview.style.display="none";
  }
  for(const key of ORDER){
    const b=map.get(key);
    if(!b)continue;
    b.textContent=LABEL[key];
    tabs.appendChild(b);
  }
  const active=$("[data-tab].on",tabs);
  if(!active || !ORDER.includes(active.dataset.tab)){
    $$("[data-tab]",tabs).forEach(b=>b.classList.toggle("on",b.dataset.tab==="pred"));
    $$(".subview").forEach(v=>v.classList.toggle("active",v.id==="tab-pred"));
  }
}
function fixBackButtons(){
  for(const sel of [".be105-back",".be104-view-back button",".be103-view-back button"]){
    $$(sel).forEach(b=>{
      b.textContent="← 戻る";
      b.onclick=e=>{e.preventDefault();e.stopPropagation();siteBack()};
    });
  }
}
function captureBottom(){
  document.addEventListener("click",e=>{
    const b=e.target.closest?.(".bottomnav [data-view]");
    if(!b)return;
    const dest=b.dataset.view,cur=activeView();
    if(dest&&dest!==cur)pushView(cur);
  },true);
}
function captureRaceOpen(){
  document.addEventListener("click",e=>{
    const race=e.target.closest?.("[data-file],[data-race-file]");
    if(!race)return;
    if(activeView()!=="raceView")pushView(activeView());
  },true);
}
function tidy(){fixBottom();fixTabs();fixBackButtons()}
captureBottom();captureRaceOpen();tidy();
new MutationObserver(()=>tidy()).observe(document.documentElement,{subtree:true,childList:true});
setInterval(tidy,1500);
})();
