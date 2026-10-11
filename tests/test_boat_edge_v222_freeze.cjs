'use strict';
const assert=require('assert'),fs=require('fs'),vm=require('vm');
const src=fs.readFileSync(process.argv[2]||'assets/boat_edge_v108.js','utf8');
const begin=src.indexOf('function saveFinalSnapshot('),end=src.indexOf('function isFinalSnapshot(',begin);
assert(begin>0&&end>begin,'final snapshot implementation missing');
const code=src.slice(begin,end);
assert(code.includes('V222_LOCAL_FINAL_IMMUTABLE'),'V222 immutable guard absent');
let stored=null,writes=0;
const ctx={Date,Object,Number,JSON,readLocal:()=>stored,snapKey:k=>k,
 writeLocal:(k,v)=>{writes++;stored=v;},
 be140StakePlan:()=>[10000],confidence:()=>70};
vm.runInNewContext(code,ctx,{filename:'v108-saveFinalSnapshot.js'});
const modes=Object.fromEntries(['hit','balance','hole','narrow'].map(k=>[k,[{combo:'1-2-3',p:20,odds:13.0}]]));
const source={meta:{venue:'唐津',race_no:1,deadline:'08:35'}};
const a=ctx.saveFinalSnapshot('20261011-23-01',source,{grade:'B'},modes,10);
assert.strictEqual(writes,1,'first prospective freeze must be saved');
const original=JSON.stringify(stored);
const changed=Object.fromEntries(['hit','balance','hole','narrow'].map(k=>[k,[{combo:'2-1-3',p:40,odds:5.0}]]));
const b=ctx.saveFinalSnapshot('20261011-23-01',source,{grade:'S'},changed,7);
assert.strictEqual(writes,1,'immutable frozen record must never be rewritten');
assert.strictEqual(JSON.stringify(stored),original,'frozen bytes changed');
assert.strictEqual(b,a,'existing frozen object was not returned');
stored={schema:'unknown',evidence:'keep'};const damaged=stored;
ctx.saveFinalSnapshot('20261011-23-01',source,{grade:'A'},changed,4);
assert.strictEqual(writes,1,'malformed existing evidence must fail-closed');
assert.strictEqual(stored,damaged,'malformed evidence should not be forged as a new freeze');
console.log('V222_CLIENT_FROZEN_FIRST_SNAPSHOT_AND_FAILED_CLOSED_PASS');
