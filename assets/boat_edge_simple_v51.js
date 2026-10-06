/* BOAT_EDGE_SITE_V72_LIVE_STATUS */
(()=>{"use strict";
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const esc=v=>String(v??"—").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const st=()=>typeof state!=="undefined"?state:null;
const KEY="boat_edge_v57_learning_log";
const now=()=>new Date().toISOString();
function readLog(){try{return JSON.parse(localStorage.getItem(KEY)||"[]")}catch(_){return[]}}
function writeLog(v){try{localStorage.setItem(KEY,JSON.stringify(v.slice(-500)))}catch(_){}}
function raceKey(){
 const r=st()?.race||{};
 return [r.date||st()?.today?.date||"",r.jcd||r.venue||"",r.race_no||r.race||""].join("-");
}
function ensureHome(){const h=$("#homeView");if(!h)return null;let a=$("#be51Home");if(!a){a=document.createElement("div");a.id="be51Home";h.prepend(a)}return a}
function mins(d){const m=/^(\d{1,2}):(\d{2})/.exec(String(d||""));if(!m)return null;const n=new Date(),t=new Date(n);t.setHours(+m[1],+m[2],0,0);return Math.floor((t-n)/60000)}
function venueName(v){try{const hit=(typeof VENUES!=="undefined"?VENUES:[]).find(x=>String(x?.[0])===String(v?.jcd));return hit?.[1]||v?.name||v?.venue||v?.jcd||"開催場"}catch(_){return v?.name||v?.venue||v?.jcd||"開催場"}}
function refreshButton(){
 let b=$("#be57Refresh"); if(b)return b;
 b=document.createElement("button"); b.id="be57Refresh"; b.type="button"; b.textContent="↻ 更新";
 b.onclick=()=>{b.disabled=true;b.textContent="更新中…";location.reload()};
 return b;
}
function renderSimpleHome(){
 const a=ensureHome();if(!a)return;
 const vs=(st()?.today?.venues||[]).filter(v=>(v.races||[]).length);
 let sel=a.dataset.venue;if(!vs.some(v=>String(v.jcd)===sel))sel=String(vs[0]?.jcd||"");a.dataset.venue=sel;
 const v=vs.find(x=>String(x.jcd)===sel),rs=(v?.races||[]).filter(r=>{const m=mins(r.deadline);return m==null||m>=0});
 a.innerHTML=`<section class="be51-head"><div><small>BOAT EDGE</small><h1>今日のレース</h1></div><div class="be57-headright"><span>${st()?.today?.updated_at?"更新済み":"読込中"}</span><span id="be57RefreshSlot"></span></div></section><section class="be51-venues">${vs.map(x=>`<button data-v="${esc(x.jcd)}" class="${String(x.jcd)===sel?"on":""}">${esc(venueName(x))}</button>`).join("")||`<div class="be51-empty">開催データを読込中</div>`}</section><section class="be51-box"><div class="be51-title"><b>${esc(venueName(v))}</b><span>レースを選択</span></div><div class="be51-grid">${rs.map(r=>{const m=mins(r.deadline);return `<button class="be51-race" data-file="${esc(r.file)}" data-jcd="${esc(v?.jcd)}"><b>${esc(r.race_no)}R</b><strong>${esc(r.deadline)}</strong><small>${m==null?"":m===0?"締切間近":`あと${m}分`}</small></button>`}).join("")||`<div class="be51-empty">表示できるレースがありません</div>`}</div></section>`;
 $("#be57RefreshSlot",a)?.append(refreshButton());
 $$('[data-v]',a).forEach(b=>b.onclick=()=>{a.dataset.venue=b.dataset.v;renderSimpleHome()});
 $$('[data-file]',a).forEach(b=>b.onclick=()=>{if(typeof loadRace==="function")loadRace(b.dataset.file,b.dataset.jcd)});
}
function cleanClone(node){
 const c=node.cloneNode(true);c.removeAttribute?.("id");
 c.querySelectorAll?.("#be48DetailBar,#be51Details,#be48Action,#be57Decision").forEach(x=>x.remove());
 $$('*',c).forEach(e=>{["id","for","aria-controls","aria-labelledby","aria-describedby"].forEach(x=>e.removeAttribute(x));if(e.tagName==="SCRIPT"||e.tagName==="FORM")e.remove();if(String(e.getAttribute("href")||"").startsWith("#"))e.removeAttribute("href")});
 return c;
}
function simplifyChrome(){
 const old=$("#be48DetailBar");if(old)old.remove();
 document.body.classList.add("be53-simple");
 const rv=$("#raceView");if(!rv)return;
 let back=$("#be53Back");
 if(!back){back=document.createElement("button");back.id="be53Back";back.type="button";back.textContent="← 今日のレース";back.onclick=()=>{const p=$("#be51Panel");if(p){p.hidden=true;p.innerHTML=""}$$("[data-d]").forEach(x=>x.classList.remove("on"));document.body.classList.remove("be48-race-active");if(typeof showView==="function")showView("homeView")};rv.prepend(back)}
 let rr=$("#be57RaceRefresh");if(!rr){rr=refreshButton().cloneNode(true);rr.id="be57RaceRefresh";rr.onclick=()=>{rr.disabled=true;rr.textContent="更新中…";location.reload()};rv.prepend(rr)}
}
function snapshot(){
 // V61: legacy V57 snapshot is disabled. V59/V60 structured snapshot is the only learning source.
 return null;
}
function detectRecommendation(){
 const pred=$("#tab-pred"); const t=(pred?.innerText||"");
 const nums=[...t.matchAll(/(\d+(?:\.\d+)?)\s*%/g)].map(m=>+m[1]).filter(n=>n>=0&&n<=100);
 if(!nums.length)return {label:"AI推奨：データ確認",reason:"確率データを確認して購入判断します。",cls:"wait"};
 nums.sort((a,b)=>b-a); const gap=(nums[0]||0)-(nums[1]||0);
 if((nums[0]||0)<8)return {label:"AI推奨：見送り",reason:"上位候補の確率が低く、予測が分散しています。",cls:"skip"};
 if(gap>=8)return {label:"AI推奨：本線厚め",reason:"最上位候補と次点の確率差が比較的大きいため、本線を厚くする候補です。",cls:"buy"};
 return {label:"AI推奨：分散",reason:"上位候補の確率差が小さいため、1点集中より分散を検討します。",cls:"buy"};
}
function ensureDecision(){
 const p=$("#tab-pred .section")||$("#tab-pred"); if(!p)return;
 let w=$("#be57Decision"); if(w)w.remove();
 const rec=detectRecommendation(); w=document.createElement("section");w.id="be57Decision";
 const count=readLog().filter(x=>x.type==="prediction_snapshot_v59").length;
 w.innerHTML=`<div class="be57-rec ${rec.cls}"><small>購入判断</small><strong>${esc(rec.label)}</strong><p>${esc(rec.reason)}</p><div class="be57-meta"><span>学習保存 ${count}R</span><span>予想順位はオッズ非依存</span></div></div><div class="be57-note">購入額・現在オッズ・確定払戻は、元データに取得値がある場合だけ表示します。値が無い場合は推測しません。</div>`;
 p.prepend(w);
}
function ensureDetails(){
 const p=$("#tab-pred .section");if(!p||$("#be51Details"))return;
 const w=document.createElement("section");w.id="be51Details";w.innerHTML=`<div class="be51-buttons" role="tablist" aria-label="レース詳細"><button data-d="scenario" aria-expanded="false">展開</button><button data-d="card" aria-expanded="false">選手</button><button data-d="before" aria-expanded="false">直前</button><button data-d="data" aria-expanded="false">データ</button><button data-d="audit" aria-expanded="false">取得状況</button></div><div id="be51Panel" hidden aria-live="polite"></div>`;p.append(w);
 $$('[data-d]',w).forEach(b=>b.onclick=()=>{const panel=$("#be51Panel"),src=$("#tab-"+b.dataset.d),same=b.classList.contains("on")&&!panel.hidden;$$('[data-d]',w).forEach(x=>{x.classList.remove("on");x.setAttribute("aria-expanded","false")});panel.innerHTML="";if(same){panel.hidden=true;return}b.classList.add("on");b.setAttribute("aria-expanded","true");panel.hidden=false;if(src){const c=cleanClone(src);c.classList.add("active","be51-inline");if(b.dataset.d==="audit")$$("*",c).forEach(x=>{if(x.children.length===0&&/監査/.test(x.textContent||""))x.textContent=(x.textContent||"").replace(/監査/g,"取得状況")});panel.append(c)}else panel.innerHTML='<div class="be56-empty">この詳細データは現在ありません</div>';panel.scrollIntoView({behavior:"smooth",block:"nearest"})});
}
function afterRace(){document.body.classList.add("be48-race-active");simplifyChrome();ensureDecision();ensureDetails();snapshot()}
function install(){
 if(typeof renderHome==="function"&&!renderHome.__be57){const o=renderHome;renderHome=function(...a){const r=o.apply(this,a);queueMicrotask(renderSimpleHome);return r};renderHome.__be57=true}
 if(typeof renderRace==="function"&&!renderRace.__be57){const o=renderRace;renderRace=function(...a){const r=o.apply(this,a);queueMicrotask(afterRace);return r};renderRace.__be57=true}
 renderSimpleHome();simplifyChrome();if(st()?.race)afterRace();
}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",install):install();
})();

