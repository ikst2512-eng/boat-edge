/* BOAT_EDGE_SITE_V57 */
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
 if(!back){back=document.createElement("button");back.id="be53Back";back.type="button";back.textContent="← 今日のレース";back.onclick=()=>{const p=$("#be51Panel");if(p){p.hidden=true;p.innerHTML=""}$$("[data-d]").forEach(x=>x.classList.remove("on"));if(typeof showView==="function")showView("homeView")};rv.prepend(back)}
 let rr=$("#be57RaceRefresh");if(!rr){rr=refreshButton().cloneNode(true);rr.id="be57RaceRefresh";rr.onclick=()=>{rr.disabled=true;rr.textContent="更新中…";location.reload()};rv.prepend(rr)}
}
function snapshot(){
 const k=raceKey(); if(!k||k==="--")return;
 const pred=$("#tab-pred"); if(!pred)return;
 const text=(pred.innerText||"").trim(); if(!text)return;
 const logs=readLog(); const old=logs.find(x=>x.key===k&&x.type==="prediction_snapshot");
 if(old)return;
 logs.push({type:"prediction_snapshot",key:k,saved_at:now(),prediction_text:text.slice(0,30000),version:"V57"});
 writeLog(logs);
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
 const count=readLog().filter(x=>x.type==="prediction_snapshot").length;
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