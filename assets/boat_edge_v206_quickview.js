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
const source=(r,k)=>{
 if(r?.meta?.phase!=='PRE_RESULT'||r?.meta?.results_seen!==false||r?.meta?.unlock!==false||r?.meta?.scoring!==false)return '結果未見条件を確認できず';
 const x=r?.source_audit?.[k];
 if(x?.status!=='ok'||!x.fetched_at||!/^[a-f0-9]{64}$/i.test(String(x.sha256||'')))return '未取得・未確認';
 const t=Date.parse(x.fetched_at),now=Date.now(),key=String(r?.race_key||''),deadline=String(r?.meta?.deadline||'');
 if(!Number.isFinite(t)||t>now+30000)return '取得時刻未確認';
 if(!/^20\d{6}-\d{2}-\d{2}$/.test(key)||!/^\d{1,2}:\d{2}$/.test(deadline))return '締切時刻未確認';
 const date=key.slice(0,4)+'-'+key.slice(4,6)+'-'+key.slice(6,8);
 const due=Date.parse(date+'T'+deadline.padStart(5,'0')+':00+09:00');
 if(!Number.isFinite(due)||t>due)return '締切後取得・未確認';
 if(now>=due)return '締切済（直前値）';
 if(now-t>25*60000)return '古い情報 '+stamp(x.fetched_at);
 return stamp(x.fetched_at)+'取得';
};
/* Counts represent present numeric fields only, not source verification or approval. */
const numericPresent=x=>typeof x==='number'&&Number.isFinite(x)&&x>0;
const sixBoatCount=(items,valid)=>Array.isArray(items)&&items.length<=6?
 items.filter(valid).length:0;
const completeness=r=>{
 const before=r?.beforeinfo||{},orig=r?.original_exhibition||{};
 const official=sixBoatCount(before.racers,x=>numericPresent(x?.exhibition_time));
 const original=sixBoatCount(orig.boats,x=>Array.isArray(x?.values)&&x.values.some(numericPresent));
 return '展示タイム '+official+'/6艇（'+source(r,'beforeinfo')+'） ／ オリ展 '+original+'/6艇（'+source(r,'original_exhibition')+'）';
};
/* V298: independent source-backed compare modes; no derived probabilities. */
const tabs={
 base:{label:'基本',hint:'全国・当地の勝率とモーター2連率。赤は6艇すべて有効で明確な単独1位のみ。',cols:[['全国勝率','national.win_rate',2,.4,false],['当地勝率','local.win_rate',2,.4,false],['M2連%','motor.quinella_rate',1,3,false]]},
 combo:{label:'連対・機力',hint:'各連対率は元データの数値。欠測を0%で補いません。',cols:[['全国2連%','national.quinella_rate',1,3,false],['当地2連%','local.quinella_rate',1,3,false],['全国3連%','national.trio_rate',1,3,false],['M2連%','motor.quinella_rate',1,3,false]]},
 exhibit:{label:'直前・展示',hint:'展示STのF、展示進入と本番進入は区別。平均STは選手の既存登録値。',cols:[['展示タイム','time',2,.05,true],['展示ST','st',2,.03,true],['展示進入','course',0,Infinity,false],['平均ST','avg',2,.03,true]]},
 original:{label:'オリ展',hint:'1周・まわり足・直線。オリ展CSVとBOATERS・競艇日和の独立照合は別。',cols:[['1周','lap',2,.08,true],['まわり足','turn',2,.04,true],['直線','straight',2,.04,true]]}
};
const field=(r,path)=>path.split('.').reduce((x,k)=>x?.[k],r);
let metric='base',layout='lanes',selectedLane=null,headSig='',showAll=false,ctx='',busy=false,queued=false,lastTable='',lastStatus='',started=false;
/* A visually outstanding number is never inferred from 4/6 known boats. */
function best(rows,path,margin,low){
 if(!Array.isArray(rows)||rows.length!==6||new Set(rows.map(r=>r?.lane)).size!==6||path==='course')return null;
 const data=rows.map(r=>field(r,path)).map(nr);
 if(data.some(x=>x===null||(!['st','avg'].includes(path)&&x<0)||(['time','lap','turn','straight'].includes(path)&&x<=0)))return null;
 if(path==='st'&&rows.some((r,i)=>r.f===true||data[i]<0))return null;
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
 if(path==='course'&&n!==null)v=Number.isInteger(n)&&n>=1&&n<=6?n+'コース':'－';
 return `<td class="be206-val${color(row,path,raw,b)}${path==='st'&&(row.f||n!==null&&n<0)?' foul':''}">${esc(v)}</td>`;
}
function format(rows){
 const specs=tabs[metric].cols,leaders=specs.map(c=>best(rows,c[1],c[3],c[4]));
 return `<thead><tr><th scope="col">選手</th>${specs.map(x=>`<th scope="col">${esc(x[0])}</th>`).join('')}</tr></thead><tbody>`+
 rows.map(r=>`<tr><th scope="row"><span class="be206-racer"><span class="be206-lane be206-l${r.lane}">${r.lane}</span><button type="button" class="be206-racername be206-headpick-trigger" data-be206-head="${r.lane}" aria-label="${r.lane}号艇 ${esc(r.name)}を1着とする既存買い目" aria-pressed="false">${esc(r.name)}<small>${esc(r.grade)}</small></button></span></th>${specs.map((c,i)=>cell(r,c[1],c[2],leaders[i])).join('')}</tr>`).join('')+'</tbody>';
}
/* Six colour-coded racer columns with a sticky metric label, like a data sheet.
   All values come from getRows() — no provider copy, network request or model call. */
