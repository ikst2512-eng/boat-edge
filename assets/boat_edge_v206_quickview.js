/* BOAT EDGE V206 — BOATERS-inspired, independently authored compact comparison UI.
 * DISPLAY ONLY. Never modifies odds, prediction outputs, scenario, tickets, payouts, scratches or frozen history. */
(()=>{'use strict';
if(window.BoatEdgeV206)return;
const $=(s,r=document)=>r.querySelector(s);
const $$=(s,r=document)=>[...r.querySelectorAll(s)];
const keyOK=k=>/^20\d{6}-\d{2}-\d{2}$/.test(String(k||''));
// 03: booleans and composite fields are not numeric measurements; genuine zero is.
const nr=x=>{
 if(x===null||x===undefined||typeof x==='boolean')return null;
 if(typeof x==='string'&&!x.trim())return null;
 if(typeof x!=='number'&&typeof x!=='string')return null;
 const n=Number(x);return Number.isFinite(n)?n:null;
};
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
const sixBoatCount=(items,valid)=>{
 if(!Array.isArray(items)||items.length>6)return 0;
 const known=new Set(),duplicate=new Set();
 for(const item of items){
  const lane=item?.lane;
  if(!Number.isInteger(lane)||lane<1||lane>6||!valid(item))continue;
  if(known.has(lane))duplicate.add(lane);
  known.add(lane);
 }
 for(const lane of duplicate)known.delete(lane);
 return known.size;
};
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
// V371: show all six racers as readable rows on narrow screens; desktop retains the matrix.
const preferredLayout=()=>window.matchMedia?.('(max-width: 650px)')?.matches?'rows':'lanes';
let metric='base',layout=preferredLayout(),selectedLane=null,headSig='',showAll=false,ctx='',busy=false,queued=false,lastTable='',lastStatus='',started=false;
let lastTicketList=null,awaitingTicketList=false;
let lastStructure='';
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
function cellData(row,path,d,b){
 const raw=field(row,path),n=nr(raw);
 let v=val(raw,d);
 if(path==='st'&&n!==null&&(row.f||n<0))v='F'+Math.abs(n).toFixed(2);
 if(path==='st'&&n!==null&&n>=0&&!row.f)v=n.toFixed(2);
 if(path==='course'&&n!==null)v=Number.isInteger(n)&&n>=1&&n<=6?n+'コース':'－';
 return {text:v,className:`be206-val${color(row,path,raw,b)}${path==='st'&&(row.f||n!==null&&n<0)?' foul':''}`};
}
function cell(row,path,d,b){
 const value=cellData(row,path,d,b);
 return `<td class="${value.className}">${esc(value.text)}</td>`;
}
/* Retain racer buttons while only numeric cells change during same-race updates. */
function updateComparisonValues(table,rows,orientation,metricName){
 const specs=tabs[metricName]?.cols;
 if(!specs||!['lanes','rows'].includes(orientation)||!Array.isArray(rows)||rows.length!==6||!table?.querySelectorAll)return false;
 const cells=[...table.querySelectorAll('tbody td')];
 if(cells.length!==6*specs.length)return false;
 const leaders=specs.map(c=>best(rows,c[1],c[3],c[4]));
 const values=orientation==='lanes'?specs.flatMap((c,i)=>rows.map(r=>cellData(r,c[1],c[2],leaders[i]))):
   rows.flatMap(r=>specs.map((c,i)=>cellData(r,c[1],c[2],leaders[i])));
 cells.forEach((node,i)=>{
   setText(node,values[i].text);
   if(node.className!==values[i].className)node.className=values[i].className;
 });
 return true;
}
function format(rows){
 const specs=tabs[metric].cols,leaders=specs.map(c=>best(rows,c[1],c[3],c[4]));
 return `<thead><tr><th scope="col">選手</th>${specs.map(x=>`<th scope="col">${esc(x[0])}</th>`).join('')}</tr></thead><tbody>`+
 rows.map(r=>`<tr><th scope="row"><span class="be206-racer"><span class="be206-lane be206-l${r.lane}">${r.lane}</span><button type="button" class="be206-racername be206-headpick-trigger" data-be206-head="${r.lane}" aria-controls="be206HeadPanel" aria-expanded="false" aria-label="${r.lane}号艇 ${esc(r.name)}を1着とする既存買い目" aria-pressed="false">${esc(r.name)}<small>${esc(r.grade)}</small></button></span></th>${specs.map((c,i)=>cell(r,c[1],c[2],leaders[i])).join('')}</tr>`).join('')+'</tbody>';
}
/* Six colour-coded racer columns with a sticky metric label, like a data sheet.
   All values come from getRows() — no provider copy, network request or model call. */
function matrix(rows){
 const specs=tabs[metric].cols,leaders=specs.map(c=>best(rows,c[1],c[3],c[4]));
 return '<thead><tr><th scope="col">比較項目</th>'+rows.map(r=>
  '<th scope="col" data-be206-lane="'+r.lane+'"><span class="be206-lane be206-l'+r.lane+'">'+r.lane+'</span><button type="button" class="be206-headpick-trigger" data-be206-head="'+r.lane+'" aria-controls="be206HeadPanel" aria-expanded="false" aria-label="'+r.lane+'号艇 '+esc(r.name)+'を1着とする既存買い目" aria-pressed="false"><b>'+esc(r.name)+'</b><small>'+esc(r.grade)+'</small></button></th>'
 ).join('')+'</tr></thead><tbody>'+specs.map((c,i)=>
  '<tr><th scope="row">'+esc(c[0])+'</th>'+rows.map(r=>cell(r,c[1],c[2],leaders[i])).join('')+'</tr>'
 ).join('')+'</tbody>';
}
/* V341: explicit horizontal navigation; only the comparison viewport moves. */
function comparisonScrollState(view){
 const width=Number(view?.clientWidth),total=Number(view?.scrollWidth),left=Number(view?.scrollLeft);
 if(!Number.isFinite(width)||!Number.isFinite(total)||!Number.isFinite(left)||width<=0||total<=0)
   return {overflow:false,previous:false,next:false,left:0,max:0};
 const max=Math.max(0,total-width),position=Math.min(max,Math.max(0,left));
 return {overflow:max>1,previous:position>1,next:max-position>1,left:position,max};
}
function updateComparisonScroll(box){
 if(!box)return;
 const view=$('.be206-matrix-scroll',box),controls=$('.be206-scroll-controls',box);
 if(!view||!controls)return;
 const status=comparisonScrollState(view);
 controls.hidden=view.hidden||!status.overflow;
 $('[data-be206-scroll="previous"]',controls).disabled=!status.previous;
 $('[data-be206-scroll="next"]',controls).disabled=!status.next;
 setText($('.be206-scroll-position',controls),status.previous?(status.next?'左右の艇へ移動できます':'右端まで表示中'):'左端から表示中');
}
function scrollComparison(box,direction){
 if(!box)return false;
 const view=$('.be206-matrix-scroll',box),status=comparisonScrollState(view);
 if(!view||view.hidden||!status.overflow||!['previous','next'].includes(direction))return false;
 const sticky=$('thead th:first-child',view)?.offsetWidth||0;
 const step=Math.max(1,view.clientWidth-Math.min(sticky,view.clientWidth/2));
 const left=Math.min(status.max,Math.max(0,status.left+(direction==='next'?step:-step)));
 if(left===status.left)return false;
 view.scrollTo({left,behavior:window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches?'auto':'smooth'});
 return true;
}
function create(root,p){
 let box=$('#be206Quick');if(box)return box;
 box=document.createElement('section');box.id='be206Quick';box.className='be206-quick';
 box.innerHTML=`<div class="be206-title"><div><small>BOAT EDGE / 6艇早見表</small><h2>6艇をひと目で比較</h2></div><span class="be206-compact-tag">比較UI V298</span></div>
 <div class="be206-safety" role="status"><strong></strong><span></span></div>
 <div class="be206-switch" role="group" aria-label="6艇比較する情報"><button type="button" data-be206-metric="base">基本</button><button type="button" data-be206-metric="combo">連対・機力</button><button type="button" data-be206-metric="exhibit">直前・展示</button><button type="button" data-be206-metric="original">オリ展</button></div>
 <div class="be206-layout-switch" role="group" aria-label="比較表の並べ方"><button type="button" data-be206-layout="lanes">6艇横並び</button><button type="button" data-be206-layout="rows">選手ごと</button></div>
 <p class="be206-swipe-help">選手名をタップすると、その艇が1着の既存買い目を表示します。6艇横並び表は左右にスワイプ。赤は同じレース内で明確に強い値だけ。</p>
 <div class="be206-table-scroll"><table class="be206-table"></table></div>
 <div id="be206MatrixViewport" class="be206-matrix-scroll" role="region" tabindex="0" aria-label="6艇横並び比較表。左右にスクロールできます"><table class="be206-matrix"></table></div>
 <div class="be206-scroll-controls" role="group" aria-label="6艇比較表の横移動" hidden><button type="button" data-be206-scroll="previous" aria-controls="be206MatrixViewport">← 前の艇</button><span class="be206-scroll-position"></span><button type="button" data-be206-scroll="next" aria-controls="be206MatrixViewport">次の艇 →</button></div>
 <div class="be206-table-help"></div>
 <section id="be206HeadPanel" class="be206-headpanel" role="status" aria-live="polite" tabindex="-1" hidden></section>
 <div class="be206-foot"><span class="be206-source"></span><button type="button" data-be206-before>直前情報を見る →</button></div>`;
 $('.be206-matrix-scroll',box).addEventListener('scroll',()=>updateComparisonScroll(box),{passive:true});
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
  btn.setAttribute('aria-expanded',String(on));
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
 const safe=pre&&status?.kind==='partial'&&locked&&!awaitingTicketList; // Only recently checked cancellation signals; never assert confirmed starters.
 const tickets=safe?headTickets($$('#be108PredictionModes .be108-ticket-list > .be108-ticket'),selected):null;
 const racer=(window.BoatEdgeV203?.getRows?.(r)||[]).find(x=>x.lane===selected);
 const label=marker==='final'?'締切前FINAL保存の表示':marker==='first'?'FIRST保存の表示':
   marker==='latest'?'変動する参考表示':'保存・表示状態未確認';
 const sig=JSON.stringify([r?.race_key,mode,selected,status?.kind,marker,racer?.name,tickets]);
 if(headSig===sig&&el.hidden===false)return;
 headSig=sig;el.hidden=false;
 const note='<small>表示中の予想スタイルの既存3連単から抽出。元順位を維持。独立した頭確率・新規予想・購入指示ではありません。</small>';
 const lines=tickets===null?'<p>出走可否・予想保存状態・買い目形式を確認できないため表示しません。</p>':
   tickets.length===0?'<p>表示中の買い目に、この艇が1着の候補はありません。</p>':
   '<ol>'+tickets.map(x=>'<li><span>元順位 #'+x.rank+'</span><b>'+x.combo+'</b></li>').join('')+'</ol>';
 if(!$('.be206-head-top strong',el)||!$('.be206-head-source',el)||!$('.be206-head-lines',el)||!$('[data-be206-head-close]',el)){
   el.innerHTML='<div class="be206-head-top"><strong></strong><span class="be206-head-source"></span>'+
     '<button type="button" data-be206-head-close aria-label="頭候補を閉じる">× 閉じる</button></div>'+
     '<div class="be206-head-lines"></div>'+note;
 }
 setText($('.be206-head-top strong',el),selected+'号艇 '+(racer?.name||'選手未確認')+' の1着候補');
 setText($('.be206-head-source',el),label);
 const content=$('.be206-head-lines',el);
 if(content.innerHTML!==lines)content.innerHTML=lines;
}
/* A36: reuse only the race-scoped V223 provenance chips; no values inferred. */
function originalSourceStatus(key){
 const host=$('#be223Source');
 if(!keyOK(key)||host?.dataset?.raceKey!==key||host.hidden)
  return '独立オリ展：BOATERS 未取得・未照合 ／ 競艇日和 未取得・未照合';
 const label=(id,name)=>{
  const chip=$('[data-be223-ex="'+id+'"]',host);
  const quality=chip?.dataset?.quality||'unknown';
  return name+' '+(chip&&['ok','stale','wait','limited','stop'].includes(quality)?chip.textContent.trim():'未取得・未照合');
 };
 return '独立オリ展：'+label('boaters','BOATERS')+' ／ '+label('biyori','競艇日和');
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
 const list=$('.be108-ticket-list',p),oldRace=ctx.split('|')[0];
 const raceChanged=oldRace!==r.race_key;
  if(ctx!==next){
   if(oldRace&&oldRace!==r.race_key)awaitingTicketList=!list||list===lastTicketList;
   ctx=next;selectedLane=null;headSig='';showAll=false;lastTable='';lastStatus='';
   if(raceChanged)layout=preferredLayout();
  }
  if(awaitingTicketList&&list&&list!==lastTicketList)awaitingTicketList=false;
  if(!awaitingTicketList&&list)lastTicketList=list;
  document.documentElement.classList.toggle('be328-await-ticket-list',awaitingTicketList);
 const box=create(root,p);if(box.nextElementSibling!==p)root.insertBefore(box,p);
 const st=window.BoatEdgeV205.sourceStatus();
 const safety=st.title+'|'+st.detail+'|'+st.kind+'|'+awaitingTicketList;
 if(safety!==lastStatus||!$('.be206-safety strong',box)?.textContent){
   lastStatus=safety;
   const e=$('.be206-safety',box);e.dataset.kind=awaitingTicketList?'pending':st.kind;
   $('.be206-safety strong',box).textContent=awaitingTicketList?'新レースの予想を照合中':st.title;
   $('.be206-safety span',box).textContent=awaitingTicketList?'前レースの買い目は表示しません':(st.detail||'出走可否の照合状態は未確定');
 }
 box.querySelectorAll('.be206-switch button').forEach(b=>{const on=b.dataset.be206Metric===metric;b.classList.toggle('on',on);b.setAttribute('aria-pressed',String(on));});
 box.querySelectorAll('.be206-layout-switch button').forEach(b=>{const on=b.dataset.be206Layout===layout;b.classList.toggle('on',on);b.setAttribute('aria-pressed',String(on));});
 const compactTable=$('.be206-table-scroll',box),matrixTable=$('.be206-matrix-scroll',box);
 compactTable.hidden=layout!=='rows';matrixTable.hidden=layout!=='lanes';
 if(raceChanged)matrixTable.scrollLeft=0;
 const data=JSON.stringify([r.race_key,metric,layout,rows.map(row=>[row.lane,row.name,row.grade,row.f,...tabs[metric].cols.map(c=>field(row,c[1]))]),r.source_audit?.beforeinfo?.fetched_at,r.source_audit?.original_exhibition?.fetched_at]);
 const structure=JSON.stringify([r.race_key,metric,layout,rows.map(row=>[row.lane,row.name,row.grade])]);
 if(lastTable!==data||(layout==='lanes'?!$('.be206-matrix tbody',box):!$('.be206-table tbody',box))){
   const table=layout==='lanes'?$('.be206-matrix',box):$('.be206-table',box);
   if(lastStructure!==structure||!updateComparisonValues(table,rows,layout,metric))table.innerHTML=layout==='lanes'?matrix(rows):format(rows);
   lastTable=data;lastStructure=structure;
 }
 setText($('.be206-table-help',box),tabs[metric].hint+'　「－」は未取得。 '+completeness(r)+'。数値の存在は取得元・鮮度・独立照合の証明ではありません。');
 setText($('.be206-source',box),`直前データ証跡 ${source(r,'beforeinfo')} ／ オリ展証跡 ${source(r,'original_exhibition')}（取得履歴のみ。6艇分の値・外部照合・予想利用は別途確認） ／ ${originalSourceStatus(r.race_key)}`);
 renderHead(box,r,mode,st);
 document.documentElement.classList.add('be206-active');
 updateComparisonScroll(box);
 const compact=$('.brandtext small');if(compact&&/^(?:サイトV205|v\d+)$/i.test(compact.textContent.trim()))compact.textContent='サイトV298';
}
function tickets(){
 if(!document.documentElement.classList.contains('be206-active')||awaitingTicketList)return;
 const p=$('#be108PredictionModes');if(!p)return;
 const list=$('.be108-ticket-list',p),card=$('.be108-mode-card',p);if(!list||!card)return;
 const rows=$$('.be108-ticket',list);rows.forEach((x,i)=>x.classList.toggle('be206-hide-ticket',!showAll&&i>=5));
 let btn=$('#be206MoreTickets',card);
 if(rows.length<=5){btn?.remove();return;}
 if(!btn){btn=document.createElement('button');btn.id='be206MoreTickets';btn.type='button';card.appendChild(btn);}
 setText(btn,showAll?`上位5点だけ表示`:`残り${rows.length-5}点を見る（全${rows.length}点）`);
 btn.setAttribute('aria-expanded',String(showAll));
}
/* Only an explicit tap may reveal and focus the selected-racer panel. Never jump during timers/race updates. */
function canRevealHead(expected,actual,lane,current,panel){
 return keyOK(expected)&&expected===actual&&lane===current&&!!panel&&panel.isConnected===true&&!panel.hidden;
}
/* V342: restore keyboard/VoiceOver location only after an explicit close. */
function restoreHeadFocus(expected,actual,lane,box){
 if(!keyOK(expected)||expected!==actual||!Number.isInteger(lane)||lane<1||lane>6||!box||box.isConnected!==true)return false;
 const target=$$('.be206-headpick-trigger',box).find(button=>
   Number(button.dataset.be206Head)===lane&&button.isConnected===true&&!button.disabled&&button.getClientRects?.().length>0);
 if(!target)return false;
 target.focus({preventScroll:true});return true;
}
function closeHead(){
 const lane=selectedLane,key=race()?.race_key;
 selectedLane=null;headSig='';schedule();
 queueMicrotask(()=>{if(selectedLane===null)restoreHeadFocus(key,race()?.race_key,lane,$('#be206Quick'));});
}
function sync(){if(busy)return;busy=true;try{board();tickets();}catch(err){console.warn('[BOAT EDGE V206 display]',err);}finally{busy=false;}}
function schedule(){if(busy||queued)return;queued=true;queueMicrotask(()=>{queued=false;sync();});}
function init(){if(started)return;started=true;
 document.addEventListener('click',e=>{
   const scrollBtn=e.target.closest?.('#be206Quick [data-be206-scroll]');
   if(scrollBtn){scrollComparison($('#be206Quick'),scrollBtn.dataset.be206Scroll);return;}
   const metricBtn=e.target.closest?.('#be206Quick [data-be206-metric]');
   if(metricBtn){const next=metricBtn.dataset.be206Metric;if(tabs[next]){metric=next;lastTable='';schedule();}return;}
   const layoutBtn=e.target.closest?.('#be206Quick [data-be206-layout]');
   if(layoutBtn){const next=layoutBtn.dataset.be206Layout;if(next==='lanes'||next==='rows'){layout=next;lastTable='';schedule();}return;}
   const headBtn=e.target.closest?.('#be206Quick [data-be206-head]');
   if(headBtn){
     const lane=Number(headBtn.dataset.be206Head);
     if(Number.isInteger(lane)&&lane>=1&&lane<=6){
        const key=race()?.race_key;
        const opening=selectedLane!==lane;
        selectedLane=opening?lane:null;headSig='';schedule();
        if(opening)queueMicrotask(()=>{
          const panel=$('#be206Quick .be206-headpanel');
          if(!canRevealHead(key,race()?.race_key,lane,selectedLane,panel))return;
          panel.scrollIntoView?.({behavior:window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches?'auto':'smooth',block:'start'});
          panel.focus?.({preventScroll:true});
        });
      }
     return;
   }
   if(e.target.closest?.('#be206Quick [data-be206-head-close]')){
     closeHead();return;
   }
   if(e.target.closest?.('#be206Quick [data-be206-before]')){$('#raceTabs [data-tab="before"]')?.click();return;}
   if(e.target.closest?.('#be206MoreTickets')){showAll=!showAll;sync();}
 });
 document.addEventListener('keydown',e=>{
   if(e.key==='Escape'&&selectedLane!==null&&e.target.closest?.('#be206Quick .be206-headpanel')){
     e.preventDefault();closeHead();
   }
 });
 const pred=$('#tab-pred');if(pred&&typeof MutationObserver!=='undefined')new MutationObserver(schedule).observe(pred,{childList:true,subtree:true});
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)schedule();});
 window.addEventListener('resize',schedule,{passive:true});
 setInterval(()=>{if(!document.hidden)sync();},5000);sync();
}
window.BoatEdgeV206={sync,format,matrix,best,completeness,headTickets,canRevealHead,restoreHeadFocus,comparisonScrollState,updateComparisonScroll,scrollComparison,updateComparisonValues,version:'V299-UI-ONLY',displayRevision:'V342',displayOnly:true};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();