/* BOAT_EDGE_SITE_V59_RESULTS_LEARNING */
(()=>{"use strict";
const $=(s,r=document)=>r.querySelector(s);
const esc=v=>String(v??"—").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const KEY="boat_edge_v57_learning_log";
const now=()=>new Date().toISOString();
function logs(){try{return JSON.parse(localStorage.getItem(KEY)||"[]")}catch(_){return[]}}
function save(a){try{localStorage.setItem(KEY,JSON.stringify(a.slice(-1000)))}catch(_){}}
function normCombo(v){
 if(Array.isArray(v)) return v.slice(0,3).join("-");
 const m=String(v??"").match(/([1-6])\D+([1-6])\D+([1-6])/);
 return m?`${m[1]}-${m[2]}-${m[3]}`:null;
}
function flattenTickets(pred){
 const out=[], seen=new Set();
 const worlds=[
  ["A",pred?.worldA||pred?.world_a||pred?.pattern_a],
  ["B",pred?.worldB||pred?.world_b||pred?.pattern_b]
 ];
 for(const [world,w] of worlds){
  const arr=w?.tickets||w?.bets||w?.combinations||[];
  for(const t of arr){
   const combo=normCombo(t?.combo||t?.combination||t?.ticket||t?.trifecta||t);
   if(!combo||seen.has(combo))continue;
   seen.add(combo);
   const p=Number(t?.probability??t?.prob??t?.p??t?.rate);
   const stake=Number(t?.amount??t?.stake??t?.yen);
   out.push({combo,world,probability:Number.isFinite(p)?p:null,stake:Number.isFinite(stake)?stake:null});
  }
 }
 // fallback prediction in current index uses worldA/worldB tickets; if unavailable, parse visible ticket text.
 if(!out.length){
   const text=$("#tab-pred")?.innerText||"";
   for(const m of text.matchAll(/([1-6])\s*[-－]\s*([1-6])\s*[-－]\s*([1-6])(?:[^\n%]*?(\d+(?:\.\d+)?)\s*%)?/g)){
     const combo=`${m[1]}-${m[2]}-${m[3]}`; if(seen.has(combo))continue; seen.add(combo);
     out.push({combo,world:null,probability:m[4]?Number(m[4]):null,stake:null});
   }
 }
 out.sort((a,b)=>(b.probability??-1)-(a.probability??-1));
 return out;
}
function currentRace(){
 try{return typeof state!=="undefined"?state.race:null}catch(_){return null}
}
function currentPrediction(race){
 try{return typeof getPrediction==="function"&&race?getPrediction(race):null}catch(_){return null}
}
function ensureStructuredSnapshot(){
 const race=currentRace(); if(!race?.race_key)return null;
 const a=logs(); let snap=a.find(x=>x.type==="prediction_snapshot_v59"&&x.key===race.race_key);
 if(snap)return snap;
 const pred=currentPrediction(race), tickets=flattenTickets(pred);
 snap={type:"prediction_snapshot_v59",key:race.race_key,saved_at:now(),version:"V59",
       model:pred?.model||race?.derived?.model||race?.current_model_input?.model||null,
       tickets:tickets.map((x,i)=>({...x,rank:i+1})),
       decision:pred?.decision||race?.derived?.decision||null};
 a.push(snap); save(a); return snap;
}
async function fetchResult(key){
 if(!key)return null;
 try{
  const r=await fetch(`./data/site_results/${key}.json?t=${Date.now()}`,{cache:"no-store"});
  if(!r.ok)return null;
  const d=await r.json();
  return d?.status==="confirmed"?d:null;
 }catch(_){return null}
}
function evaluation(snap,res){
 const win=normCombo(res?.trifecta||res?.finish_order);
 const tickets=snap?.tickets||[];
 const ix=tickets.findIndex(x=>x.combo===win);
 const hit=ix>=0;
 const ticket=hit?tickets[ix]:null;
 const payout100=Number(res?.trifecta_payout_yen_per_100);
 const stake=Number(ticket?.stake);
 const actualPayout=hit&&Number.isFinite(payout100)&&Number.isFinite(stake)?Math.floor(payout100*(stake/100)):null;
 const totalStake=tickets.reduce((s,x)=>s+(Number.isFinite(Number(x.stake))?Number(x.stake):0),0);
 const profit=actualPayout!==null&&totalStake>0?actualPayout-totalStake:null;
 return {winning_combo:win,winning_rank:hit?ix+1:null,hit,payout100:Number.isFinite(payout100)?payout100:null,
         hit_stake:Number.isFinite(stake)?stake:null,total_stake:totalStake||null,actual_payout:actualPayout,profit};
}
function persistEval(key,ev,res){
 const a=logs(); const i=a.findIndex(x=>x.type==="result_evaluation_v59"&&x.key===key);
 const row={type:"result_evaluation_v59",key,evaluated_at:now(),version:"V59",...ev,result:res};
 if(i>=0)a[i]=row;else a.push(row); save(a);
}
function panel(){
 let p=$("#be59Result");
 if(!p){p=document.createElement("section");p.id="be59Result";const host=$("#tab-pred .section")||$("#tab-pred");host?.prepend(p)}
 return p;
}
function money(v){return v===null||v===undefined?"未取得":`${Number(v).toLocaleString("ja-JP")}円`}
function renderPending(){
 const p=panel(); if(!p)return;
 p.innerHTML=`<div class="be59-card pending"><small>レース結果</small><strong>結果待ち</strong><p>結果公開後、自動で的中判定・払戻・収支を反映します。</p></div>`;
}
function renderResult(ev,res,snap){
 const p=panel();if(!p)return;
 const rank=ev.winning_rank?`${ev.winning_rank}位`:"表示買い目外";
 const cls=ev.hit?"hit":"miss";
 p.innerHTML=`<div class="be59-card ${cls}">
 <div class="be59-top"><div><small>確定結果</small><strong>${esc(ev.winning_combo)}</strong></div><b>${ev.hit?"的中":"不的中"}</b></div>
 <div class="be59-grid">
   <div><span>正解の予測順位</span><strong>${esc(rank)}</strong></div>
   <div><span>3連単払戻（100円）</span><strong>${money(ev.payout100)}</strong></div>
   <div><span>購入額</span><strong>${money(ev.total_stake)}</strong></div>
   <div><span>実払戻</span><strong>${money(ev.actual_payout)}</strong></div>
   <div><span>収支</span><strong>${ev.profit===null?"未計算":`${ev.profit>=0?"+":""}${ev.profit.toLocaleString("ja-JP")}円`}</strong></div>
 </div>
 <p class="be59-note">${ev.hit?"予想時点で保存した買い目と確定結果を照合。":"予想時点の保存内容は変更せず、確定結果だけを後から照合しています。"}</p>
 </div>`;
}
async function run(){
 const race=currentRace(); if(!race?.race_key)return;
 // V60: result first. Never create a new prediction snapshot after result confirmation.
 const res=await fetchResult(race.race_key);
 const a=logs();
 let snap=a.find(x=>x.type==="prediction_snapshot_v59"&&x.key===race.race_key);
 if(res){
   if(!snap){
     const p=panel(); if(p)p.innerHTML=`<div class="be59-card miss"><small>確定結果</small><strong>${esc(normCombo(res?.trifecta||res?.finish_order)||"—")}</strong><p>予想時点スナップショットなし。結果確定後の予想は学習データとして保存しません。</p></div>`;
     return;
   }
   const ev=evaluation(snap,res);persistEval(race.race_key,ev,res);renderResult(ev,res,snap);return;
 }
 snap=ensureStructuredSnapshot();
 renderPending();
}
function hook(){
 if(typeof renderRace==="function"&&!renderRace.__be59){
  const old=renderRace;renderRace=function(...a){const x=old.apply(this,a);queueMicrotask(()=>run());return x};renderRace.__be59=true;
 }
 if(currentRace())run();
 setInterval(()=>{if(document.visibilityState==="visible"&&currentRace())run()},60000);
 document.addEventListener("visibilitychange",()=>{if(document.visibilityState==="visible")run()});
}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",hook):hook();
})();

