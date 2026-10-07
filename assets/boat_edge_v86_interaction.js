/* BOAT_EDGE_V86_INTERACTION_GUARD */
(()=>{
"use strict";
window.BOAT_EDGE_SITE_VERSION="V86";
function toast(msg){
 let x=document.getElementById("be86Toast");
 if(!x){x=document.createElement("div");x.id="be86Toast";x.style.cssText="position:fixed;left:12px;right:12px;bottom:18px;z-index:9999;background:#102d50;color:#fff;padding:12px 14px;border-radius:12px;font:700 12px/1.5 system-ui;box-shadow:0 8px 28px #0003";document.body.appendChild(x)}
 x.textContent=msg;x.hidden=false;clearTimeout(x._t);x._t=setTimeout(()=>x.hidden=true,4500);
}
window.addEventListener("error",e=>toast("画面エラー: "+(e.message||"不明")));
window.addEventListener("unhandledrejection",e=>toast("読込エラー: "+(e.reason?.message||e.reason||"不明")));
document.addEventListener("click",async e=>{
 const b=e.target.closest("button[data-file]");
 if(!b)return;
 const file=b.dataset.file,jcd=b.dataset.jcd;
 if(!file)return;
 e.preventDefault();e.stopPropagation();
 b.disabled=true;
 try{
   if(typeof loadRace!=="function")throw new Error("loadRace が見つかりません");
   await loadRace(file,jcd);
 }catch(err){
   console.error("V86 loadRace",err);
   toast("レースを開けません: "+(err?.message||err));
 }finally{b.disabled=false}
},true);
})();