function matrix(rows){
 const specs=tabs[metric].cols,leaders=specs.map(c=>best(rows,c[1],c[3],c[4]));
 return '<thead><tr><th scope="col">比較項目</th>'+rows.map(r=>
  '<th scope="col" data-be206-lane="'+r.lane+'"><span class="be206-lane be206-l'+r.lane+'">'+r.lane+'</span><button type="button" class="be206-headpick-trigger" data-be206-head="'+r.lane+'" aria-label="'+r.lane+'号艇 '+esc(r.name)+'を1着とする既存買い目" aria-pressed="false"><b>'+esc(r.name)+'</b><small>'+esc(r.grade)+'</small></button></th>'
 ).join('')+'</tr></thead><tbody>'+specs.map((c,i)=>
  '<tr><th scope="row">'+esc(c[0])+'</th>'+rows.map(r=>cell(r,c[1],c[2],leaders[i])).join('')+'</tr>'
 ).join('')+'</tbody>';
}
function create(root,p){
 let box=$('#be206Quick');if(box)return box;
 box=document.createElement('section');box.id='be206Quick';box.className='be206-quick';
 box.innerHTML=`<div class="be206-title"><div><small>BOAT EDGE / 6艇早見表</small><h2>6艇をひと目で比較</h2></div><span class="be206-compact-tag">比較UI V298</span></div>
 <div class="be206-safety" role="status"><strong></strong><span></span></div>
 <div class="be206-switch" role="group" aria-label="6艇比較する情報"><button type="button" data-be206-metric="base">基本</button><button type="button" data-be206-metric="combo">連対・機力</button><button type="button" data-be206-metric="exhibit">直前・展示</button><button type="button" data-be206-metric="original">オリ展</button></div>
 <div class="be206-layout-switch" role="group" aria-label="比較表の並べ方"><button type="button" data-be206-layout="lanes">6艇横並び</button><button type="button" data-be206-layout="rows">選手ごと</button></div>
 <p class="be206-swipe-help">6艇横並び表は左右にスワイプして比較できます。赤は同じレース内で明確に強い値だけ。</p>
 <div class="be206-table-scroll"><table class="be206-table"></table></div>
 <div class="be206-matrix-scroll" tabindex="0" aria-label="6艇横並び比較表。左右にスクロールできます"><table class="be206-matrix"></table></div>
 <div class="be206-table-help"></div>
 <section class="be206-headpanel" role="status" aria-live="polite" hidden></section>
 <div class="be206-foot"><span class="be206-source"></span><button type="button" data-be206-before>直前情報を見る →</button></div>`;
 root.insertBefore(box,p);return box;
}