/* BOAT_EDGE_SITE_V63_DISTRIBUTION_BLOCK */
(()=>{"use strict";
const $=(s,r=document)=>r.querySelector(s);
const esc=v=>String(v??"—").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const getRace=()=>{try{return typeof state!=="undefined"?state.race:null}catch(_){return null}};
const getPred=r=>{try{const f=r?.__formal120||window.__boatEdgeFormal120?.[r?.race_key];if(f?.distribution120)return f;return typeof getPrediction==="function"&&r?getPrediction(r):null}catch(_){return null}};
function combo(v){if(Array.isArray(v))return v.slice(0,3).join("-");const m=String(v??"").match(/([1-6])\D+([1-6])\D+([1-6])/);return m?`${m[1]}-${m[2]}-${m[3]}`:null}
function why(t){const v=t?.reasons??t?.reason??t?.why??t?.explanation??t?.rationale;if(Array.isArray(v))return v.filter(Boolean).join(" / ");if(v&&typeof v==="object")return Object.values(v).filter(Boolean).join(" / ");return v?String(v):"理由データ未生成"}
function rows(p){
 const src=p?.distribution120||p?.distribution_120||p?.all_combinations||p?.allCombinations||p?.trifecta_distribution||p?.probabilities;
 let a=Array.isArray(src)?src:(src&&typeof src==="object"?Object.entries(src).map(([k,v])=>typeof v==="object"?{combo:k,...v}:{combo:k,probability:v}):[]);
 return a.map(t=>({combo:combo(t?.combo||t?.combination||t?.ticket||t?.trifecta||t?.order||t),probability:Number(t?.probability??t?.prob??t?.p??t?.rate),world:t?.world??t?.scenario??t?.pattern??null,reason:why(t)})).filter(x=>x.combo&&Number.isFinite(x.probability)).sort((a,b)=>b.probability-a.probability).map((x,i)=>({...x,rank:i+1}));
}
function render(){
 const r=getRace();if(!r)return;const host=$("#tab-pred .section")||$("#tab-pred");if(!host)return;
 let box=$("#be63Distribution");if(!box){box=document.createElement("section");box.id="be63Distribution";host.append(box)}
 const a=rows(getPred(r));
 if(!a.length){box.innerHTML='<div class="be62-box"><div class="be62-title"><b>全3連単 確率順位</b><span>最大120通り</span></div><p>120通りの確率分布はまだ予想データ側で生成されていません。サイト側では確率を作りません。</p></div>';return}
 const row=x=>`<div class="be62-row"><b>${x.rank}位</b><strong>${esc(x.combo)}</strong><span>${esc(x.probability)}%</span><small>${x.world?`世界 ${esc(x.world)} / `:""}${esc(x.reason)}</small></div>`;
 box.innerHTML=`<div class="be62-box"><div class="be62-title"><b>全3連単 確率順位</b><span>${a.length}/120通り</span></div>${a.slice(0,10).map(row).join("")}${a.length>10?`<details><summary>11位以下を全部見る</summary>${a.slice(10).map(row).join("")}</details>`:""}</div>`;
}
function hook(){if(typeof renderRace==="function"&&!renderRace.__be63){const old=renderRace;renderRace=function(...a){const x=old.apply(this,a);queueMicrotask(render);return x};renderRace.__be63=true}if(getRace())render()}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",hook):hook();
})();

/* BOAT_EDGE_SITE_V64_FORMAL120_BRIDGE */
(()=>{"use strict";
const $=(s,r=document)=>r.querySelector(s);
const KEY="boat_edge_v57_learning_log";
const getRace=()=>{try{return typeof state!=="undefined"?state.race:null}catch(_){return null}};
function logs(){try{return JSON.parse(localStorage.getItem(KEY)||"[]")}catch(_){return[]}}
function save(a){try{localStorage.setItem(KEY,JSON.stringify(a.slice(-1000)))}catch(_){}}
function norm(v){if(Array.isArray(v))return v.slice(0,3).join("-");const m=String(v??"").match(/([1-6])\D+([1-6])\D+([1-6])/);return m?`${m[1]}-${m[2]}-${m[3]}`:null}
function normalize(raw,key){
 const src=raw?.distribution120||raw?.distribution_120||raw?.all_combinations||raw?.trifecta_distribution||raw?.probabilities;
 let a=Array.isArray(src)?src:(src&&typeof src==="object"?Object.entries(src).map(([combo,v])=>typeof v==="object"?{combo,...v}:{combo,probability:v}):[]);
 a=a.map(t=>({combo:norm(t?.combo||t?.combination||t?.ticket||t?.trifecta||t?.order||t),probability:Number(t?.probability??t?.prob??t?.p??t?.rate),world:t?.world??t?.scenario??t?.pattern??null,reasons:t?.reasons??t?.reason??t?.why??t?.explanation??t?.rationale??null})).filter(x=>x.combo&&Number.isFinite(x.probability)).sort((a,b)=>b.probability-a.probability).map((x,i)=>({...x,rank:i+1}));
 if(!a.length)return null;
 return {race_key:raw?.race_key||key,model:raw?.model||raw?.formal_meta?.model||raw?.current||null,generated_at:raw?.generated_at||raw?.updated_at||null,distribution120:a};
}
async function fetchFormal120(key){
 for(const path of [`./data/formal_predictions/${key}.json`,`./data/formal/${key}.json`]){
  try{const r=await fetch(`${path}?t=${Date.now()}`,{cache:"no-store"});if(!r.ok)continue;const n=normalize(await r.json(),key);if(n)return n}catch(_){}
 }
 return null;
}
function attachToPrediction(race,formal){
 if(!race||!formal)return;
 race.__formal120=formal;
 const old=window.__boatEdgeFormal120||{};old[race.race_key]=formal;window.__boatEdgeFormal120=old;
}
function snapshotFormal(formal){
 const key=formal?.race_key;if(!key)return;
 const a=logs();if(a.some(x=>x.type==="prediction_distribution120_v64"&&x.key===key))return;
 a.push({type:"prediction_distribution120_v64",key,saved_at:new Date().toISOString(),model:formal.model,generated_at:formal.generated_at,tickets:formal.distribution120});
 save(a);
}
async function resultExists(key){
 try{const r=await fetch(`./data/site_results/${key}.json?t=${Date.now()}`,{cache:"no-store"});if(!r.ok)return false;return (await r.json())?.status==="confirmed"}catch(_){return false}
}
async function run(){
 const race=getRace();if(!race?.race_key)return;
 const formal=await fetchFormal120(race.race_key);if(!formal)return;
 attachToPrediction(race,formal);
 // PRE_RESULT only: never create the central 120 snapshot after a confirmed result exists.
 if(!(await resultExists(race.race_key)))snapshotFormal(formal);
 window.dispatchEvent(new CustomEvent("boat-edge-formal120",{detail:{race_key:race.race_key,count:formal.distribution120.length}}));
}
function hook(){
 if(typeof renderRace==="function"&&!renderRace.__be64){const old=renderRace;renderRace=function(...a){const x=old.apply(this,a);queueMicrotask(run);return x};renderRace.__be64=true}
 if(getRace())run();
 document.addEventListener("visibilitychange",()=>{if(document.visibilityState==="visible")run()});
}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",hook):hook();
})();/* BOAT_EDGE_SITE_V64_RERENDER_SIGNAL */
window.addEventListener("boat-edge-formal120",()=>{try{if(typeof renderRace==="function"&&typeof state!=="undefined"&&state.race)renderRace(state.race)}catch(_){}});

