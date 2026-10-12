'use strict';
/* V263: read ONLY immutable PRE_RESULT site snapshot, sidecar and audit files.
 * Never read results, payout or combined endpoint; no production-prediction changes.
 */
const assert=require('assert'),fs=require('fs'),path=require('path'),crypto=require('crypto'),vm=require('vm');
const lib=require('../assets/boat_edge_v263_odds_snapshot_proof.js');
const digest=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const ROOT=path.resolve(__dirname,'..');
const keys=['20261012-09-09','20261012-18-12','20261012-16-10'];
const combos=new Set();
for(let a=1;a<=6;a++)for(let b=1;b<=6;b++)for(let c=1;c<=6;c++)if(a!==b&&a!==c&&b!==c)combos.add(a+'-'+b+'-'+c);
assert.strictEqual(combos.size,120);
(async()=>{
 let passed=0;
 for(const key of keys){
  const snap=read(path.join(ROOT,'data/site_prediction_snapshots',key+'.json'));
  const evidence=read(path.join(ROOT,'data/site_autopilot/v229_evidence',key+'.json'));
  const sidecar=path.join(ROOT,'data/site_prediction_snapshots/odds_v214',key+'-'+snap.odds_sha256+'.json');
  const raw=fs.readFileSync(sidecar),odds=JSON.parse(raw);
  assert.equal(digest(raw),snap.odds_sha256,'byte exact original odds archive');
  assert.equal(lib.inspect(key,snap,evidence,odds,snap.odds_sha256).state,'verified');
  assert.equal(lib.inspect(key,snap,evidence,{...odds,source_url:odds.source_url.replace('boatrace.jp','boatrace.jp.evil.test')},snap.odds_sha256).state,'invalid');
  assert.equal(lib.inspect(key,snap,evidence,{...odds,available_count:60},snap.odds_sha256).state,'invalid');
  assert.equal(lib.inspect(key,snap,evidence,{...odds,verified_official_dom_v167:false},snap.odds_sha256).state,'invalid');
  assert.equal(lib.inspect(key,snap,evidence,{...odds,raw_official_html_sha256:null},snap.odds_sha256).state,'invalid');
  assert.equal(lib.inspect(key,snap,evidence,{...odds,results_seen:true},snap.odds_sha256).state,'invalid');
  assert.equal(lib.inspect(key,snap,evidence,{...odds,fetched_at:'2026-10-12T23:59:00+09:00'},snap.odds_sha256).state,'invalid');
  const first=snap.modes.hit.tickets[0];
  assert.equal(lib.inspect(key,snap,evidence,odds,'f'.repeat(64)).state,'invalid');
  assert.equal(lib.inspect(key,{...snap,modes:{...snap.modes,hit:{tickets:[{...first,odds:first.odds+.1}]}}},evidence,odds,snap.odds_sha256).state,'invalid');
  const partial={...odds,trifecta_odds:Object.fromEntries(Object.entries(odds.trifecta_odds).slice(0,60))};
  assert.equal(lib.inspect(key,snap,evidence,partial,snap.odds_sha256).state,'invalid');
  // Exercise actual async browser verification with immutable bytes and Node WebCrypto.
  const environment={
   window:{crypto:crypto.webcrypto},
   fetch:async url=>{
    assert(url.includes('/odds_v214/'+key+'-'+snap.odds_sha256+'.json?v263='));
    return{ok:true,arrayBuffer:async()=>raw};
   },
   module:{exports:{}},TextDecoder,Uint8Array,Date,Set,Number,Object,RegExp,Array
  };
  const script=fs.readFileSync(path.join(ROOT,'assets/boat_edge_v263_odds_snapshot_proof.js'),'utf8');
  vm.runInNewContext(script,environment,{filename:'V263_OFFLINE_SIDE_CAR'});
  const result=await environment.module.exports.verify(key,snap,evidence);
  assert.equal(result.state,'verified','browser crypto SHA and complete original 120 proof');
  passed++;
 }
 // Sidecar not served: do not call it a failed prediction; state is unverified.
 const snap=read(path.join(ROOT,'data/site_prediction_snapshots',keys[0]+'.json'));
 const evidence=read(path.join(ROOT,'data/site_autopilot/v229_evidence',keys[0]+'.json'));
 const environment={window:{crypto:crypto.webcrypto},fetch:async()=>({ok:false,status:404}),module:{exports:{}},TextDecoder,Uint8Array,Date};
 const script=fs.readFileSync(path.join(ROOT,'assets/boat_edge_v263_odds_snapshot_proof.js'),'utf8');
 vm.runInNewContext(script,environment);
 assert.equal((await environment.module.exports.verify(keys[0],snap,evidence)).state,'unverified');
 assert(!script.includes('data/site_results/'));
 assert(!script.includes('data/formal_predictions/'));
 console.log('V263_ARCHIVED_120_OFFICIAL_ODDS_FROZEN_TICKET_PARITY_PASS '+passed+'R / 120-combo / byte-SHA / async WebCrypto / fail-closed');
})().catch(err=>{console.error(err);process.exitCode=1});
