/* BOAT EDGE V175: audited odds band display only; no prediction/ticket/stake edits. */
(()=>{'use strict';
const validCombo=x=>typeof x==='string'&&/^[1-6]-[1-6]-[1-6]$/.test(x)&&new Set(x.split('-')).size===3;
function band(value){
  if(value===null||value===undefined||value==='')return null;
  const x=Number(value);if(!Number.isFinite(x)||x<=0)return null;
  return x<10?'under10':x<30?'10to29':x<50?'30to49':x<100?'50to99':'over100';
}
const KEYS=['under10','10to29','30to49','50to99','over100'];
function analyze(mode,modes,freshOdds,settled=false){
  if(settled)return {status:'settled'};
  const src=modes?.[mode]?.tickets||modes?.[mode];
  if(!Array.isArray(src))return {status:'missing_tickets'};
  const combos=[...new Set(src.map(x=>typeof x==='string'?x:x?.combo).filter(validCombo))];
  const counts=Object.fromEntries(KEYS.map(k=>[k,0]));
  if(!freshOdds||typeof freshOdds!=='object'||!Object.keys(freshOdds).length)
    return {status:'missing_odds',total:combos.length,known:0};
  let known=0;
  for(const combo of combos){const b=band(freshOdds[combo]);if(b){counts[b]++;known++;}}
  if(!known)return {status:'missing_odds',total:combos.length,known};
  return {status:'ok',total:combos.length,known,unknown:combos.length-known,
    counts,high:counts['50to99']+counts.over100,veryHigh:counts.over100};
}
const records=new Map();let currentKey='',updating=false;
function register(key,modes,freshOdds,resultConfirmed){
  if(!/^\d{8}-\d{2}-\d{2}$/.test(String(key||''))||!modes)return false;
  records.set(key,{modes,odds:freshOdds,settled:!!resultConfirmed});currentKey=key;
  if(records.size>16)records.delete(records.keys().next().value);
  if(typeof setTimeout==='function')setTimeout(render,0);
  return true;
}
function render(){
  if(updating)return;
  const panel=document.querySelector('#be108PredictionModes');
  if(!panel||!currentKey||!records.has(currentKey))return;
  const top=panel.querySelector('.be108-mode-top');if(!top)return;
  const mode=panel.querySelector('.be108-mode-tabs button.on')?.getAttribute('data-be108-mode')||'hit';
  const rec=records.get(currentKey),a=analyze(mode,rec.modes,rec.odds,rec.settled);
  let note=panel.querySelector('.be175-payout-bands');updating=true;
  try{
    if(!note){note=document.createElement('div');note.className='be175-payout-bands';
      const after=panel.querySelector('.be174-mode-clarity');
      (after||top).insertAdjacentElement('afterend',note);
    }
    let msg='';
    if(a.status==='settled')msg='配当帯：結果確定後のオッズから、当時の買い目の配当を再推定しません。確定払戻は上に表示。';
    else if(a.status==='missing_tickets')msg='配当帯：選択中の買い目を取得できません。';
    else if(a.status==='missing_odds')msg='配当帯：検証済みの新しい公式3連単オッズがないため判定保留（古い倍率や不整合値は使いません）。';
    else{
      const c=a.counts;
      msg='選択中の買い目の配当帯：10倍未満 '+c.under10+'点 / 10〜29.9倍 '+c['10to29']+'点 / '+
        '30〜49.9倍 '+c['30to49']+'点 / 50〜99.9倍 '+c['50to99']+'点 / '+
        '100倍以上 '+c.over100+'点。確認済み '+a.known+'/'+a.total+'点。';
      if(mode==='hole')msg+=a.high===0?
        ' この「波乱展開」の買い目には50倍以上がなく、配当面では高配当狙いとは呼びません。':
        ' 高配当候補（50倍以上）'+a.high+'点、うち万舟候補（100倍以上）'+a.veryHigh+'点。';
      if(a.unknown)msg+=' 倍率未取得 '+a.unknown+'点は判定外。';
    }
    msg+=' 配当帯は表示専用。オッズは予想順位・買い目・1万円配分に使用しません。';
    if(note.textContent!==msg)note.textContent=msg;
  }finally{updating=false;}
}
function initialize(){
  if(!document.getElementById('be175-payout-style')){
    const style=document.createElement('style');style.id='be175-payout-style';
    style.textContent='.be175-payout-bands{margin:8px 0 10px;padding:10px 12px;border:1px solid #d7e1eb;border-radius:12px;background:#f6f9fc;color:#20384d;font-size:12px;line-height:1.65;font-weight:650}';
    document.head.appendChild(style);
  }
  render();
  if(typeof MutationObserver!=='undefined'){
    new MutationObserver(()=>{if(!updating)render();}).observe(document.body,{subtree:true,childList:true});
  }
}
window.BoatEdgeV175={band,analyze,register,render};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize,{once:true});else initialize();
})();