/* V299: head selection reads the already-rendered active-mode tickets only.
   It cannot create a new forecast, infer unrendered tickets, or reprioritise bets. */
function headTickets(ticketRows,lane){
 const num=Number(lane);
 if(!Number.isInteger(num)||num<1||num>6||!Array.isArray(ticketRows)||
    ticketRows.length<1||ticketRows.length>120)return null;
 const found=[],seen=new Set();
 for(let i=0;i<ticketRows.length;i++){
   const text=ticketRows[i]?.querySelector?.('b')?.textContent?.trim()||'';
   const m=text.match(/(?:^|[^0-9])([1-6]-[1-6]-[1-6])(?:$|[^0-9])/);
   if(!m)return null;
   const combo=m[1],parts=combo.split('-');
   if(new Set(parts).size!==3||seen.has(combo))return null;
   seen.add(combo);
   if(Number(parts[0])===num)found.push({rank:i+1,combo});
 }
 return found.slice(0,5);
}
function renderHead(box,r,mode,status){
 const el=$('.be206-headpanel',box),selected=selectedLane;
 if(!el)return;
 $$('.be206-headpick-trigger',box).forEach(btn=>{
  const on=selected===Number(btn.dataset.be206Head);
  btn.setAttribute('aria-pressed',String(on));
 });
 if(selected===null){
  if(!el.hidden)el.hidden=true;
  if(el.childNodes.length)el.replaceChildren();
  headSig='';return;
 }
 const marker=$('#be108PredictionModes .be181-freeze-banner')?.dataset?.be181Source||'';
 const locked=['first','final','latest'].includes(marker);
 const pre=keyOK(r?.race_key)&&r?.meta?.phase==='PRE_RESULT'&&
   r.meta.results_seen===false&&r.meta.unlock===false&&r.meta.scoring===false;
 const safe=pre&&status?.kind==='partial'&&locked; // Only recently checked cancellation signals; never assert confirmed starters.
 const tickets=safe?headTickets($$('#be108PredictionModes .be108-ticket-list > .be108-ticket'),selected):null;
 const racer=(window.BoatEdgeV203?.getRows?.(r)||[]).find(x=>x.lane===selected);
 const label=marker==='final'?'締切前FINAL保存の表示':marker==='first'?'FIRST保存の表示':
   marker==='latest'?'変動する参考表示':'保存・表示状態未確認';
 const sig=JSON.stringify([r?.race_key,mode,selected,status?.kind,marker,racer?.name,tickets]);
 if(headSig===sig&&el.hidden===false)return;
 headSig=sig;el.hidden=false;
 const title='<strong>'+selected+'号艇 '+esc(racer?.name||'選手未確認')+' の1着候補</strong>';
 const note='<small>表示中の予想スタイルの既存3連単から抽出。元順位を維持。独立した頭確率・新規予想・購入指示ではありません。</small>';
 const help='<span class="be206-head-source">'+esc(label)+'</span>';
 const lines=tickets===null?'<p>出走可否・予想保存状態・買い目形式を確認できないため表示しません。</p>':
   tickets.length===0?'<p>表示中の買い目に、この艇が1着の候補はありません。</p>':
   '<ol>'+tickets.map(x=>'<li><span>元順位 #'+x.rank+'</span><b>'+x.combo+'</b></li>').join('')+'</ol>';
 el.innerHTML='<div class="be206-head-top">'+title+help+
   '<button type="button" data-be206-head-close aria-label="頭候補を閉じる">× 閉じる</button></div>'+
   lines+note;
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
 if(ctx!==next){ctx=next;selectedLane=null;headSig='';showAll=false;lastTable='';lastStatus='';layout='lanes';}
 const box=create(root,p);if(box.nextElementSibling!==p)root.insertBefore(box,p);
 const st=window.BoatEdgeV205.sourceStatus();
 const safety=st.title+'|'+st.detail+'|'+st.kind;
 if(safety!==lastStatus||!$('.be206-safety strong',box)?.textContent){
   lastStatus=safety;
   const e=$('.be206-safety',box);e.dataset.kind=st.kind;
   $('.be206-safety strong',box).textContent=st.title;
   $('.be206-safety span',box).textContent=st.detail||'出走可否の照合状態は未確定';
 }
 $('.be206-switch button',box).forEach(b=>{const on=b.dataset.be206Metric===metric;b.classList.toggle('on',on);b.setAttribute('aria-pressed',String(on));});
 $('.be206-layout-switch button',box).forEach(b=>{const on=b.dataset.be206Layout===layout;b.classList.toggle('on',on);b.setAttribute('aria-pressed',String(on));});
 const compactTable=$('.be206-table-scroll',box),matrixTable=$('.be206-matrix-scroll',box);
 compactTable.hidden=layout!=='rows';matrixTable.hidden=layout!=='lanes';
 const data=JSON.stringify([r.race_key,metric,layout,rows.map(row=>[row.lane,row.name,row.grade,row.f,...tabs[metric].cols.map(c=>field(row,c[1]))]),r.source_audit?.beforeinfo?.fetched_at,r.source_audit?.original_exhibition?.fetched_at]);
 if(lastTable!==data||(layout==='lanes'?!$('.be206-matrix tbody',box):!$('.be206-table tbody',box))){
   if(layout==='lanes')$('.be206-matrix',box).innerHTML=matrix(rows);
   else $('.be206-table',box).innerHTML=format(rows);
   lastTable=data;
 }
 setText($('.be206-table-help',box),tabs[metric].hint+'　「－」は未取得。 '+completeness(r)+'。数値の存在は取得元・鮮度・独立照合の証明ではありません。');
 setText($('.be206-source',box),`直前データ証跡 ${source(r,'beforeinfo')} ／ オリ展証跡 ${source(r,'original_exhibition')}（取得履歴のみ。6艇分の値・外部照合・予想利用は別途確認）`);
 renderHead(box,r,mode,st);
 document.documentElement.classList.add('be206-active');
 const compact=$('.brandtext small');if(compact&&/^(?:サイトV205|v\d+)$/i.test(compact.textContent.trim()))compact.textContent='サイトV298';
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
   const layoutBtn=e.target.closest?.('#be206Quick [data-be206-layout]');
   if(layoutBtn){const next=layoutBtn.dataset.be206Layout;if(next==='lanes'||next==='rows'){layout=next;lastTable='';schedule();}return;}
   const headBtn=e.target.closest?.('#be206Quick [data-be206-head]');
   if(headBtn){
     const lane=Number(headBtn.dataset.be206Head);
     if(Number.isInteger(lane)&&lane>=1&&lane<=6){selectedLane=lane;headSig='';schedule();}
     return;
   }
   if(e.target.closest?.('#be206Quick [data-be206-head-close]')){
     selectedLane=null;headSig='';schedule();return;
   }
   if(e.target.closest?.('#be206Quick [data-be206-before]')){$('#raceTabs [data-tab="before"]')?.click();return;}
   if(e.target.closest?.('#be206MoreTickets')){showAll=!showAll;sync();}
 });
 const pred=$('#tab-pred');if(pred&&typeof MutationObserver!=='undefined')new MutationObserver(schedule).observe(pred,{childList:true,subtree:true});
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)schedule();});
 setInterval(()=>{if(!document.hidden)sync();},5000);sync();
}
window.BoatEdgeV206={sync,format,matrix,best,headTickets,version:'V299-UI-ONLY',displayOnly:true};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