/* BOAT_EDGE_SITE_V65_120_RESULT_SCORING */
(()=>{"use strict";
const KEY="boat_edge_v57_learning_log";
const getRace=()=>{try{return typeof state!=="undefined"?state.race:null}catch(_){return null}};
function logs(){try{return JSON.parse(localStorage.getItem(KEY)||"[]")}catch(_){return[]}}
function save(a){try{localStorage.setItem(KEY,JSON.stringify(a.slice(-1200)))}catch(_){}}
function norm(v){if(Array.isArray(v))return v.slice(0,3).join("-");const m=String(v??"").match(/([1-6])\D+([1-6])\D+([1-6])/);return m?`${m[1]}-${m[2]}-${m[3]}`:null}
async function result(key){
 try{const r=await fetch(`./data/site_results/${key}.json?t=${Date.now()}`,{cache:"no-store"});if(!r.ok)return null;const d=await r.json();return d?.status==="confirmed"?d:null}catch(_){return null}
}
function classify(rank){
 if(!Number.isFinite(rank))return "distribution_missing";
 if(rank<=10)return "top10";
 if(rank<=30)return "rank11_30";
 if(rank<=60)return "rank31_60";
 return "rank61_120";
}
function score(snap,res){
 const win=norm(res?.trifecta||res?.finish_order);
 const ts=Array.isArray(snap?.tickets)?snap.tickets:[];
 const hit=ts.find(x=>norm(x?.combo)===win)||null;
 const rank=hit?Number(hit.rank)||ts.indexOf(hit)+1:null;
 const probability=hit&&Number.isFinite(Number(hit.probability))?Number(hit.probability):null;
 return {
  winning_combo:win,
  winning_rank:Number.isFinite(rank)?rank:null,
  winning_probability:probability,
  winning_world:hit?.world??null,
  winning_reasons:hit?.reasons??null,
  rank_bucket:classify(rank),
  distribution_count:ts.length,
  model:snap?.model??null,
  snapshot_saved_at:snap?.saved_at??null,
  result_fetched_at:res?.fetched_at??null,
  payout100:Number.isFinite(Number(res?.trifecta_payout_yen_per_100))?Number(res.trifecta_payout_yen_per_100):null
 };
}
function persist(key,row,res){
 const a=logs(),i=a.findIndex(x=>x.type==="distribution120_result_v65"&&x.key===key);
 const v={type:"distribution120_result_v65",key,evaluated_at:new Date().toISOString(),version:"V65",...row,result:res};
 if(i>=0)a[i]=v;else a.push(v);save(a);
}
function render(row){
 const host=document.querySelector("#be59Result .be59-card");if(!host)return;
 let el=document.querySelector("#be65RankAudit");
 if(!el){el=document.createElement("p");el.id="be65RankAudit";el.className="be59-note";host.append(el)}
 const rank=row.winning_rank?`${row.winning_rank}位 / ${row.distribution_count}通り`:"120通りスナップ未取得";
 const prob=row.winning_probability===null?"未取得":`${row.winning_probability}%`;
 el.textContent=`全確率分布での正解順位: ${rank} / 予測確率: ${prob}${row.winning_world?` / 世界 ${row.winning_world}`:""}`;
}
async function run(){
 const race=getRace();if(!race?.race_key)return;
 const res=await result(race.race_key);if(!res)return;
 const a=logs();
 const snap=a.find(x=>x.type==="prediction_distribution120_v64"&&x.key===race.race_key);
 if(!snap)return; // never rebuild a pre-result snapshot after result.
 const row=score(snap,res);persist(race.race_key,row,res);render(row);
}
function hook(){
 window.addEventListener("boat-edge-formal120",()=>run());
 if(typeof renderRace==="function"&&!renderRace.__be65){const old=renderRace;renderRace=function(...a){const x=old.apply(this,a);queueMicrotask(run);return x};renderRace.__be65=true}
 if(getRace())run();
 setInterval(()=>{if(document.visibilityState==="visible")run()},60000);
}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",hook):hook();
})();

