const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {webcrypto}=require('node:crypto');
const src=fs.readFileSync('assets/boat_edge_v178_verified_parity.js','utf8');
const win={};
const doc={readyState:'loading',addEventListener(){}};
const fake177={contractStatus:s=>s?.connected===true&&s?.predictions_ready===true&&
 s.guards?.results_seen===false&&s.guards.unlock===false&&s.guards.scoring===false&&s.guards.RESULT_UNLOCK_TOKEN===null&&
 typeof s.active_model_id==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(s.target_date),
 acceptRaw:(raw,k,s)=>Boolean(raw.formal_meta?.model_approved&&raw.formal_meta?.formal_gate_pass&&raw.formal_meta?.race_key===k&&raw.formal_meta?.model_id===s?.active_model_id),
 acceptNormalized:(race,s)=>Boolean(race.formal_meta?.model_id===s?.active_model_id)};
win.BoatEdgeV177=fake177;
vm.runInNewContext(src,{window:win,document:doc,crypto:webcrypto,TextEncoder,Uint8Array,console});
const v=win.BoatEdgeV178;assert.ok(v);
const combos=[];
for(let a=1;a<=6;a++)for(let b=1;b<=6;b++)for(let c=1;c<=6;c++)if(a!==b&&a!==c&&b!==c)combos.push(`${a}-${b}-${c}`);
const sum=combos.reduce((s,_,i)=>s+120-i,0);
const ranked_120=combos.map((combo,i)=>({combo,probability:(120-i)/sum}));
const derived={world_a:{probability:0.5,tickets:[{combo:combos[0],amount:5000}]},
 world_b:{probability:0.5,tickets:[{combo:combos[1],amount:5000}]},ranked_120};
const key='20261009-01-03';const shaPattern='a'.repeat(64);
const meta={schema_version:'boat-edge-formal-approved-overlay-v1',race_key:key,model_id:'V1.21.33',model_approved:true,formal_gate_pass:true,
 prediction_sha256:'',freeze_sha256:shaPattern,parent_sha256:shaPattern,
 guards:{results_seen:false,unlock:false,scoring:false,RESULT_UNLOCK_TOKEN:null},scope:'FORMAL_FRESH_APPROVED_PRE_RESULT'};
const status={connected:true,predictions_ready:true,active_model_id:'V1.21.33',target_date:'2026-10-09',formalParentSha:shaPattern,
 guards:{results_seen:false,unlock:false,scoring:false,RESULT_UNLOCK_TOKEN:null},approved_prediction_sha256_by_race:{}};
(async()=>{
 assert.equal(v.ranked120(derived).length,120);
 assert.equal(v.stakeParity(derived),true);
 assert.equal(v.stakeParity({...derived,world_a:{...derived.world_a,tickets:[{combo:combos[0],amount:100}]}}),false);
 assert.equal(v.preview(derived).top3.length,3);
 assert.equal(v.preview(derived).top5.length,5);
 assert.equal(v.preview(derived).top10.length,10);
 assert.equal(v.ranked120({...derived,ranked_120:ranked_120.slice(1)}),null);
 assert.equal(v.ranked120({...derived,ranked_120:ranked_120.map((x,i)=>i===1?{...x,combo:ranked_120[0].combo}:x)}),null);
 assert.equal(v.ranked120({...derived,ranked_120:[...ranked_120].reverse()}),null);
 const hash=await v.hashDerived(derived);assert.match(hash,/^[a-f0-9]{64}$/);
 meta.prediction_sha256=hash;status.approved_prediction_sha256_by_race[key]=hash;
 const raw={derived,formal_meta:meta};
 assert.equal(await v.verifyRaw(raw,key,status),true);
 assert.equal(v.isVerified({race_key:key,derived,formal_meta:meta},status),true);
 assert.equal(v.isVerified({race_key:key,derived:{...derived},formal_meta:meta},status),false);
 assert.equal(await v.verifyRaw({...raw,derived:{...derived,world_a:{probability:0.5,tickets:[{combo:combos[2],amount:5000}]}}},key,status),false);
 assert.equal(await v.verifyRaw(raw,key,{...status,approved_prediction_sha256_by_race:{}}),false);
 assert.equal(await v.verifyRaw(raw,key,{...status,connected:false}),false);
 assert.equal(await v.verifyRaw(raw,key,status),true);
 assert.equal(v.isVerified({race_key:key,derived,formal_meta:meta},{...status,active_model_id:'Other'}),false);
 const index=fs.readFileSync('index.html','utf8');
 assert.equal((index.match(/BoatEdgeV178\?\.verifyRaw\?\.\(/g)||[]).length,1);
 assert.equal((index.match(/BoatEdgeV178\?\.isVerified\?\.\(/g)||[]).length,1);
 assert.equal((index.match(/boat_edge_v178_verified_parity\.js\?v=178/g)||[]).length,1);
 console.log('V178_JS_SHA_BOUND_RANK120_APPROVAL_AND_NEGATIVE_TESTS_PASS');
})().catch(e=>{console.error(e);process.exit(1)});
