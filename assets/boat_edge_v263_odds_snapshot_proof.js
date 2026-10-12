/* V263: verify byte-exact ORIGINAL stored official 120 trifecta odds at purchase-time freeze.
 * Read-only sidecar: never a current odds fetch, results, payouts or combined endpoint.
 * No model, stake, score or immutable prediction file is modified.
 */
(function(root){'use strict';
const KEY=/^20\d{6}-\d{2}-\d{2}$/;
const HEX=/^[a-f0-9]{64}$/;
const COMBOS=[];
for(let a=1;a<=6;a++)for(let b=1;b<=6;b++)for(let c=1;c<=6;c++){
 if(a!==b&&a!==c&&b!==c)COMBOS.push(a+'-'+b+'-'+c);
}
const EXPECTED=new Set(COMBOS);
const utc=s=>Date.parse(String(s||''));
function officialUrl(source,key){
 if(typeof source!=='string'||!KEY.test(String(key||'')))return false;
 const prefix='https://www.boatrace.jp/owpc/pc/race/odds3t?';
 if(!source.startsWith(prefix))return false;
 const q=source.slice(prefix.length);
 const vals={};
 for(const entry of q.split('&')){
  const pair=entry.split('=');
  if(pair.length!==2||!['hd','jcd','rno'].includes(pair[0])||
     Object.prototype.hasOwnProperty.call(vals,pair[0]))return false;
  vals[pair[0]]=pair[1];
 }
 if(Object.keys(vals).length!==3||!/^20\d{6}$/.test(vals.hd||'')||
    !/^\d{1,2}$/.test(vals.jcd||'')||!/^\d{1,2}$/.test(vals.rno||''))return false;
 const parts=key.split('-');
 return vals.hd===parts[0]&&Number(vals.jcd)===Number(parts[1])&&Number(vals.rno)===Number(parts[2]);
}
function inspect(key,snapshot,evidence,odds,sidecarSha){
 const bad=reason=>({state:'invalid',label:reason});
 if(!KEY.test(String(key||''))||snapshot?.race_key!==key||evidence?.race_key!==key||
    odds?.race_key!==key||!HEX.test(String(sidecarSha||''))||
    snapshot.odds_sha256!==sidecarSha||evidence.odds_sha256!==sidecarSha)
  return bad('保存オッズSHA・レース照合不一致');
 if(odds.schema_version!=='boat-edge-site-odds-v71'||odds.phase!=='PRE_RESULT_PURCHASE_ONLY'||
    odds.results_seen!==false||odds.scoring!==false||odds.verified_official_dom_v167!==true||
    !HEX.test(String(odds.raw_official_html_sha256||''))||
    odds.source!=='BOAT RACE オフィシャルウェブサイト 3連単オッズ'||
    !officialUrl(odds.source_url,key))
  return bad('公式オッズURL・DOM出典が未検証');
 const deadline=String(snapshot.deadline||'');
 if(!/^([01]\d|2[0-3]):[0-5]\d$/.test(deadline)||odds.deadline!==deadline)
  return bad('オッズ締切時刻の不一致');
 const due=Date.parse(key.slice(0,4)+'-'+key.slice(4,6)+'-'+key.slice(6,8)+'T'+deadline+':00+09:00');
 const fetched=utc(odds.fetched_at),saved=utc(snapshot.saved_at),proof=utc(evidence.odds_fetched_at);
 if(!Number.isFinite(due)||!Number.isFinite(fetched)||!Number.isFinite(saved)||
    !Number.isFinite(proof)||proof!==fetched||fetched>saved||saved>=due||
    saved-fetched>15*60*1000||saved-fetched<0)
  return bad('オッズ取得時刻・保存前後関係が不正');
 const rows=odds.trifecta_odds;
 if(!rows||typeof rows!=='object'||Array.isArray(rows)||
    Object.keys(rows).length!==120||odds.available_count!==120||odds.unavailable_count!==0||
    !Array.isArray(odds.unavailable_combinations)||odds.unavailable_combinations.length!==0||
    Object.keys(rows).some(k=>!EXPECTED.has(k))||
    COMBOS.some(k=>typeof rows[k]!=='number'||!Number.isFinite(rows[k])||rows[k]<=0))
  return bad('公式3連単120通りの取得・数値が不完全');
 for(const group of ['hit','balance','hole','narrow']){
  const tickets=snapshot.modes?.[group]?.tickets;
  if(!Array.isArray(tickets)||tickets.length<1)return bad('保存買い目が不足');
  for(const ticket of tickets){
   if(!EXPECTED.has(ticket.combo)||typeof ticket.odds!=='number'||
      !Number.isFinite(ticket.odds)||ticket.odds!==rows[ticket.combo])
    return bad('保存買い目と当時の公式オッズが不一致');
  }
 }
 return {state:'verified',label:'保存オッズ120通り・買い目倍率一致'};
}
function unavailable(reason){return {state:'unverified',label:reason||'購入前オッズの監査データ取得待ち'};}
async function verify(key,snapshot,evidence){
 if(typeof fetch!=='function'||!root.crypto?.subtle||typeof TextDecoder!=='function')
  return unavailable('オッズSHA照合機能を使用できません');
 const sha=snapshot?.odds_sha256;
 if(!KEY.test(String(key||''))||!HEX.test(String(sha||'')))return unavailable('保存オッズSHA未取得');
 const url='./data/site_prediction_snapshots/odds_v214/'+key+'-'+sha+'.json';
 let response;
 try{response=await fetch(url+'?v263='+Date.now(),{cache:'no-store'})}
 catch(_){return unavailable('保存オッズの通信失敗・未確認')}
 if(!response?.ok)return unavailable('保存オッズの公開待ち・未確認');
 try{
  const bytes=await response.arrayBuffer();
  const digest=await root.crypto.subtle.digest('SHA-256',bytes);
  const got=Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,'0')).join('');
  if(got!==sha)return {state:'invalid',label:'保存オッズのバイトSHA不一致'};
  const json=JSON.parse(new TextDecoder().decode(bytes));
  return inspect(key,snapshot,evidence,json,got);
 }catch(_){return unavailable('保存オッズのJSON・SHA照合不可')}
}
const exports={officialUrl,inspect,verify};
if(typeof module!=='undefined'&&module.exports)module.exports=exports;
if(typeof window!=='undefined')window.BoatEdgeV263OddsProof=exports;
})(typeof window!=='undefined'?window:{});
