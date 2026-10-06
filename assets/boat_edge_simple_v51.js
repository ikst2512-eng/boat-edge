/* BOAT_EDGE_SITE_V61_SINGLE_SAFE_LEDGER */
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
