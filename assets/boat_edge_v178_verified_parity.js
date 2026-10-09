/* BOAT EDGE V178 — independently bound latest-formal prediction consumer.
   Reference predictions, historical freezes, ranking weights, stake plans and formal CURRENT not modified. */
(()=>{'use strict';
  const SHA=/^[a-f0-9]{64}$/;
  const KEY=/^\d{8}-\d{2}-\d{2}$/;
  const COMBO=/^[1-6]-[1-6]-[1-6]$/;
  const verified=new Map();
  const validCombo=s=>typeof s==='string'&&COMBO.test(s)&&new Set(s.split('-')).size===3;
  function canonical(v){
    if(v===null||typeof v==='boolean'||typeof v==='number'||typeof v==='string')return JSON.stringify(v);
    if(Array.isArray(v))return '['+v.map(canonical).join(',')+']';
    if(v&&typeof v==='object')return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
    throw new Error('NON_JSON_VALUE');
  }
  const derivedOf=raw=>raw?.derived||raw?.prediction?.derived||raw?.prediction||raw;
  const metaOf=raw=>raw?.formal_meta||raw?.meta;
  function ranked120(d){
    const rows=d?.ranked_120;
    if(!Array.isArray(rows)||rows.length!==120)return null;
    const combos=new Set();let sum=0,prev=Infinity;
    for(const x of rows){
      if(!x||!validCombo(x.combo)||combos.has(x.combo))return null;
      if(typeof x.probability!=='number'||!Number.isFinite(x.probability)||x.probability<0||x.probability>1)return null;
      if(x.probability>prev+1e-11)return null;
      combos.add(x.combo);sum+=x.probability;prev=x.probability;
    }
    if(Math.abs(sum-1)>0.0001)return null;
    for(let a=1;a<=6;a++)for(let b=1;b<=6;b++)for(let c=1;c<=6;c++){
      if(a!==b&&a!==c&&b!==c&&!combos.has(`${a}-${b}-${c}`))return null;
    }
    return rows;
  }
  function preview(d){const r=ranked120(d);return r?{top3:r.slice(0,3),top5:r.slice(0,5),top10:r.slice(0,10)}:null;}
  function stakeParity(d){
    const worlds=['world_a','world_b'].map((key,i)=>d?.[key]||d?.[i===0?'pattern_a':'pattern_b']);
    if(worlds.some(w=>!w))return false;
    const probs=worlds.map(w=>w?.probability??w?.prob??w?.rate);
    if(probs.some(x=>typeof x!=='number'||!Number.isFinite(x)||x<=0))return false;
    const sum=probs[0]+probs[1];
    if(Math.abs(sum-1)>0.0001&&Math.abs(sum-100)>0.01)return false;
    const expectedA=Math.round((10000*probs[0]/sum)/100)*100;
    const expected=[expectedA,10000-expectedA];
    return worlds.every((w,i)=>{
      const tickets=w?.tickets||w?.bets||w?.combinations;
      if(!Array.isArray(tickets)||!tickets.length)return false;
      let total=0;
      for(const t of tickets){
        if(typeof t!=='object'||!t)return false;
        const stake=t.amount??t.stake;
        if(!Number.isInteger(stake)||stake<100||stake%100!==0)return false;
        total+=stake;
      }
      return total===expected[i];
    });
  }
  function boundStatus(status,key,meta){
    if(!KEY.test(String(key||''))||!window.BoatEdgeV177?.contractStatus?.(status))return false;
    if(!meta||meta.race_key!==key||meta.model_id!==status.active_model_id)return false;
    const trusted=status.approved_prediction_sha256_by_race;
    return trusted&&typeof trusted==='object'&&!Array.isArray(trusted)&&
      typeof trusted[key]==='string'&&SHA.test(trusted[key])&&trusted[key]===meta.prediction_sha256;
  }
  async function hashDerived(d){
    const subtle=(typeof crypto!=='undefined'&&crypto?.subtle)?crypto.subtle:null;
    if(!subtle||typeof TextEncoder==='undefined')return null;
    const bytes=new TextEncoder().encode(canonical(d));
    const digest=await subtle.digest('SHA-256',bytes);
    return Array.from(new Uint8Array(digest),v=>v.toString(16).padStart(2,'0')).join('');
  }
  async function verifyRaw(raw,key,status){
    verified.delete(key);
    if(!window.BoatEdgeV177?.acceptRaw?.(raw,key,status))return false;
    const meta=metaOf(raw),d=derivedOf(raw);
    if(!boundStatus(status,key,meta)||!ranked120(d)||!stakeParity(d))return false;
    for(const k of ['world_a','world_b']){
      const world=d[k]||d[k==='world_a'?'pattern_a':'pattern_b'];
      const rows=world?.tickets||world?.bets||world?.combinations;
      if(!Array.isArray(rows)||!rows.length)return false;
      if(!rows.every(x=>validCombo(typeof x==='string'?x:x?.combo||x?.ticket||x?.bet)))return false;
    }
    let sha;try{sha=await hashDerived(d);}catch(_){return false;}
    if(!sha||sha!==meta.prediction_sha256)return false;
    verified.set(key,{derived:d,model_id:meta.model_id,sha,ref:status.formalParentSha,target_date:status.target_date});
    return true;
  }
  function isVerified(race,status){
    if(!race||!window.BoatEdgeV177?.acceptNormalized?.(race,status))return false;
    const proof=verified.get(race.race_key);
    return !!proof&&proof.derived===race.derived&&proof.model_id===status.active_model_id&&
      proof.sha===race.formal_meta?.prediction_sha256&&proof.target_date===status.target_date&&
      proof.ref===status.formalParentSha&&!!ranked120(race.derived)&&stakeParity(race.derived);
  }
  const escape=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;','\'':'&#39;'}[c]));
  let drawing=false;
  function render(){
    if(drawing)return;
    const panel=document.getElementById('be108PredictionModes');
    if(!panel)return;
    const header=panel.querySelector('.be108-head');if(!header)return;
    const race=typeof state!=='undefined'?state.race:null;
    const status=typeof state!=='undefined'?state.formal:null;
    const formal=isVerified(race,status);
    const desc=formal?preview(race.derived):null;
    const mode=panel.querySelector('.be108-mode-tabs button.on')?.getAttribute('data-be108-mode');
    let info='';
    if(formal&&desc){
      const list=n=>desc['top'+n].map(x=>x.combo).join(' / ');
      info=`<b>正式CURRENT 120通り・1万円配分・SHA照合済み</b><span>モデル ${escape(status.active_model_id)} ／ Top3 ${escape(list(3))}</span>`+
        `<span>Top5 ${escape(list(5))}</span><span>Top10 ${escape(list(10))}</span>`;
      if(mode==='hit'){
        const actual=[...panel.querySelectorAll('.be108-ticket-list .be108-ticket b')].map(x=>String(x.textContent).match(/[1-6]-[1-6]-[1-6]/)?.[0]).filter(Boolean);
        const expected=desc.top10.map(x=>x.combo);
        info+=`<strong>サイト的中重視10点と正式Top10の照合：${actual.length===10&&actual.every((x,i)=>x===expected[i])?'一致':'不一致・未採用（順位を改変しません）'}</strong>`;
      }
    }else{
      info='<b>最新予想の正式120通り照合：未完了</b><span>検証済み予測のレース別SHA・独立した承認一覧・120通り順位が揃うまで、サイト参考予想を正式モデルと同一視しません。</span>';
    }
    drawing=true;
    try{
      let el=panel.querySelector('.be178-latest-parity');
      if(!el){el=document.createElement('div');el.className='be178-latest-parity';header.insertAdjacentElement('afterend',el);}
      if(el.innerHTML!==info)el.innerHTML=info;
    }finally{drawing=false;}
  }
  function start(){
    if(!document.getElementById('be178-style')){
      const st=document.createElement('style');st.id='be178-style';
      st.textContent='.be178-latest-parity{display:grid;gap:4px;margin:9px 0;padding:11px 12px;background:#f6f8fb;border:1px solid #dce3eb;border-radius:12px;color:#22394f;font-size:12px;line-height:1.55}.be178-latest-parity span{font-size:11px}.be178-latest-parity strong{font-size:11px}';
      document.head.appendChild(st);
    }
    render();
    if(typeof MutationObserver!=='undefined')new MutationObserver(()=>{if(!drawing)render();}).observe(document.body,{subtree:true,childList:true});
  }
  window.BoatEdgeV178={canonical,ranked120,stakeParity,preview,boundStatus,hashDerived,verifyRaw,isVerified,render};
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
