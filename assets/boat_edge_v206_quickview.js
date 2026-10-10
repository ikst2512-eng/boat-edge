/* BOAT EDGE V206 — BOATERS-inspired, independently authored compact comparison UI.
 * DISPLAY ONLY. Never modifies odds, prediction outputs, scenario, tickets, payouts, scratches or frozen history. */
(()=>{'use strict';
if(window.BoatEdgeV206)return;
const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>[...r.querySelectorAll(s)];
const keyOK=k=>/^20\d{6}-\d{2}-\d{2}$/.test(String(k||''));
const nr=x=>x===null||x===undefined||String(x).trim()===''?null:Number.isFinite(Number(x))?Number(x):null;
const val=(x,d=2)=>nr(x)===null?'－':Number(x).toFixed(d);
const esc=x=>String(x??'－').replace(/[&<>"']/g,s=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[s]));
const setText=(el,value)=>{if(el&&el.textContent!==value)el.textContent=value;};
const race=()=>{try{return typeof state==='undefined'?null:state?.race||null;}catch(_){return null;}};
const stamp=s=>{const d=s?new Date(s):null;return d&&Number.isFinite(d.getTime())?d.toLocaleTimeString('ja-JP',{timeZone:'Asia/Tokyo',hour:'2-digit',minute:'2-digit'}):null;};
const source=(r,k)=>{const x=r?.source_audit?.[k];return x?.status==='ok'&&x?.fetched_at&&x?.sha256&&Number.isFinite(Date.parse(x.fetched_at))?stamp(x.fetched_at):null;};
const tabs={base:{label:'基本',hint:'実力の比較。赤は6艇の中で差が明確な1位だけ。',cols:[['全国','national.win_rate',2,.4,false],['当地','local.win_rate',2,.4,false],['M2連','motor.quinella_rate',1,3,false]]},
 exhibit:{label:'展示',hint:'STは展示スタート。Fは展示フライング。実コース・本番STではありません。',cols:[['展示ST','st',2,.03,true],['1周','lap',2,.08,true],['回り足','turn',2,.04,true],['直線','straight',2,.04,true]]},
 combo:{label:'連対・機力',hint:'全国・当地の2連対率とモーター2連対率。数値はパーセント。',cols:[['全国2連','national.quinella_rate',1,3,false],['当地2連','local.quinella_rate',1,3,false],['全国3連','national.trio_rate',1,3,false],['M2連','motor.quinella_rate',1,3,false]]}};
const field=(r,path)=>path.split('.').reduce((x,k)=>x?.[k],r);
let metric='base',showAll=false,ctx='',busy=false,queued=false,lastTable='',lastStatus='',started=false;
function best(rows,path,margin,low){
 const data=rows.map(r=>field(r,path)).map(nr).filter(x=>x!==null);
 if(path==='st'){data.splice(0,data.length,...rows.filter(r=>!r.f&&nr(r.st)!==null&&Number(r.st)>=0).map(r=>Number(r.st)));}
 if(data.length<4)return null;
 data.sort((a,b)=>low?a-b:b-a);
 if(Math.abs(data[0]-data[1])+1e-9<margin)return null;
 return data[0];
}
function color(row,path,x,b){
 return b!==null&&nr(x)!==null&&Math.abs(Number(x)-b)<1e-8&&!(path==='st'&&(row.f||Number(x)<0))?' best':'';
}
function cell(row,path,d,b){
 const raw=field(row,path),n=nr(raw);
 let v=val(raw,d);
 if(path==='st'&&n!==null&&(row.f||n<0))v='F'+Math.abs(n).toFixed(2);
 if(path==='st'&&n!==null&&n>=0&&!row.f)v=n.toFixed(2);
 return `<td class="be206-val${color(row,path,raw,b)}${path==='st'&&(row.f||n!==null&&n<0)?' foul':''}">${esc(v)}</td>`;
}
function format(rows){
 const specs=tabs[metric].cols,leaders=specs.map(c=>best(rows,c[1],c[3],c[4]));
 return `<thead><tr><th scope="col">選手</th>${specs.map(x=>`<th scope="col">${esc(x[0])}</th>`).join('')}</tr></thead><tbody>`+
 rows.map(r=>`<tr><th scope="row"><span class="be206-racer"><span class="be206-lane be206-l${r.lane}">${r.lane}</span><span class="be206-racername">${esc(r.name)}<small>${esc(r.grade)}</small></span></span></th>${specs.map((c,i)=>cell(r,c[1],c[2],leaders[i])).join('')}</tr>`).join('')+'</tbody>';
}
function create(root,p){
 let box=$('#be206Quick');if(box)return box;
 box=document.createElement('section');box.id='be206Quick';box.className='be206-quick';
 box.innerHTML=`<div class="be206-title"><div><small>BOAT EDGE / 6艇早見表</small><h2>6艇をひと目で比較</h2></div><span class="be206-compact-tag">サイトV206</span></div>
 <div class="be206-safety" role="status"><strong></strong><span></span></div>
 <div class="be206-switch" role="group" aria-label="6艇比較する情報"><button type="button" data-be206-metric="base">基本</button><button type="button" data-be206-metric="exhibit">展示</button><button type="button" data-be206-metric="combo">連対・機力</button></div>
 <div class="be206-table-scroll"><table class="be206-table"></table></div>
 <div class="be206-table-help"></div>
 <div class="be206-foot"><span class="be206-source"></span><button type="button" data-be206-before>直前情報を見る →</button></div>`;
 root.insertBefore(box,p);return box;
}
function board(){
 const r=race(),p=$('#be108PredictionModes'),root=$('#tab-pred .section.stack');
 if(!keyOK(r?.race_key)||!root||!p||!window.BoatEdgeV203?.getRows||!window.BoatEdgeV205?.sourceStatus||!$('#be203Layout')||!$('#be204Overview')){
   document.documentElement.classList.remove('be206-active');$('#be206Quick')?.remove();return;
 }
 const rows=window.BoatEdgeV203.getRows(r);
 if(rows.length!==6||new Set(rows.map(x=>x.lane)).size!==6){document.documentElement.classList.remove('be206-active');$('#be206Quick')?.remove();return;}
 const mode=$('#be108PredictionModes .be108-mode-tabs .on')?.dataset?.be108Mode||'';
 const next=r.race_key+'|'+mode;
 if(ctx!==next){ctx=next;showAll=false;lastTable='';}
 const box=create(root,p);if(box.nextElementSibling!==p)root.insertBefore(box,p);
 const st=window.BoatEdgeV205.sourceStatus();
 const safety=st.title+'|'+st.detail+'|'+st.kind;
 if(safety!==lastStatus){
   lastStatus=safety;
   const e=$('.be206-safety',box);e.dataset.kind=st.kind;
   $('.be206-safety strong',box).textContent=st.title;
   $('.be206-safety span',box).textContent=st.detail||'出走可否の照合状態は未確定';
 }
 $$('.be206-switch button',box).forEach(b=>{const on=b.dataset.be206Metric===metric;b.classList.toggle('on',on);b.setAttribute('aria-pressed',String(on));});
 const data=JSON.stringify([r.race_key,metric,rows.map(row=>[row.lane,row.name,row.grade,...tabs[metric].cols.map(c=>field(row,c[1]))]),r.source_audit?.beforeinfo?.fetched_at,r.source_audit?.original_exhibition?.fetched_at]);
 if(lastTable!==data){$('.be206-table',box).innerHTML=format(rows);lastTable=data;}
 setText($('.be206-table-help',box),tabs[metric].hint+'　「－」は未取得。');
 setText($('.be206-source',box),`公式展示 ${source(r,'beforeinfo')||'未取得'} ／ オリ展 ${source(r,'original_exhibition')||'未取得'}（取得時刻・予想利用は別）`);
 document.documentElement.classList.add('be206-active');
 const compact=$('.brandtext small');if(compact&&/^(?:サイトV205|v\d+)$/i.test(compact.textContent.trim()))compact.textContent='サイトV206';
}
function tickets(){
 if(!document.documentElement.classList.contains('be206-active'))return;
 const p=$('#be108PredictionModes');if(!p)return;
 const list=$('.be108-ticket-list',p),card=$('.be108-mode-card',p);if(!list||!card)return;
 const rows=$$('.be108-ticket',list);rows.forEach((x,i)=>x.classList.toggle('be206-hide-ticket',!showAll&&i>=5));
 let btn=$('#be206MoreTickets',card);
 if(rows.length<=5){btn?.remove();return;}
 if(!btn){btn=document.createElement('button');btn.id='be206MoreTickets';btn.type='button';card.appendChild(btn);}
 setText(btn,showAll?`上位5点だけ表示`:`残り${rows.length-5}点を見る（全${rows.length}点）`);
 btn.setAttribute('aria-expanded',String(showAll));
}
function sync(){if(busy)return;busy=true;try{board();tickets();}catch(err){console.warn('[BOAT EDGE V206 display]',err);}finally{busy=false;}}
function schedule(){if(busy||queued)return;queued=true;queueMicrotask(()=>{queued=false;sync();});}
function init(){if(started)return;started=true;
 document.addEventListener('click',e=>{
   const metricBtn=e.target.closest?.('#be206Quick [data-be206-metric]');
   if(metricBtn){const next=metricBtn.dataset.be206Metric;if(tabs[next]){metric=next;lastTable='';schedule();}return;}
   if(e.target.closest?.('#be206Quick [data-be206-before]')){$('#raceTabs [data-tab="before"]')?.click();return;}
   if(e.target.closest?.('#be206MoreTickets')){showAll=!showAll;sync();}
 });
 const pred=$('#tab-pred');if(pred&&typeof MutationObserver!=='undefined')new MutationObserver(schedule).observe(pred,{childList:true,subtree:true});
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)schedule();});
 setInterval(()=>{if(!document.hidden)sync();},5000);sync();
}
window.BoatEdgeV206={sync,version:'V206',displayOnly:true};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