/* BOAT_EDGE_SITE_V70_BATCH_LEARNING_PURCHASE */
(()=>{"use strict";
const KEY="boat_edge_v57_learning_log", CFG="boat_edge_v70_purchase_cfg";
const $=(q,r=document)=>r.querySelector(q);
const race=()=>{try{return typeof state!=="undefined"?state.race:null}catch(_){return null}};
const norm=v=>{if(Array.isArray(v))return v.slice(0,3).join("-");const m=String(v??"").match(/([1-6])\D+([1-6])\D+([1-6])/);return m?`${m[1]}-${m[2]}-${m[3]}`:null};
const logs=()=>{try{return JSON.parse(localStorage.getItem(KEY)||"[]")}catch(_){return[]}};
const saveLogs=a=>{try{localStorage.setItem(KEY,JSON.stringify(a.slice(-1600)))}catch(_){}};
const cfg=()=>{try{return {...{budget:5000,cutoff:10},...JSON.parse(localStorage.getItem(CFG)||"{}")}}catch(_){return {budget:5000,cutoff:10}}};
const saveCfg=v=>{try{localStorage.setItem(CFG,JSON.stringify(v))}catch(_){}};
function dist(r){const d=r?.__formal120||window.__boatEdgeFormal120?.[r?.race_key];return Array.isArray(d?.distribution120)?d.distribution120:[]}
async function getJSON(url){try{const x=await fetch(url+(url.includes("?")?"&":"?")+"t="+Date.now(),{cache:"no-store"});return x.ok?await x.json():null}catch(_){return null}}
async function result(key){const d=await getJSON(`./data/site_results/${key}.json`);return d?.status==="confirmed"?d:null}
function oddsMap(raw){
 const src=raw?.trifecta_odds||raw?.odds||raw?.odds3t||raw?.data||raw;
 const out={};
 if(Array.isArray(src)){for(const x of src){const c=norm(x?.combo||x?.trifecta||x?.order),o=Number(x?.odds??x?.value??x?.rate);if(c&&o>0)out[c]=o}}
 else if(src&&typeof src==="object"){for(const [k,v] of Object.entries(src)){const c=norm(k),o=Number(typeof v==="object"?(v.odds??v.value??v.rate):v);if(c&&o>0)out[c]=o}}
 return out;
}
async function loadOdds(r){const x=await getJSON(`./data/site_odds/${r.race_key}.json`);return {...oddsMap(r?.odds),...oddsMap(x)}}
function unitsAlloc(rows,budget,weightFn){
 const units=Math.max(1,Math.floor(Number(budget||5000)/100)), ws=rows.map((x,i)=>Math.max(0,Number(weightFn(x,i))||0));
 let sum=ws.reduce((a,b)=>a+b,0); if(!sum){ws.fill(1);sum=ws.length}
 const raw=ws.map(w=>units*w/sum), base=raw.map(Math.floor), left=units-base.reduce((a,b)=>a+b,0);
 [...raw.keys()].sort((a,b)=>(raw[b]-base[b])-(raw[a]-base[a])).slice(0,left).forEach(i=>base[i]++);
 return rows.map((x,i)=>({...x,stake:base[i]*100}));
}
function strategyRows(rows,budget,odds){
 const eq=unitsAlloc(rows,budget,()=>1), pp=unitsAlloc(rows,budget,x=>x.probability);
 const allOdds=rows.length&&rows.every(x=>Number(odds[x.combo])>0);
 const du=allOdds?unitsAlloc(rows,budget,x=>1/Number(odds[x.combo])):null;
 return [{id:"equal",label:"均等",rows:eq},{id:"prob",label:"確率比例",rows:pp},{id:"dutch",label:"払戻均等化",rows:du}];
}
function stats(st,odds){
 if(!st.rows)return null; let ev=0,min=null,max=null,have=0;
 for(const x of st.rows){const o=Number(odds[x.combo]);if(o>0){have++;const gross=x.stake*o;ev+=(Number(x.probability)||0)/100*gross;min=min===null?gross:Math.min(min,gross);max=max===null?gross:Math.max(max,gross)}}
 return {stake:st.rows.reduce((a,x)=>a+x.stake,0),ev:have===st.rows.length?Math.round(ev):null,min:have===st.rows.length?Math.round(min):null,max:have===st.rows.length?Math.round(max):null};
}
function yen(v){return v==null?"—":Number(v).toLocaleString("ja-JP")+"円"}
async function persistPlan(r,selected,strategies,odds,c){
 if(await result(r.race_key))return;
 const a=logs(),i=a.findIndex(x=>x.type==="purchase_plan_v70"&&x.key===r.race_key);
 const row={type:"purchase_plan_v70",key:r.race_key,saved_at:new Date().toISOString(),budget:c.budget,cutoff:c.cutoff,odds,coverage:selected.reduce((z,x)=>z+(Number(x.probability)||0),0),strategies:strategies.filter(x=>x.rows).map(x=>({id:x.id,label:x.label,rows:x.rows}))};
 if(i>=0)return; a.push(row);saveLogs(a);
}
async function settlePlan(r){
 const res=await result(r.race_key);if(!res)return;const a=logs(),plan=a.find(x=>x.type==="purchase_plan_v70"&&x.key===r.race_key);if(!plan)return;
 if(a.some(x=>x.type==="purchase_result_v70"&&x.key===r.race_key))return;
 const win=norm(res.trifecta||res.finish_order),pay=Number(res.trifecta_payout_yen_per_100);
 const outcomes=(plan.strategies||[]).map(s=>{const t=(s.rows||[]).find(x=>x.combo===win),stake=(s.rows||[]).reduce((z,x)=>z+(Number(x.stake)||0),0),gross=t&&pay>0?Math.floor(pay*(Number(t.stake)||0)/100):0;return {id:s.id,label:s.label,winning_stake:t?.stake||0,total_stake:stake,payout:gross,profit:gross-stake}});
 a.push({type:"purchase_result_v70",key:r.race_key,evaluated_at:new Date().toISOString(),winning_combo:win,payout100:pay||null,outcomes});saveLogs(a);
}
async function learningSummary(){
 const remote=await getJSON("./data/site_learning/summary.json"); if(remote?.evaluated!=null)return remote;
 const a=logs().filter(x=>x.type==="distribution120_result_v65"&&Number.isFinite(Number(x.winning_rank))),ranks=a.map(x=>Number(x.winning_rank));
 const n=ranks.length,rate=k=>n?Math.round(1000*ranks.filter(x=>x<=k).length/n)/10:null;
 return {evaluated:n,top10_rate:rate(10),top30_rate:rate(30),top60_rate:rate(60),avg_rank:n?Math.round(10*ranks.reduce((x,y)=>x+y,0)/n)/10:null,source:"browser"};
}
function ensureHost(){
 const h=$("#tab-pred .section")||$("#tab-pred");if(!h)return null;let x=$("#be70Lab");if(!x){x=document.createElement("section");x.id="be70Lab";h.append(x)}return x;
}
async function render(){
 const r=race(),host=ensureHost();if(!r||!host)return;const d=dist(r),c=cfg(),sum=await learningSummary();
 if(!d.length){host.innerHTML='<div class="be62-box"><div class="be62-title"><b>購入戦略・学習分析</b></div><p>正式120通り分布を待っています。確率はサイト側で作りません。</p></div>';return}
 const cutoff=Math.min(d.length,Math.max(1,Number(c.cutoff)||10)),selected=d.slice(0,cutoff),od=await loadOdds(r),strategies=strategyRows(selected,c.budget,od),ss=strategies.map(x=>({...x,stat:stats(x,od)}));
 const coverage=selected.reduce((z,x)=>z+(Number(x.probability)||0),0);
 const valid=ss.filter(x=>x.stat?.ev!=null).sort((a,b)=>b.stat.ev-a.stat.ev),best=valid[0]||null;
 const rec=best?`AI推奨（購入比較）: ${best.label}`:"AI推奨: オッズ待ち";
 const opts=[3,5,10,20,30,60,120].map(n=>`<option value="${n}" ${n===cutoff?"selected":""}>上位${n}点</option>`).join("");
 const srow=x=>`<div class="be62-row"><b>${x.label}</b><strong>投資 ${yen(x.stat?.stake)}</strong><span>${x.stat?.ev==null?"EV未計算":"期待払戻 "+yen(x.stat.ev)}</span><small>${x.stat?.min==null?"現在オッズ未取得":"想定払戻幅 "+yen(x.stat.min)+"〜"+yen(x.stat.max)}</small></div>`;
 host.innerHTML=`<div class="be62-box">
 <div class="be62-title"><b>購入戦略・学習分析</b><span>予想順位は確率のみ</span></div>
 <div style="display:flex;gap:8px;flex-wrap:wrap;margin:10px 0"><label>予算 <input id="be70Budget" type="number" min="100" step="100" value="${c.budget}" style="width:100px">円</label><label>候補 <select id="be70Cutoff">${opts}</select></label></div>
 <p><b>${rec}</b><br>選択範囲の確率合計 ${coverage.toFixed(2)}% ／ オッズは購入判断だけに使用します。</p>
 ${ss.map(srow).join("")}
 <details><summary>学習成績を見る</summary><div class="be59-grid"><div><span>採点済み</span><strong>${sum.evaluated||0}R</strong></div><div><span>正解TOP10</span><strong>${sum.top10_rate==null?"—":sum.top10_rate+"%"}</strong></div><div><span>正解TOP30</span><strong>${sum.top30_rate==null?"—":sum.top30_rate+"%"}</strong></div><div><span>正解TOP60</span><strong>${sum.top60_rate==null?"—":sum.top60_rate+"%"}</strong></div><div><span>平均正解順位</span><strong>${sum.avg_rank??"—"}</strong></div></div></details>
 </div>`;
 $("#be70Budget")?.addEventListener("change",e=>{saveCfg({budget:Math.max(100,Math.floor(Number(e.target.value||5000)/100)*100),cutoff:Number($("#be70Cutoff")?.value||cutoff)});render()});
 $("#be70Cutoff")?.addEventListener("change",e=>{saveCfg({budget:Number($("#be70Budget")?.value||5000),cutoff:Number(e.target.value)});render()});
 await persistPlan(r,selected,strategies,od,{budget:Number(c.budget),cutoff}); await settlePlan(r);
}
function hook(){
 window.addEventListener("boat-edge-formal120",()=>render());
 if(typeof renderRace==="function"&&!renderRace.__be70){const old=renderRace;renderRace=function(...a){const x=old.apply(this,a);queueMicrotask(render);return x};renderRace.__be70=true}
 if(race())render();setInterval(()=>{if(document.visibilityState==="visible"&&race())render()},60000);
}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",hook):hook();
})();

