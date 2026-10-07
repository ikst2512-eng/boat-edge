/* BOAT_EDGE_V96_UX_UPGRADE */
(()=>{"use strict";
const $=s=>document.querySelector(s);
const E=x=>String(x??"－");
async function J(u){const r=await fetch(u+(u.includes("?")?"&":"?")+"t="+Date.now(),{cache:"no-store"});if(!r.ok)throw Error(r.status);return r.json()}
function distribution(f){let a=f?.distribution120||f?.distribution_120||f?.all_combinations||f?.allCombinations||f?.trifecta_distribution||f?.probabilities;if(Array.isArray(a))return a.map(x=>({c:x.combo||x.combination||x.ticket,p:Number(x.probability??x.prob??x.p),r:x.reason||x.rationale||""})).filter(x=>x.c&&Number.isFinite(x.p)).sort((a,b)=>b.p-a.p);if(a&&typeof a==="object")return Object.entries(a).map(([c,v])=>({c,p:Number(typeof v==="object"?(v.probability??v.prob??v.p):v),r:typeof v==="object"?(v.reason||v.rationale||""):""})).filter(x=>Number.isFinite(x.p)).sort((a,b)=>b.p-a.p);return[]}
async function showHead(d){
  if(!d.open||d.dataset.be96==="1")return;
  d.dataset.be96="1";
  const lane=d.querySelector("summary b")?.textContent?.trim()?.match(/^([1-6])/ )?.[1];
  if(!lane)return;
  let box=document.createElement("div");box.className="be96-head";box.innerHTML="<b>"+lane+"号艇が1着の正式予想</b><p>読込中…</p>";d.appendChild(box);
  try{
    const f=window.be90cur?.f;if(!f)throw Error("race");
    const rd=await J(f),k=rd.race_key||f.match(/(\d{8}-\d{2}-\d{2})/)?.[1];
    const [fp,o]=await Promise.all([J("./data/formal_predictions/"+k+".json").catch(()=>null),J("./data/site_odds/"+k+".json").catch(()=>null)]);
    const a=distribution(fp).filter(x=>String(x.c).startsWith(lane+"-")).slice(0,5),om=o?.trifecta_odds||{};
    box.innerHTML="<b>"+lane+"号艇が1着の正式予想</b>"+(a.length?a.map((x,i)=>"<div><strong>#"+(i+1)+" "+E(x.c)+"</strong><span>"+(x.p<=1?x.p*100:x.p).toFixed(2)+"%</span><span>"+(om[x.c]?om[x.c]+"倍":"オッズ待ち")+"</span></div>").join(""):"<p>正式120確率が未接続のため、頭予想は作りません。</p>");
  }catch(e){box.innerHTML="<b>"+lane+"号艇が1着の正式予想</b><p>正式予想データ待ち</p>"}
}
document.addEventListener("toggle",e=>{if(e.target.matches?.(".be94racer"))showHead(e.target)},true);
function highlight(){
  const cards=[...document.querySelectorAll(".be94racer")];if(cards.length!==6)return;
  const vals=cards.map((c,i)=>{const boxes=[...c.querySelectorAll(".be94stats>div")];const parse=b=>{let n=parseFloat(b?.querySelector("b")?.textContent);return Number.isFinite(n)?n:null};return{c,i,nat:parse(boxes[0]),loc:parse(boxes[1]),mot:parse(boxes[2]),boxes}});
  ["nat","loc","mot"].forEach((key,bi)=>{let v=vals.filter(x=>x[key]!=null).sort((a,b)=>b[key]-a[key]);vals.forEach(x=>x.boxes[bi]?.classList.remove("be96-best","be96-second"));if(v[0])v[0].boxes[bi]?.classList.add("be96-best");if(v[1])v[1].boxes[bi]?.classList.add("be96-second")});
}
function simplifyFlow(){
  const f=$("#scenarioFlow");if(!f||f.dataset.be96)return;
  const txt=f.textContent||""; if(!txt.trim())return;
  const conclusion=(txt.match(/結論[\s\S]*/)||[])[0]||"直前データに応じて更新";
  f.dataset.be96="1";
  f.innerHTML='<div class="be96-flow"><h3>レースの流れ</h3><div><em>①</em><span><small>まず見る</small><b>誰がスタートで前に出そうか</b></span></div><div><em>②</em><span><small>次に見る</small><b>誰が1マークで攻めるか</b></span></div><div><em>③</em><span><small>その結果</small><b>内が残るか、外が展開をもらうか</b></span></div><div class="last"><em>④</em><span><small>結論</small><b>'+E(conclusion.replace("結論","").trim())+'</b></span></div></div>';
}
function nav(){const b=[...document.querySelectorAll(".bottomnav button")].find(x=>x.dataset.view==="raceView");if(b){b.innerHTML='<span class="navicon">◎</span>予想';b.dataset.be96="1"}}
nav();highlight();simplifyFlow();
setInterval(()=>{nav();highlight();simplifyFlow()},1500);
})();
