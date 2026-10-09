/* BOAT EDGE V163 — Global same-day race selector + factual racer/course stats.
 * UI-only: no prediction, stake, result, frozen snapshot, or formal state changes.
 * Data sources: data/today.json; data/races/YYYYMMDD-jcd-rno.json;
 *               data/site_course_stats/XX.json (venue × course recent 3 mo).
 */
(() => {
  'use strict';
  const VENUES = { '01':'桐生','02':'戸田','03':'江戸川','04':'平和島','05':'多摩川','06':'浜名湖',
    '07':'蒲郡','08':'常滑','09':'津','10':'三国','11':'びわこ','12':'住之江',
    '13':'尼崎','14':'鳴門','15':'丸亀','16':'児島','17':'宮島','18':'徳山',
    '19':'下関','20':'若松','21':'芦屋','22':'福岡','23':'唐津','24':'大村' };
  const $ = (s, scope=document) => scope.querySelector(s);
  const $$ = (s, scope=document) => Array.from(scope.querySelectorAll(s));
  const escapeHtml = x => String(x ?? '').replace(/[&<>"']/g, ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const numeric = x => (x === null || x === undefined || String(x).trim() === '' || !Number.isFinite(Number(x))) ? null : Number(x);
  const percent = x => numeric(x) === null ? '－' : numeric(x).toFixed(1) + '%';
  const jstDay = () => new Date(Date.now() + 9*3600_000).toISOString().slice(0,10).replaceAll('-','');
  const normJcd = x => String(x ?? '').padStart(2,'0');
  const statsCache = new Map();
  let nav, navVenue, navRaces, navStatus;
  let currentDay = null, selectedVenue = null, latestRaceSignature = '', latestView = '', syncedRaceKey = '';
  let lastDayFetch = 0, initialized = false, refreshScheduled = false;
  let alive = true;

  function courseSummary(row) {
    if (!row || ['first_rate','second_rate','third_rate'].some(k=>numeric(row[k]) === null)) return null;
    const trio = numeric(row.first_rate)+numeric(row.second_rate)+numeric(row.third_rate);
    return {first: numeric(row.first_rate), second:numeric(row.second_rate), third:numeric(row.third_rate), trio:+trio.toFixed(2),
      escape:numeric(row.escape), sashi:numeric(row.sashi), makuri:numeric(row.makuri), makuriSashi:numeric(row.makuri_sashi)};
  }
  function verifiedCourseMap(race) {
    const rows = Array.isArray(race?.actual_entry) ? race.actual_entry : [];
    if (rows.length!==6) return null;
    const courses = new Map();
    for (const r of rows) {
      const lane=numeric(r.lane), course=numeric(r.course);
      if (!Number.isInteger(lane)||lane<1||lane>6||!Number.isInteger(course)||course<1||course>6||courses.has(lane)) return null;
      courses.set(lane,course);
    }
    return new Set(courses.values()).size===6 ? courses : null;
  }
  function racerTrioRows(race) {
    return (race?.racers||[]).map((r,i)=>({lane:Number(r.lane ?? (i+1)),name:String(r.name ?? ''),
      nationalTrio:numeric(r.national?.trio_rate),localTrio:numeric(r.local?.trio_rate),
      nationalTwo:numeric(r.national?.quinella_rate),localTwo:numeric(r.local?.quinella_rate)})).filter(r=>r.lane>=1&&r.lane<=6);
  }
  function bestLane(rows,key,minimumGap=5) {
    const values=rows.filter(r=>numeric(r[key])!==null).sort((a,b)=>b[key]-a[key]);
    return values.length>1 && values[0][key]-values[1][key]>=minimumGap ? values[0].lane : null;
  }
  function sourceLiveDay(obj){return obj&&String(obj.date||'').replaceAll('-','')===jstDay()&&Array.isArray(obj.venues)?obj:null;}
  async function loadDay(force=false) {
    const source = typeof state !== 'undefined' ? sourceLiveDay(state?.today) : null;
    if(source && !force){ currentDay=source; return source; }
    if(!force && currentDay && Date.now()-lastDayFetch<30000)return currentDay;
    try {
      const res=await fetch('./data/today.json?be163='+Math.floor(Date.now()/30000),{cache:'no-store'});
      if (!res.ok) throw new Error('HTTP '+res.status);
      const raw=await res.json(); lastDayFetch=Date.now();
      currentDay=sourceLiveDay(raw);
    } catch (_) { currentDay=source || currentDay; }
    return currentDay;
  }
  function validRaceFile(file) { return /^data\/races\/\d{8}-\d{2}-\d{2}\.json$/.test(String(file??'')); }
  function activeView() { return $('.view.active')?.id || 'homeView'; }
  function raceInView() { try {return typeof state==='undefined'?null:state.race||null;} catch(_){return null;} }
  function goHome() {
    const bottom=$('.bottomnav [data-view="homeView"]');
    if(bottom) bottom.click();
    else if(typeof window.showView==='function')window.showView('homeView');
    else {
      $$('.view').forEach(v=>v.classList.toggle('active',v.id==='homeView'));
    }
    window.scrollTo({top:0,behavior:'smooth'});
    scheduleRefresh();
  }
  function attachBrandHome() {
    const brand=$('.topbar .brand'); if(!brand || brand.dataset.be163Home==='1')return;
    brand.dataset.be163Home='1';brand.setAttribute('role','button');brand.setAttribute('tabindex','0');
    brand.setAttribute('aria-label','BOAT EDGEのホーム画面に戻る');
    brand.addEventListener('click',goHome);
    brand.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();goHome();}});
  }
  function mountNavigation() {
    if ($('#be163RaceNav')){nav=$('#be163RaceNav');navVenue=$('#be163Venue');navRaces=$('#be163Races');navStatus=$('#be163Status');return;}
    const header=$('.topbar'); if(!header)return;
    nav=document.createElement('nav');nav.id='be163RaceNav';nav.setAttribute('aria-label','当日の全レースを選択');
    nav.innerHTML='<div class="be163-nav-top"><b>本日のレース</b><select id="be163Venue" aria-label="開催場を選択"></select><span id="be163Status" aria-live="polite"></span></div>'+
      '<div id="be163Races" class="be163-race-strip" aria-label="レースを選択"></div>';
    const app=$('.app')||document.body, accent=$('.edge-accent');
    if(accent && accent.parentNode===app)app.insertBefore(nav,accent.nextSibling);
    else header.insertAdjacentElement('afterend',nav);
    navVenue=$('#be163Venue');navRaces=$('#be163Races');navStatus=$('#be163Status');
    const resizeHeader=()=>{document.documentElement.style.setProperty('--be163-topbar-height',Math.ceil(header.getBoundingClientRect().height)+'px');document.documentElement.style.setProperty('--be163-nav-height',nav.hidden?'0px':Math.ceil(nav.getBoundingClientRect().height)+'px');};
    resizeHeader();window.addEventListener('resize',resizeHeader);
    if(typeof ResizeObserver!=='undefined'){const observer=new ResizeObserver(resizeHeader);observer.observe(header);observer.observe(nav);}
    navVenue.addEventListener('change',()=>{ selectedVenue=navVenue.value;renderNavRaces(); });
    navRaces.addEventListener('click',e=>{
      const b=e.target.closest('button[data-file]');if(!b||b.disabled)return;
      const file=b.dataset.file,jcd=b.dataset.jcd;
      if(!validRaceFile(file))return;
      if(typeof window.loadRace==='function')window.loadRace(file,jcd);
      else if(typeof loadRace==='function')loadRace(file,jcd);
    });
  }
  function renderNavRaces() {
    if(!navRaces)return;
    const venue=(currentDay?.venues||[]).find(v=>normJcd(v.jcd)===selectedVenue);
    const race=raceInView();const cur=race?.race_key||'';
    navRaces.innerHTML=(venue?.races||[]).filter(r=>validRaceFile(r.file)).sort((a,b)=>Number(a.race_no)-Number(b.race_no)).map(r=>{
      const isCur=r.race_key===cur;
      const status=r.beforeinfo_status==='ok'?' 展示済':'';
      return '<button type="button" class="be163-race '+(isCur?'on':'')+'" data-jcd="'+escapeHtml(normJcd(venue.jcd))+'" data-file="'+escapeHtml(r.file)+'" aria-current="'+(isCur?'true':'false')+'">'+
        '<b>'+escapeHtml(r.race_no)+'R</b><small>'+escapeHtml(r.deadline||'')+'</small><em>'+status+'</em></button>';
    }).join('');
    if(!navRaces.children.length)navRaces.innerHTML='<span class="be163-empty">当日のレース公開待ち</span>';
    const on=navRaces.querySelector('button.on');
    if(on && nav.dataset.lastVenue!==selectedVenue){on.scrollIntoView({block:'nearest',inline:'center'});}
    nav.dataset.lastVenue=selectedVenue||'';
  }
  function renderNavigation() {
    if(!nav)return;
    const v=activeView();const shouldShow=v!=='homeView';
    nav.hidden=!shouldShow;
    document.documentElement.style.setProperty('--be163-nav-height',shouldShow?Math.ceil(nav.getBoundingClientRect().height)+'px':'0px');
    if(!shouldShow){latestView=v;return;}
    const day=currentDay;const race=raceInView();const today=jstDay();
    const venues=(day?.venues||[]).filter(v=>(v.races||[]).some(r=>validRaceFile(r.file)));
    if(!venues.length){navVenue.innerHTML='<option>開催場の取得待ち</option>';navRaces.innerHTML='';navStatus.textContent='当日'+today.slice(4,6)+'/'+today.slice(6)+'のデータ待ち';return;}
    const code=normJcd(race?.meta?.venue_code||'');
    if(race?.race_key && race.race_key!==syncedRaceKey && code!=='00' && venues.some(t=>normJcd(t.jcd)===code) && v==='raceView') { selectedVenue=code; syncedRaceKey=race.race_key; }
    if(!venues.some(t=>normJcd(t.jcd)===selectedVenue))selectedVenue=normJcd(venues[0].jcd);
    const prev=navVenue.value;
    const opts=venues.map(x=>'<option value="'+escapeHtml(normJcd(x.jcd))+'">'+escapeHtml(x.venue||VENUES[normJcd(x.jcd)]||normJcd(x.jcd))+'</option>').join('');
    if(navVenue.innerHTML!==opts)navVenue.innerHTML=opts;
    navVenue.value=selectedVenue;
    navStatus.textContent=day.date+' / '+venues.length+'場';
    const sig=[day.updated_at,selectedVenue,race?.race_key,v].join('|');
    if(sig!==latestRaceSignature || latestView!==v || prev!==selectedVenue)renderNavRaces();
    latestRaceSignature=sig;latestView=v;
    document.documentElement.style.setProperty('--be163-nav-height',Math.ceil(nav.getBoundingClientRect().height)+'px');
  }
  function refreshNavigation(){loadDay().then(()=>renderNavigation());}
  function scheduleRefresh(){if(refreshScheduled)return;refreshScheduled=true;requestAnimationFrame(()=>{refreshScheduled=false;refreshNavigation();});}

  function mountStats() {
    const root=$('#tab-data .section.stack'); if(!root)return false;
    if(!$('#be163TrioStats')){
      const tri=document.createElement('section');tri.id='be163TrioStats';tri.className='be163-stats-card';
      root.insertBefore(tri,root.firstChild);
    }
    if(!$('#be163MethodStats')){
      const method=document.createElement('section');method.id='be163MethodStats';method.className='be163-stats-card';
      $('#be163TrioStats')?.insertAdjacentElement('afterend',method);
    }
    return true;
  }
  function renderTrio(race){
    const host=$('#be163TrioStats'); if(!host||!race)return;
    const rows=racerTrioRows(race),nBest=bestLane(rows,'nationalTrio'),lBest=bestLane(rows,'localTrio');
    host.innerHTML='<div class="be163-stats-head"><h3>選手別・3連対率</h3><span>全国 / 当地</span></div>'+
      '<p class="be163-note">出走表に記載された選手成績。直近10走ではなく、集計期間・母数は現在のデータに未収録。勝率とは別の数値です。</p>'+
      '<div class="be163-table-scroll"><table class="be163-data-table"><thead><tr><th>艇・選手</th><th>全国3連対</th><th>当地3連対</th><th>全国2連対</th><th>当地2連対</th></tr></thead><tbody>'+
      rows.map(r=>'<tr><th><span class="be163-lane lane-'+r.lane+'">'+r.lane+'</span><span>'+escapeHtml(r.name)+'</span></th>'+
        '<td class="'+(r.lane===nBest?'be163-strong':'')+'">'+percent(r.nationalTrio)+'</td>'+
        '<td class="'+(r.lane===lBest?'be163-strong':'')+'">'+percent(r.localTrio)+'</td><td>'+percent(r.nationalTwo)+'</td><td>'+percent(r.localTwo)+'</td></tr>').join('')+
      '</tbody></table></div>';
  }
  async function courseStats(jcd){
    const code=normJcd(jcd);if(!/^\d{2}$/.test(code))return null;
    const existing=statsCache.get(code);if(existing&&Date.now()-existing.at<600000)return existing.obj;
    try{
      const resp=await fetch('./data/site_course_stats/'+code+'.json?be163='+Math.floor(Date.now()/600000),{cache:'no-store'});
      if(!resp.ok)return null;
      const obj=await resp.json();
      if(normJcd(obj.venue_code)!==code||obj.scope!=='venue_recent_3_months')return null;
      statsCache.set(code,{at:Date.now(),obj});return obj;
    }catch(_){return null;}
  }
  async function renderMethod(race){
    const host=$('#be163MethodStats');if(!host||!race)return;
    const code=race.meta?.venue_code || race.race_key?.split('-')[1];
    const id=String(race.race_key||'');
    host.innerHTML='<div class="be163-stats-head"><h3>コース別・決まり手率</h3><span>公式・場別3か月</span></div><p class="be163-note">公式コース統計を確認中…</p>';
    const obj=await courseStats(code);
    if(raceInView()?.race_key!==id)return; // stale async response must not replace another race
    if(!obj){host.innerHTML='<div class="be163-stats-head"><h3>コース別・決まり手率</h3></div><p class="be163-note">当地コース統計が取得できていません。未取得値は表示しません。</p>';return;}
    const confirmed=verifiedCourseMap(race);
    const rows=(race.racers||[]).map((r,i)=>{
      const lane=Number(r.lane??(i+1)),course=confirmed?.get(lane)??lane;
      return {lane,course,name:r.name||'',...courseSummary(obj.courses?.[String(course)])};
    });
    const keys=['first','trio','escape','sashi','makuri','makuriSashi'];
    const heads={first:'コース1着率',trio:'コース3連対率',escape:'逃げ',sashi:'差し',makuri:'まくり',makuriSashi:'まくり差し'};
    const bests=Object.fromEntries(keys.map(k=>[k,bestLane(rows,k,5)]));
    const firstDate=obj.period?.from||'－',lastDate=obj.period?.to||'－';
    host.innerHTML='<div class="be163-stats-head"><h3>コース別・決まり手率</h3><span>'+escapeHtml(obj.venue||'')+' / 3か月</span></div>'+
      '<p class="be163-note">'+escapeHtml(firstDate)+'〜'+escapeHtml(lastDate)+'の<strong>場×進入コース統計</strong>（選手個人の決まり手率ではありません）。'+
      (confirmed?'6艇の実進入コースで表示。':'実進入が未確定のため枠＝コースの暫定表示。')+
      '「逃げ・差し・まくり・まくり差し」は<strong>そのコースが勝った場合の決まり手内訳</strong>です。</p>'+
      '<div class="be163-table-scroll"><table class="be163-data-table be163-method-table"><thead><tr><th>艇・進入</th>'+keys.map(k=>'<th>'+heads[k]+'</th>').join('')+'</tr></thead><tbody>'+
      rows.map(r=>'<tr><th><span class="be163-lane lane-'+r.lane+'">'+r.lane+'</span><span>'+r.course+'コース</span></th>'+keys.map(k=>'<td class="'+(bests[k]===r.lane?'be163-strong':'')+'">'+percent(r[k])+'</td>').join('')+'</tr>').join('')+
      '</tbody></table></div><p class="be163-foot">「直近10走」「選手個人の6か月決まり手率」はまだ未収録。推測で埋めません。</p>';
  }
  let statsSignature='', statsSeq=0;
  function renderStats(force=false){
    if(!mountStats())return;
    const race=raceInView();if(!race)return;
    const sig=[race.race_key,race.meta?.updated_at,race.source_audit?.beforeinfo?.sha256].join('|');
    if(!force&&sig===statsSignature)return;
    statsSignature=sig;const seq=++statsSeq;
    renderTrio(race);
    renderMethod(race).catch(()=>{});
  }
  function tick(){if(!alive)return;
    const view=activeView(),race=raceInView();
    if(view!==latestView || [currentDay?.updated_at,selectedVenue,race?.race_key,view].join('|')!==latestRaceSignature)renderNavigation();
    if(view==='raceView')renderStats();
  }
  function init(){
    if(initialized)return;initialized=true;attachBrandHome();mountNavigation();mountStats();scheduleRefresh();
    const views=$$('.view');
    if(typeof MutationObserver!=='undefined'){
      const o=new MutationObserver(scheduleRefresh);for(const view of views)o.observe(view,{attributes:true,attributeFilter:['class']});
      const t=$('#raceTitle');if(t)o.observe(t,{childList:true,characterData:true,subtree:true});
    }
    // Reuse the existing SPA's race loader. This wraps the already-installed V108 handler.
    const prior=window.renderRace;
    if(typeof prior==='function'&&!prior.__be163Wrapped){
      const wrapper=function(){const value=prior.apply(this,arguments);setTimeout(()=>{scheduleRefresh();renderStats(true);},0);return value;};
      wrapper.__be163Wrapped=true;window.renderRace=wrapper;
    }
    document.addEventListener('visibilitychange',()=>{if(!document.hidden){loadDay(true).then(renderNavigation);renderStats(true);}});
    setInterval(tick,3000);
    setInterval(()=>{if(!document.hidden)loadDay(true).then(renderNavigation);},60000);
  }
  window.BoatEdgeV163={courseSummary,verifiedCourseMap,racerTrioRows,bestLane,jstDay,refresh:()=>loadDay(true).then(renderNavigation)};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