/* BOAT_EDGE_SITE_V73_SELF_HEALING_HOME */
(()=>{"use strict";
window.BOAT_EDGE_SITE_VERSION="V73";
const $=(q,r=document)=>r.querySelector(q);
const esc=v=>String(v??"—").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
let lastTodayError=null,lastTodayOK=null,busy=false;

function getState(){try{return typeof state!=="undefined"?state:null}catch(_){return null}}
function venueName(v){return v?.venue||v?.name||v?.jcd||"開催場"}
function mins(dl){
 const m=/^(\d{1,2}):(\d{2})/.exec(String(dl||""));if(!m)return null;
 const n=new Date(),t=new Date(n);t.setHours(+m[1],+m[2],0,0);return Math.floor((t-n)/60000);
}
async function getJSON(url){
 try{
  const r=await fetch(url+(url.includes("?")?"&":"?")+"t="+Date.now(),{cache:"no-store"});
  if(!r.ok)throw new Error("HTTP "+r.status);
  return await r.json();
 }catch(e){throw e}
}
function ensureStatus(){
 let x=$("#be73Status");if(x)return x;
 x=document.createElement("section");x.id="be73Status";
 x.style.cssText="margin:10px 18px;padding:10px 12px;border:1px solid #dbe6f4;border-radius:12px;background:#fff;font-size:12px;line-height:1.5";
 const h=$("#be51Home")||$("#homeView")||document.body;
 h.prepend(x);return x;
}
function renderStatus(today,health){
 const x=ensureStatus();
 const venues=(today?.venues||[]).length;
 const odds=health?.odds||{},learn=health?.learning||{},res=health?.results||{};
 const ok=!!today;
 x.innerHTML=`<div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap">
 <b>BOAT EDGE V73 ● ${ok?"データ接続":"再接続中"}</b><span>${lastTodayOK||"—"}</span></div>
 <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:5px">
 <span>開催 ${venues}場</span>
 <span>オッズ ${odds.updated||0}R</span>
 <span>結果 ${res.updated||0}R</span>
 <span>学習 ${learn.evaluated||0}R</span>
 ${lastTodayError?`<span style="color:#b54708">再取得: ${esc(lastTodayError)}</span>`:""}
 </div>`;
}
function renderFallback(today){
 let a=$("#be51Home");
 if(!a){const home=$("#homeView");if(!home)return;a=document.createElement("div");a.id="be51Home";home.prepend(a)}
 const vs=(today?.venues||[]).filter(v=>(v.races||[]).length);
 let sel=a.dataset.venue;if(!vs.some(v=>String(v.jcd)===sel))sel=String(vs[0]?.jcd||"");a.dataset.venue=sel;
 const v=vs.find(x=>String(x.jcd)===sel),rs=(v?.races||[]).filter(r=>{const m=mins(r.deadline);return m==null||m>=0});
 a.innerHTML=`<section class="be51-head"><div><small>BOAT EDGE</small><h1>今日のレース</h1></div>
 <div class="be57-headright"><span>${today?.updated_at?"更新済み":"読込中"}</span><button id="be73Refresh" type="button">↻ 更新</button></div></section>
 <section class="be51-venues">${vs.map(x=>`<button data-v="${esc(x.jcd)}" class="${String(x.jcd)===sel?"on":""}">${esc(venueName(x))}</button>`).join("")||'<div class="be51-empty">開催データを再取得中</div>'}</section>
 <section class="be51-box"><div class="be51-title"><b>${esc(venueName(v))}</b><span>レースを選択</span></div>
 <div class="be51-grid">${rs.map(r=>{const m=mins(r.deadline);return `<button class="be51-race" data-file="${esc(r.file)}" data-jcd="${esc(v?.jcd)}"><b>${esc(r.race_no)}R</b><strong>${esc(r.deadline)}</strong><small>${m==null?"":m===0?"締切間近":m>0?`あと${m}分`:"締切済"}</small></button>`}).join("")||'<div class="be51-empty">表示できるレースがありません</div>'}</div></section>`;
 $('[id="be73Refresh"]',a)?.addEventListener("click",()=>bootstrap(true));
 a.querySelectorAll("[data-v]").forEach(b=>b.addEventListener("click",()=>{a.dataset.venue=b.dataset.v;renderFallback(today);renderStatus(today,window.__be73Health||null)}));
 a.querySelectorAll("[data-file]").forEach(b=>b.addEventListener("click",()=>{try{if(typeof loadRace==="function")loadRace(b.dataset.file,b.dataset.jcd)}catch(_){}}));
}
async function bootstrap(force=false){
 if(busy&&!force)return;busy=true;
 let today=null,health=null;
 try{
  today=await getJSON("./data/today.json");
  lastTodayOK=new Date().toLocaleTimeString("ja-JP",{hour:"2-digit",minute:"2-digit"});
  lastTodayError=null;
  const st=getState();if(st)st.today=today;
 }catch(e){lastTodayError=e?.message||String(e);today=getState()?.today||null}
 try{health=await getJSON("./data/site_health.json")}catch(_){health=null}
 window.__be73Health=health;
 if(today){
  try{if(typeof renderHome==="function")renderHome()}catch(_){}
  // Always render an independent fallback after the legacy renderer.
  renderFallback(today);
 }
 renderStatus(today,health);
 busy=false;
}
function hardenLegacy(){
 try{
  if(typeof renderHome==="function"&&!renderHome.__be73safe){
    const old=renderHome;
    renderHome=function(...a){
      let y;try{y=old.apply(this,a)}catch(e){lastTodayError="旧表示エラー";console.warn("BOAT EDGE legacy renderHome error",e)}
      queueMicrotask(()=>{const t=getState()?.today;if(t){renderFallback(t);renderStatus(t,window.__be73Health||null)}});return y;
    };renderHome.__be73safe=true;
  }
 }catch(_){}
}
function hook(){
 hardenLegacy();
 bootstrap();
 setTimeout(()=>bootstrap(),3000);
 setInterval(()=>{if(document.visibilityState==="visible")bootstrap()},30000);
 document.addEventListener("visibilitychange",()=>{if(document.visibilityState==="visible")bootstrap(true)});
}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",hook):hook();
})();

