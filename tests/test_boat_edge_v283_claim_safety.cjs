'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync('autopilot.html','utf8');
assert.equal((html.match(/id="be283Evidence"/g)||[]).length,1);
assert(html.includes('GitHub Actions PASS・Pages SUCCESS'));
assert(html.includes('予想の的中率改善は未証明'));
assert(html.includes('正式Fresh'));
assert(html.includes('json(\'data/formal_status.json\').catch(()=>null)'));
assert(html.includes("put('be283Evidence',liveFormalClosed?"));
assert(html.includes("put('be283Evidence','監査データ未確認"));
assert(html.includes("g.RESULT_UNLOCK_TOKEN===null&&formalNow?.formalFirst100?.races===0"));
assert(!html.includes('正式Fresh100合格'));
const inline=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)]
   .map(x=>x[1]).filter(x=>x.trim());
assert(inline.length>0);
for(const code of inline)new vm.Script(code);
console.log('V283_ACTIONS_NOT_PROOF_AND_FORMAL_FAIL_CLOSED_PASS');
