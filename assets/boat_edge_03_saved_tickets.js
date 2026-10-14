/* BOAT EDGE 03: view-only, per-race first-seen reference ticket archive.
 * Reads existing V181 browser records. Never creates/rewrites records, never
 * reads outcomes, invents a final snapshot, or enables betting. */
(()=>{'use strict';
if(window.BoatEdge03SavedTickets)return;
const PREFIX='boatEdgeV181FirstShown:';
const MODES={hit:'的中重視',balance:'バランス',hole:'穴狙い',narrow:'絞り込み'};
const validKey=k=>/^20\d{6}-(?:0[1-9]|1\d|2[0-4])-(?:0[1-9]|1[0-2])$/.test(String(k||''));
const validCombo=c=>/^[1-6]-[1-6]-[1-6]$/.test(c)&&new Set(c.split('-')).size===3;
const current=()=>{try{return typeof state==='undefined'?null:state?.race||null}catch(_){return null}};
let activeKey='',mode='hit',shown=10,lastSignature='';
function parse(key,meta,record,now=Date.now()){
 if(!validKey(key)||!record||record.schema!=='V181_FIRST_SEEN_BEFORE_DEADLINE'||
    record.race_key!==key||!meta||meta.date!==key.slice(0,4)+'-'+key.slice(4,6)+'-'+key.slice(6,8)||
    String(meta.venue_code||'').padStart(2,'0')!==key.slice(9,11)||
    Number(meta.race_no)!==Number(key.slice(12,14))||
    !/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(String(meta.deadline||'')))return null;
 const due=Date.parse(meta.date+'T'+meta.deadline+':00+09:00');
 const seen=Date.parse(record.first_seen_at||'');
 if(!Number.isFinite(due)||!Number.isFinite(seen)||seen>=due||seen>now+60000)return null;
 if(!record.modes||Object.keys(MODES).some(m=>{
   const tickets=record.modes[m]?.tickets;
   if(!Array.isArray(tickets)||tickets.length===0||tickets.length>120)return true;
   const combos=tickets.map(t=>t?.combo);
   return combos.some(c=>typeof c!=='string'||!validCombo(c))||
     new Set(combos).size!==combos.length;
 }))return null;
 return {key,seen:record.first_seen_at,modes:record.modes};
}
function read(key,meta,now=Date.now()){
 try{return parse(key,meta,JSON.parse(localStorage.getItem(PREFIX+key)||'null'),now);}
 catch(_){return null;}
}
function markup(saved,currentMode='hit',limit=10){
 if(!saved||!Object.prototype.hasOwnProperty.call(MODES,currentMode))return '';
 const tickets=saved.modes[currentMode]?.tickets||[],count=limit==='all'?tickets.length:Math.min(Number(limit)||3,tickets.length);
 const stamp=new Date(saved.seen).toLocaleString('ja-JP',{timeZone:'Asia/Tokyo',month:'numeric',day:'numeric',hour:'2-digit',minute:'2-digit'});
 const modeButtons=Object.entries(MODES).map(([id,label])=>
   '<button type="button" data-be03-archive-mode="'+id+'" aria-pressed="'+(id===currentMode)+'">'+label+'</button>').join('');
 const countButtons=[3,5,10,'all'].map(n=>
   '<button type="button" data-be03-archive-count="'+n+'" aria-pressed="'+(n===limit)+'">'+(n==='all'?'全件':'Top'+n)+'</button>').join('');
 const rows=tickets.slice(0,count).map((t,i)=>
   '<li><span>#'+(i+1)+'</span><b>'+t.combo+'</b></li>').join('');
 return '<div class="be03-archive-head"><strong>保存済みの参考買い目</strong><span>この端末の初回記録</span></div>'+
   '<p class="be03-archive-notice">一度保存した買い目をレースごとに見返せます。'+stamp+' 記録。締切後も表示しますが、正式最終予想・的中判定・購入履歴ではありません。端末変更時は引き継がれません。</p>'+
   '<div class="be03-archive-controls" role="group" aria-label="保存した予想スタイル">'+modeButtons+'</div>'+
   '<div class="be03-archive-controls" role="group" aria-label="保存した買い目の件数">'+countButtons+'</div>'+
   '<ol class="be03-archive-lines" aria-label="保存済みの未検証参考3連単">'+rows+'</ol>'+
   '<small class="be03-archive-note">全'+tickets.length+'点の保存順位から表示。オッズ・配分・購入ボタンはありません。元の買い目は再計算・並べ替えしません。</small>';
}
function render(){
 const r=current(),key=r?.race_key||'',host=document.querySelector('#raceView .race-summary');
 const old=document.getElementById('be03SavedTickets');
 if(!host||!validKey(key)){old?.remove();activeKey='';lastSignature='';return;}
 if(key!==activeKey){activeKey=key;mode='hit';shown=10;lastSignature='';old?.remove();}
 const saved=read(key,r.meta);
 if(!saved){document.getElementById('be03SavedTickets')?.remove();lastSignature='';return;}
 const signature=JSON.stringify([key,saved.seen,mode,shown,
    Object.keys(MODES).map(m=>saved.modes[m].tickets.map(t=>t.combo))]);
 let panel=document.getElementById('be03SavedTickets');
 if(!panel){
   panel=document.createElement('section');
   panel.id='be03SavedTickets';panel.className='be03-saved-tickets';
   panel.dataset.raceKey=key;
   panel.setAttribute('aria-label','この端末の保存済み参考買い目');
   const before=host.querySelector('#be207Top')||host.querySelector('.summary-top');
   if(before)before.insertAdjacentElement('afterend',panel);else host.prepend(panel);
 }
 if(lastSignature===signature&&panel.dataset.raceKey===key)return;
 panel.dataset.raceKey=key;panel.innerHTML=markup(saved,mode,shown);lastSignature=signature;
}
function install(){
 if(!document.getElementById('be03ArchiveStyle')){
   const style=document.createElement('style');style.id='be03ArchiveStyle';
   style.textContent=[
     '#raceView .be03-saved-tickets{margin:10px 0;padding:12px;border:1px solid #cbd9e6;border-radius:9px;background:#fff;color:#1f3348}',
     '.be03-archive-head{display:flex;gap:8px;justify-content:space-between;align-items:center;flex-wrap:wrap}',
     '.be03-archive-head strong{font-size:17px}.be03-archive-head span{font-size:11px;color:#5d6b7b}',
     '.be03-archive-notice{font-size:12px;line-height:1.5;margin:7px 0;color:#57697b}',
     '.be03-archive-controls{display:flex;gap:5px;margin:8px 0;flex-wrap:wrap}',
     '.be03-archive-controls button{flex:1 1 auto;min-height:44px;min-width:62px;background:#f3f6f9;border:1px solid #c8d8e5;border-radius:6px;padding:8px;color:#263f5a;font-weight:700}',
     '.be03-archive-controls button[aria-pressed="true"]{background:#195b91;color:#fff;border-color:#195b91}',
     '.be03-archive-lines{display:grid;gap:4px;padding:0;margin:9px 0;list-style:none}',
     '.be03-archive-lines li{display:flex;gap:12px;align-items:center;padding:7px 9px;background:#f7f9fb;border-radius:5px}',
     '.be03-archive-lines li span{font-size:12px;color:#60748a}.be03-archive-lines li b{font-size:18px;font-variant-numeric:tabular-nums}',
     '.be03-archive-note{font-size:11px;line-height:1.5;color:#647587}',
     '#raceView.be03-race-loading #be03SavedTickets{display:none!important}'
   ].join('');
   document.head.append(style);
 }
 document.addEventListener('click',event=>{
   const b=event.target.closest?.('#be03SavedTickets button');
   if(!b)return;
   if(b.dataset.be03ArchiveMode&&Object.prototype.hasOwnProperty.call(MODES,b.dataset.be03ArchiveMode))
     mode=b.dataset.be03ArchiveMode;
   else if(['3','5','10','all'].includes(b.dataset.be03ArchiveCount))
     shown=b.dataset.be03ArchiveCount==='all'?'all':Number(b.dataset.be03ArchiveCount);
   else return;
   lastSignature='';render();
 });
 if(typeof MutationObserver!=='undefined'){
   const host=document.getElementById('raceView');
   if(host)new MutationObserver(render).observe(host,{subtree:true,childList:true,characterData:true});
 }
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)render();});
 setInterval(()=>{if(!document.hidden)render();},3000);
 render();
}
window.BoatEdge03SavedTickets={render,parse,read,markup,displayOnly:true};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',install,{once:true});
else install();
})();