/* BOAT_EDGE_SITE_V74_DEADLINE_SPOTLIGHT */
(()=>{"use strict";
window.BOAT_EDGE_SITE_VERSION="V74";
const $=(q,r=document)=>r.querySelector(q);
const esc=v=>String(v??"—").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
let recCache={at:0,key:null,row:null,busy:false};

function st(){try{return typeof state!=="undefined"?state:null}catch(_){return null}}
function mins(dl){
 const m=/^(\d{1,2}):(\d{2})/.exec(String(dl||""));if(!m)return null;
 const n=new Date(),t=new Date(n);t.setHours(+m[1],+m[2],0,0);
 return Math.floor((t-n)/60000);
}
function allUpcoming(today){
 const out=[];
 for(const v of (today?.venues||[])){
  for(const r of (v.races||[])){
   const m=mins(r.deadline);
   if(m===null||m<0)continue;
   out.push({...r,jcd:v.jcd,venue:v.venue||v.name||v.jcd,event:v.event||"",mins:m});
  }
 }
 return out.sort((a,b)=>a.mins-b.mins || String(a.jcd).localeCompare(String(b.jcd)) || Number(a.race_no)-Number(b.race_no));
}
function ensure(){
 let box=$("#be74Priority");if(box)return box;
 box=document.createElement("section");box.id="be74Priority";
 box.style.cssText="margin:12px 18px 16px";
 const home=$("#homeView")||document.body;
 const ref=$("#be51Home",home);
 if(ref)home.insertBefore(box,ref);else home.prepend(box);
 return box;
}
function raceButton(r,extra=""){
 return `<button class="be74-race" data-file="${esc(r.file)}" data-jcd="${esc(r.jcd)}" style="border:1px solid #d9e5f3;border-radius:12px;background:#fff;padding:10px;text-align:left;min-width:0">
 <div style="display:flex;justify-content:space-between;gap:8px"><b>${esc(r.venue)} ${esc(r.race_no)}R</b><strong>${esc(r.deadline)}</strong></div>
 <div style="font-size:12px;color:#60738c;margin-top:4px">${r.mins===0?"締切間近":`あと${r.mins}分`}${extra?` / ${extra}`:""}</div>
 </button>`;
}
function bind(root){
 root.querySelectorAll("[data-file]").forEach(b=>b.onclick=()=>{try{if(typeof loadRace==="function")loadRace(b.dataset.file,b.dataset.jcd)}catch(_){}});
}
function pct(v){
 const n=Number(v);if(!Number.isFinite(n))return null;
 return n<=1?n*100:n;
}
function topTicket(pred){
 const rows=[];
 for(const w of (pred?.worlds||[]))for(const t of (w?.tickets||[])){
  const p=pct(t?.probability);
  if(Number.isFinite(p))rows.push({combo:t.combo,probability:p,world:w.key});
 }
 rows.sort((a,b)=>b.probability-a.probability);return rows[0]||null;
}
function completeness(race){
 let n=0,total=4;
 if((race?.beforeinfo?.racers||[]).length)n++;
 if((race?.beforeinfo?.start_exhibition||[]).length)n++;
 if((race?.actual_entry||[]).length)n++;
 if((race?.original_exhibition?.boats||[]).length)n++;
 return n/total;
}
async function fetchRace(row){
 try{
  const r=await fetch(`${row.file}?t=${Date.now()}`,{cache:"no-store"});if(!r.ok)return null;
  let d=await r.json();
  try{
   if(typeof loadFormalOverlay==="function"&&typeof mergeFormalOverlay==="function"){
    const o=await loadFormalOverlay(d.race_key);d=mergeFormalOverlay(d,o);
   }
  }catch(_){}
  return d;
 }catch(_){return null}
}
async function assess(row){
 const d=await fetchRace(row);if(!d)return null;
 let pred=null;try{pred=typeof getPrediction==="function"?getPrediction(d):null}catch(_){}
 if(!pred)return null;
 const t=topTicket(pred),comp=completeness(d),decision=String(pred.decision||"");
 if(!t)return null;
 const formal=pred.mode==="formal";
 const grade=String(pred.grade||"");
 const gradeBonus=/A\+|S/.test(grade)?8:/^A/.test(grade)?5:/^B\+/.test(grade)?3:0;
 const score=t.probability + comp*20 + (formal?8:0) + gradeBonus;
 const eligible=t.probability>=10 && comp>=0.5 && !/見送り|慎重|SKIP/i.test(decision);
 return {...row,pred,top:t,comp,score,eligible,formal,grade,decision};
}
async function chooseRecommendation(today){
 const now=Date.now(),key=String(today?.updated_at||"");
 if(recCache.row && recCache.key===key && now-recCache.at<120000)return recCache.row;
 if(recCache.busy)return recCache.row;
 recCache.busy=true;
 const candidates=allUpcoming(today).filter(r=>r.mins<=180).slice(0,18);
 const out=[];
 for(let i=0;i<candidates.length;i+=4){
  const batch=await Promise.all(candidates.slice(i,i+4).map(assess));
  out.push(...batch.filter(Boolean));
 }
 const eligible=out.filter(x=>x.eligible).sort((a,b)=>b.score-a.score || a.mins-b.mins);
 const row=eligible[0]||null;
 recCache={at:Date.now(),key,row,busy:false};return row;
}
function recHTML(r){
 if(!r)return `<div style="padding:13px;border:1px solid #dce6f2;border-radius:14px;background:#fff"><div style="font-size:12px;font-weight:800;color:#3172c9">一押しレース</div><b style="display:block;margin-top:4px">現時点なし</b><div style="font-size:12px;color:#60738c;margin-top:3px">直前データと確率の集中が条件を満たした時だけ表示します。</div></div>`;
 return `<button data-file="${esc(r.file)}" data-jcd="${esc(r.jcd)}" style="width:100%;padding:14px;border:1px solid #bad8fb;border-radius:14px;background:linear-gradient(135deg,#fff,#eef7ff);text-align:left">
 <div style="display:flex;justify-content:space-between;gap:8px;align-items:center"><span style="font-size:12px;font-weight:900;color:#176bd6">★ 一押しレース</span><span style="font-size:12px">${r.formal?"正式":"暫定"}</span></div>
 <div style="display:flex;justify-content:space-between;gap:10px;margin-top:5px"><b style="font-size:18px">${esc(r.venue)} ${esc(r.race_no)}R</b><strong>${esc(r.deadline)} / あと${r.mins}分</strong></div>
 <div style="font-size:12px;color:#50657f;margin-top:5px">1位候補 ${esc(r.top.combo)} ${r.top.probability.toFixed(1)}% / 勝負度 ${esc(r.grade||"—")} / 直前充足 ${Math.round(r.comp*100)}%</div>
 </button>`;
}
async function render(){
 const today=st()?.today;if(!today)return;
 const box=ensure(),rows=allUpcoming(today);
 const first=rows.slice(0,12),rest=rows.slice(12);
 box.innerHTML=`<div id="be74Rec">${recHTML(recCache.row)}</div>
 <div style="margin-top:12px;border:1px solid #dce6f2;border-radius:14px;background:#f8fbff;padding:12px">
  <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:8px"><b style="font-size:16px">締切順</b><span style="font-size:12px;color:#60738c">全開催場を横断</span></div>
  <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px">${first.map(r=>raceButton(r)).join("")||'<div style="grid-column:1/-1">表示できるレースがありません</div>'}</div>
  ${rest.length?`<details style="margin-top:9px"><summary>この後のレースも見る（${rest.length}R）</summary><div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:8px">${rest.map(r=>raceButton(r)).join("")}</div></details>`:""}
 </div>`;
 bind(box);
 const rec=await chooseRecommendation(today);
 const h=$("#be74Rec",box);if(h){h.innerHTML=recHTML(rec);bind(h)}
}
function hook(){
 if(typeof renderHome==="function"&&!renderHome.__be74){
  const old=renderHome;renderHome=function(...a){let y;try{y=old.apply(this,a)}catch(e){throw e}queueMicrotask(render);return y};renderHome.__be74=true;
 }
 render();
 setInterval(()=>{if(document.visibilityState==="visible")render()},60000);
 document.addEventListener("visibilitychange",()=>{if(document.visibilityState==="visible")render()});
}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",hook):hook();
})();

/* BOAT_EDGE_SITE_V76_PERSISTENT_PRIORITY */
(()=>{"use strict";
window.BOAT_EDGE_SITE_VERSION="V76";
const $=(q,r=document)=>r.querySelector(q);
const esc=v=>String(v??"—").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
let rendering=false,lastKey="",recCache={key:"",row:null,at:0};

function st(){try{return typeof state!=="undefined"?state:null}catch(_){return null}}
function mins(dl){
 const m=/^(\d{1,2}):(\d{2})/.exec(String(dl||""));if(!m)return null;
 const n=new Date(),t=new Date(n);t.setHours(+m[1],+m[2],0,0);
 return Math.floor((t-n)/60000);
}
function upcoming(today){
 const rows=[];
 for(const v of (today?.venues||[]))for(const r of (v.races||[])){
   const m=mins(r.deadline); if(m===null||m<0)continue;
   rows.push({...r,jcd:v.jcd,venue:v.venue||v.name||v.jcd,event:v.event||"",mins:m});
 }
 return rows.sort((a,b)=>a.mins-b.mins || Number(a.race_no)-Number(b.race_no));
}
function attachHost(){
 const home=$("#be51Home"); if(!home)return null;
 let box=$("#be76Priority",home);
 if(!box){
   box=document.createElement("section"); box.id="be76Priority";
   const head=$(".be51-head",home);
   if(head?.nextSibling)home.insertBefore(box,head.nextSibling); else home.prepend(box);
 }
 return box;
}
function bind(root){
 root.querySelectorAll("[data-file]").forEach(b=>b.onclick=()=>{try{if(typeof loadRace==="function")loadRace(b.dataset.file,b.dataset.jcd)}catch(_){}});
}
function raceCard(r){
 return `<button data-file="${esc(r.file)}" data-jcd="${esc(r.jcd)}" style="width:100%;border:1px solid #dce7f5;border-radius:12px;background:#fff;padding:9px 10px;text-align:left">
 <div style="display:flex;justify-content:space-between;gap:8px;align-items:center">
 <b style="font-size:14px">${esc(r.venue)} ${esc(r.race_no)}R</b><strong style="font-size:14px;color:#176bd6">${esc(r.deadline)}</strong></div>
 <div style="font-size:11px;color:#6b7f97;margin-top:3px">${r.mins===0?"締切間近":`あと${r.mins}分`}</div></button>`;
}
function pval(v){const n=Number(v);if(!Number.isFinite(n))return null;return n<=1?n*100:n}
function top(pred){
 const a=[];
 for(const w of (pred?.worlds||[]))for(const t of (w?.tickets||[])){
   const p=pval(t?.probability);if(Number.isFinite(p))a.push({combo:t.combo,p,world:w.key});
 }
 a.sort((x,y)=>y.p-x.p);return a[0]||null;
}
function complete(d){
 let n=0;
 if((d?.beforeinfo?.racers||[]).length)n++;
 if((d?.beforeinfo?.start_exhibition||[]).length)n++;
 if((d?.actual_entry||[]).length)n++;
 if((d?.original_exhibition?.boats||[]).length)n++;
 return n/4;
}
async function fetchRace(row){
 try{
  const r=await fetch(`${row.file}?t=${Date.now()}`,{cache:"no-store"});if(!r.ok)return null;
  let d=await r.json();
  try{
    if(typeof loadFormalOverlay==="function"&&typeof mergeFormalOverlay==="function"){
      d=mergeFormalOverlay(d,await loadFormalOverlay(d.race_key));
    }
  }catch(_){}
  return d;
 }catch(_){return null}
}
async function recommend(today){
 const key=String(today?.updated_at||"");
 if(recCache.key===key&&Date.now()-recCache.at<120000)return recCache.row;
 const cand=upcoming(today).filter(x=>x.mins<=180).slice(0,12), scored=[];
 for(let i=0;i<cand.length;i+=3){
   const batch=await Promise.all(cand.slice(i,i+3).map(async row=>{
     const d=await fetchRace(row);if(!d)return null;
     let pred=null;try{pred=typeof getPrediction==="function"?getPrediction(d):null}catch(_){}
     if(!pred)return null;
     const t=top(pred),c=complete(d),decision=String(pred.decision||""),grade=String(pred.grade||"");
     if(!t)return null;
     const eligible=t.p>=10&&c>=0.5&&!/見送り|慎重|SKIP/i.test(decision);
     const score=t.p+c*20+(pred.mode==="formal"?8:0)+(/^A|S/.test(grade)?5:0);
     return {...row,t,c,decision,grade,formal:pred.mode==="formal",eligible,score};
   }));
   scored.push(...batch.filter(Boolean));
 }
 const row=scored.filter(x=>x.eligible).sort((a,b)=>b.score-a.score||a.mins-b.mins)[0]||null;
 recCache={key,row,at:Date.now()};return row;
}
function recommendationHTML(r){
 if(!r)return `<div style="padding:11px 12px;border:1px solid #dce7f5;border-radius:13px;background:#fff">
 <div style="font-size:11px;font-weight:900;color:#176bd6">★ 一押しレース</div>
 <b style="display:block;margin-top:3px">現時点なし</b>
 <div style="font-size:11px;color:#6b7f97;margin-top:3px">条件が揃った時だけ表示</div></div>`;
 return `<button data-file="${esc(r.file)}" data-jcd="${esc(r.jcd)}" style="width:100%;padding:12px;border:1px solid #b9d7fb;border-radius:13px;background:linear-gradient(135deg,#fff,#eef7ff);text-align:left">
 <div style="display:flex;justify-content:space-between"><span style="font-size:11px;font-weight:900;color:#176bd6">★ 一押しレース</span><span style="font-size:11px">${r.formal?"正式":"暫定"}</span></div>
 <div style="display:flex;justify-content:space-between;gap:8px;margin-top:4px"><b>${esc(r.venue)} ${esc(r.race_no)}R</b><strong>${esc(r.deadline)} / あと${r.mins}分</strong></div>
 <div style="font-size:11px;color:#5d728c;margin-top:4px">1位候補 ${esc(r.t.combo)} ${r.t.p.toFixed(1)}% / 勝負度 ${esc(r.grade||"—")} / 直前 ${Math.round(r.c*100)}%</div></button>`;
}
async function render(force=false){
 if(rendering)return; rendering=true;
 try{
  const today=st()?.today;if(!today)return;
  const host=attachHost();if(!host)return;
  const rows=upcoming(today),key=(today.updated_at||"")+"|"+rows[0]?.race_key+"|"+rows.length;
  if(force||host.dataset.key!==key){
    host.dataset.key=key;
    const first=rows.slice(0,8),rest=rows.slice(8);
    host.innerHTML=`<div id="be76Rec">${recommendationHTML(recCache.row)}</div>
    <div style="margin-top:10px;padding:11px;border:1px solid #dce7f5;border-radius:13px;background:#f8fbff">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:7px"><b>締切順</b><span style="font-size:11px;color:#6b7f97">全12場横断</span></div>
      <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px">${first.map(raceCard).join("")}</div>
      ${rest.length?`<details style="margin-top:7px"><summary style="font-size:12px">この後も見る（${rest.length}R）</summary><div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;margin-top:7px">${rest.map(raceCard).join("")}</div></details>`:""}
    </div>`;
    bind(host);
  }
  const rec=await recommend(today),recHost=$("#be76Rec",host);
  if(recHost){recHost.innerHTML=recommendationHTML(rec);bind(recHost)}
  const status=$("#be73Status");
  if(status)status.innerHTML=status.innerHTML.replace(/BOAT EDGE V73/g,"BOAT EDGE V76").replace(/BOAT EDGE V74/g,"BOAT EDGE V76");
 }finally{rendering=false}
}
function observe(){
 const root=$("#homeView")||document.body;
 const mo=new MutationObserver(()=>{if(!$("#be76Priority"))queueMicrotask(()=>render(true));else{const s=$("#be73Status");if(s&&/BOAT EDGE V7[34]/.test(s.innerHTML))s.innerHTML=s.innerHTML.replace(/BOAT EDGE V7[34]/g,"BOAT EDGE V76")}});
 mo.observe(root,{childList:true,subtree:true});
}
function hook(){
 observe();render(true);setTimeout(()=>render(true),1500);setTimeout(()=>render(true),4000);
 setInterval(()=>{if(document.visibilityState==="visible")render()},30000);
 document.addEventListener("visibilitychange",()=>{if(document.visibilityState==="visible")render(true)});
}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",hook):hook();
})();

/* BOAT_EDGE_SITE_V72_LIVE_STATUS */
(()=>{"use strict";
window.BOAT_EDGE_SITE_VERSION="V72";
const $=(q,r=document)=>r.querySelector(q);
async function get(){
 try{
  const r=await fetch(`./data/site_health.json?t=${Date.now()}`,{cache:"no-store"});
  return r.ok?await r.json():null;
 }catch(_){return null}
}
function statusText(d){
 const o=d?.odds||{}, l=d?.learning||{}, rs=d?.results||{};
 let odds="オッズ 待機中";
 if((o.errors||0)>0) odds=`オッズ 一部エラー ${o.errors}件`;
 else if((o.updated||0)>0) odds=`実オッズ取得 ${o.updated}R`;
 else if((o.checked||0)>0) odds=`オッズ確認 ${o.checked}R`;
 const learn=`学習採点 ${l.evaluated||0}R`;
 const result=(rs.updated||0)>0?`結果反映 ${rs.updated}R`:"結果待ち";
 return {odds,learn,result};
}
function ensure(){
 let x=$("#be72Status");
 if(x)return x;
 x=document.createElement("section");x.id="be72Status";
 x.style.cssText="margin:10px 0;padding:10px 12px;border:1px solid #dfe5ec;border-radius:12px;background:#fff;font-size:12px;line-height:1.5";
 const home=$("#be51Home");
 const pred=$("#tab-pred .section")||$("#tab-pred");
 (home||pred||document.body).prepend(x);
 return x;
}
async function render(){
 const x=ensure(),d=await get();
 if(!d){x.innerHTML='<b>BOAT EDGE V72</b>　稼働状況を取得中';return}
 const s=statusText(d);
 const badge=d.site_asset_v72?"反映済み":"確認中";
 x.innerHTML=`<div style="display:flex;justify-content:space-between;gap:8px;align-items:center;flex-wrap:wrap">
 <b>BOAT EDGE ${d.site_version||"V72"} <span style="font-weight:600">● ${badge}</span></b>
 <span>${d.generated_at||"—"}</span></div>
 <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:5px">
 <span>${s.odds}</span><span>${s.result}</span><span>${s.learn}</span></div>`;
}
function hook(){
 render();
 setInterval(()=>{if(document.visibilityState==="visible")render()},60000);
 window.addEventListener("boat-edge-formal120",render);
 if(typeof renderHome==="function"&&!renderHome.__be72){
  const old=renderHome;renderHome=function(...a){const y=old.apply(this,a);queueMicrotask(render);return y};renderHome.__be72=true;
 }
 if(typeof renderRace==="function"&&!renderRace.__be72){
  const old=renderRace;renderRace=function(...a){const y=old.apply(this,a);queueMicrotask(render);return y};renderRace.__be72=true;
 }
}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",hook):hook();
})();

/* BOAT_EDGE_SITE_V77_HOME_POLISH */
(()=>{"use strict";
window.BOAT_EDGE_SITE_VERSION="V77";
const $=(q,r=document)=>r.querySelector(q);
function cleanLegacy(){
  // V72 health/status is useful internally but duplicate on the public home.
  document.querySelectorAll("body *").forEach(el=>{
    if(el.children.length>12)return;
    const t=(el.textContent||"").trim();
    if(/^BOAT EDGE V72\s*[●・]/.test(t) && /反映済み|オッズ|結果|学習/.test(t)){
      el.style.display="none";
      el.dataset.be77Hidden="legacy-v72";
    }
  });
}
function urgency(){
  const root=$("#be76Priority"); if(!root)return;
  root.querySelectorAll("button[data-file]").forEach(b=>{
    const txt=b.textContent||"";
    const m=/あと\s*(\d+)分/.exec(txt);
    if(!m)return;
    const n=+m[1];
    b.style.transition="border-color .15s,background .15s";
    if(n<=5){
      b.style.borderColor="#ff9b8f"; b.style.background="#fff6f4";
      let x=b.querySelector(".be77-urgent");
      if(!x){x=document.createElement("div");x.className="be77-urgent";x.style.cssText="font-size:10px;font-weight:900;color:#d7442f;margin-top:3px";b.appendChild(x)}
      x.textContent=n<=1?"まもなく締切":"締切5分以内";
    }else if(n<=15){
      b.style.borderColor="#f2c36b"; b.style.background="#fffaf0";
    }
  });
}
function polish(){
  cleanLegacy();
  const status=$("#be73Status");
  if(status){
    status.innerHTML=status.innerHTML.replace(/BOAT EDGE V7[3-6]/g,"BOAT EDGE V77");
    status.style.marginBottom="12px";
  }
  const pri=$("#be76Priority");
  if(pri){
    pri.style.marginTop="8px";
    pri.style.marginBottom="12px";
    urgency();
    const rec=pri.querySelector("#be76Rec");
    if(rec){
      const t=(rec.textContent||"");
      if(/現時点なし/.test(t)){
        const note=rec.querySelector(".be77-rec-note");
        if(!note){
          const d=document.createElement("div");
          d.className="be77-rec-note";
          d.style.cssText="font-size:10px;color:#7890aa;margin-top:5px";
          d.textContent="無理に選ばず、条件成立時だけAI推奨を表示";
          rec.firstElementChild?.appendChild(d);
        }
      }
    }
  }
  const h=$("#homeView");
  if(h){
    h.querySelectorAll("h1,h2").forEach(x=>{x.style.marginBottom="10px"});
  }
}
function boot(){
  polish();
  const mo=new MutationObserver(()=>requestAnimationFrame(polish));
  mo.observe(document.body,{childList:true,subtree:true});
  setInterval(polish,15000);
  document.addEventListener("visibilitychange",()=>{if(document.visibilityState==="visible")polish()});
}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",boot):boot();
})();
