/* BOAT_EDGE_V88_SAFE_BOOT_AND_FORMAL_ADAPTER */
(()=>{
"use strict";
window.BOAT_EDGE_SITE_VERSION="V88";

function safeCall(name){
  try{
    const fn=window[name];
    if(typeof fn==="function") fn();
    return true;
  }catch(e){
    console.error("V88",name,e);
    return false;
  }
}
function bootFallback(){
  const home=document.getElementById("homeView");
  if(!home)return;
  const venues=window.state?.today?.venues||[];
  if(venues.length && !document.querySelector("#venueGrid [data-code],#deadlineBoard [data-file]")){
    const host=document.getElementById("deadlineBoard")||document.getElementById("venueGrid")||home;
    host.innerHTML=venues.map(v=>`<section style="margin:10px 0;padding:12px;background:#fff;border-radius:14px"><b>${v.venue||v.name||"開催場"}</b><div style="display:flex;gap:7px;overflow:auto;margin-top:8px">${(v.races||[]).map(r=>`<button type="button" data-file="${r.file||""}" data-jcd="${v.jcd||""}" style="min-width:62px;padding:10px;border:1px solid #dce6f5;border-radius:10px;background:#fff">${r.race_no||"-"}R<br><small>${r.deadline||""}</small></button>`).join("")}</div></section>`).join("");
  }
}
window.addEventListener("load",()=>{
  setTimeout(()=>{
    ["renderLiveTicker","renderVenueStats","renderSpotlightRaces","renderRecentRaces","renderDeadlineBoard","updateNextRaceBar","renderVenues","renderModelPanels","renderHealthPanels","updateSystemBanner"].forEach(safeCall);
    bootFallback();
  },500);
  setTimeout(bootFallback,1800);
});
})();
