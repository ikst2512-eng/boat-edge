/* BOAT EDGE V252 — source-readonly mobile race clarity and genuine 6-boat navigation.
 * Uses existing verified/presented DOM only. No model, odds, payout, scratch, stake,
 * frozen prediction, result collector, or Formal Fresh mutation. */
(function(root){
'use strict';
const KEY=/^20\d{6}-\d{2}-\d{2}$/;
const validKey=x=>typeof x==='string'&&KEY.test(x);
const pickVisible=(selectors,scope)=>{
 for(const s of selectors){
  const e=(scope||document).querySelector(s);
  if(e&&e.getClientRects().length&&e.getBoundingClientRect().height>0)return e;
 }
 return null;
};
const valueOf=(node,selector)=>node?.querySelector(selector)?.textContent?.trim()||'';
function summaryOf(card,strip){
 const cards=Array.from(card?.querySelectorAll('.command-card')||[]);
 const decision=valueOf(cards[0],'.cv');
 const grade=valueOf(cards[1],'.cv');
 const source=valueOf(cards[2],'.cv');
 const weather=Array.from(strip?.querySelectorAll('.strip-card')||[]).find(x=>
   /風\s*\/\s*波/.test(valueOf(x,'.label')));
 const wind=valueOf(weather,'.value');
 return {
  decision:decision||'結論を確認中',
  grade:grade||'未取得',
  sources:source||'取得状態を確認中',
  weather:wind||'未取得'
 };
}
if(typeof module!=='undefined'&&module.exports)
 module.exports={validKey,summaryOf};
if(typeof document==='undefined'||typeof window==='undefined')return;
if(window.BoatEdgeV252)return;
let compact=true,ready=false,signature='',lastKey='';
const find=s=>document.querySelector(s);
const make=(tag,cl,txt)=>{
 const e=document.createElement(tag);if(cl)e.className=cl;
 if(txt!==undefined)e.textContent=String(txt);
 return e;
};
const selected=()=>{try{return typeof state!=='undefined'?state?.race:null}catch(_){return null}};
function goTab(name,selectors){
 const btn=find('#raceTabs [data-tab="'+name+'"]');
 if(!btn)return false;
 btn.click();
 window.setTimeout(()=>{
  const target=pickVisible(selectors);
  if(target)target.scrollIntoView({behavior:'smooth',block:'start'});
 },200);
 return true;
}
function showRacers(){
 return goTab('pred',['#be206Quick','#be203Layout','#tab-pred .be203-cards','#boats','#tab-pred']);
}
function panel(){
 const host=find('#raceView .race-summary'),nav=find('#be249Focus');
 if(!host||!nav||!find('#be207Top'))return null;
 let section=find('#be252Tools');
 if(section)return section;
 section=make('section','be252-tools');section.id='be252Tools';
 section.setAttribute('aria-label','選択中レースの表示設定');
 const data=make('div','be252-kpis');data.setAttribute('aria-label','保存済みの判断と水面状況');
 const options=make('div','be252-options');
 const card=make('button','be252-card','出走表を見る');
 card.type='button';card.dataset.be252='card';
 const other=make('button','be252-card','他の画面・監査');
 other.type='button';other.dataset.be252='other';
 other.setAttribute('aria-controls','raceTabs');other.setAttribute('aria-expanded','false');
 const toggle=make('button','be252-toggle','詳細を全部表示');
 toggle.type='button';toggle.dataset.be252='toggle';toggle.setAttribute('aria-pressed','false');
 options.append(card,other,toggle);
 const note=make('p','be252-note','買い目・6艇・展開・直前は上の4つから。欠場やオッズの確認状態は表示された証跡を優先。');
 section.append(data,options,note);
 nav.insertAdjacentElement('afterend',section);
 return section;
}
function syncFullDetail(open){
 const rootNode=document.documentElement;
 rootNode.classList.toggle('be208-details-on',open);
 const api=window.BoatEdgeV205;
 if(api&&typeof api.change==='function'&&rootNode.classList.contains('be205-expanded')!==open)api.change();
 rootNode.classList.toggle('be202-expanded',open);
 const original=find('#be207Top [data-be207="detail"]');
 if(original){original.textContent=open?'詳しいデータ・監査を閉じる':'詳しいデータ・監査を開く';original.setAttribute('aria-expanded',String(open));}
}
function update(){
 const key=selected()?.race_key||'';
 const host=find('#raceView');
 if(!host||!host.classList.contains('active')||!validKey(key)){
  document.documentElement.classList.remove('be252-compact','be252-ready');
  lastKey='';signature='';return;
 }
 if(!find('#be207Top')||!find('#be249Focus'))return;
 const section=panel();if(!section)return;
 if(key!==lastKey){if(lastKey)syncFullDetail(false);lastKey=key;compact=true;signature='';}
 document.documentElement.classList.add('be252-ready');
 document.documentElement.classList.toggle('be252-compact',compact);
 const toggle=section.querySelector('[data-be252="toggle"]');
 toggle.textContent=compact?'詳細を全部表示':'簡単表示に戻す';
 toggle.setAttribute('aria-pressed',String(!compact));
 const other=section.querySelector('[data-be252="other"]');
 other.setAttribute('aria-expanded',String(!compact));
 const summary=summaryOf(find('#raceCommand'),find('#summaryStrip'));
 const sig=JSON.stringify([key,summary.decision,summary.grade,summary.sources,summary.weather]);
 if(sig===signature)return;
 signature=sig;
 const kpis=section.querySelector('.be252-kpis');
 kpis.replaceChildren();
 for(const [label,value] of [
  ['予想の結論',summary.decision],
  ['勝負度',summary.grade],
  ['直前取得',summary.sources],
  ['風・波',summary.weather]
 ]){
  const item=make('div','be252-kpi');
  item.append(make('small','',label),make('strong','',value));
  kpis.append(item);
 }
}
document.addEventListener('click',event=>{
 // Capture before V249's hidden legacy .be203-cards scroll. The visible V206
 // six-racer table is the actual default content; use it first.
 const racerButton=event.target?.closest?.('#be249Focus [data-nav="racers"]');
 if(racerButton){
  event.preventDefault();
  event.stopPropagation();
  showRacers();
  document.querySelectorAll('#be249Focus [data-nav]').forEach(b=>
   b.setAttribute('aria-pressed',String(b===racerButton)));
 }
},true);
document.addEventListener('click',event=>{
 const legacy=event.target?.closest?.('#be207Top [data-be207="detail"]');
 if(!legacy)return;
 event.preventDefault();event.stopPropagation();
 compact=!compact;signature='';syncFullDetail(!compact);update();
},true);
document.addEventListener('click',event=>{
 const button=event.target?.closest?.('#be252Tools [data-be252]');
 if(!button)return;
 const what=button.dataset.be252;
 if(what==='card'){goTab('card',['#tab-card .tablewrap','#tab-card']);return}
 if(what==='toggle'||what==='other'){
  compact=!compact;signature='';
  syncFullDetail(!compact);update();
  if(what==='other'&&!compact){
   const menu=find('#raceTabs');
   if(menu)window.setTimeout(()=>menu.scrollIntoView({behavior:'smooth',block:'start'}),75);
  }
 }
});
function start(){
 update();
 window.setInterval(()=>{if(!document.hidden)update()},2500);
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)update()});
}
window.BoatEdgeV252={refresh:update,showRacers,version:'V252-READONLY-UI'};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})(typeof window!=='undefined'?window:{});
