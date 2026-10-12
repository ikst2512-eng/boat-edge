'use strict';
/* A27: no result/payout/formal endpoint, paper ledger evidence only. */
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const w={},doc={hidden:false,querySelector(){return null},querySelectorAll(){return []},createElement(){return {style:{},dataset:{},classList:{toggle(){}},setAttribute(){},append(){},textContent:''}}};
let fetched=0;
vm.runInNewContext(fs.readFileSync('assets/boat_edge_v211_paper.js','utf8'),{
 window:w,document:doc,Number,Date,Math,Set,Map,JSON,
 fetch:async()=>{fetched++;throw Error('test has no network access')},
 setInterval(){},console
},{filename:'v262-paper-only.js'});
const api=w.BoatEdgeV211PaperEvidence;
assert.equal(typeof api.budgetAuditSummary,'function');
const now=Date.parse('2026-10-12T12:10:00+09:00');
function blank(){
 return {mode:'PAPER_ONLY',strategy_status:'CALIBRATION_GATE',
 money:{day:'20261012',virtual_only:true,daily_budget_yen:50000,
 today_spent_yen:0,today_remaining_yen:50000,today_paper_races:0,
 pending_yen:0,settled_stake_yen:0},recent_bets:[],
 scan:{as_of:'2026-10-12T12:05:00+09:00',skipped_by_reason:{'未見校正未完了':2}}};
}
const data=blank(),proof=api.paperEvidence(data,now),states=api.paperStates(data,proof),skips=api.skipEvidence(data.scan,proof,now);
assert.equal(proof.verified,true);
assert.equal(proof.current,true);
assert.equal(states.kind,'no-bet');
assert.equal(skips.verified,true);
const summary=api.budgetAuditSummary(data,proof,states,skips);
for(const word of ['紙上運用のみ（実購入0件）','本日の予算 50,000円','保存済み使用 0円',
  '残額 50,000円','仮想購入 0R','結果待ち投下 0円','結果確定投下 0円',
  '購入条件未達のため本日は見送り','未見校正未完了 2R','結果待ち分を利益に加算せず'])
 assert(summary.includes(word),word+' not visible in '+summary);
assert(!summary.includes('50,000円の利益'),'daily budget is NOT a return');
const after=blank();after.money.day='20261011';
const priorProof=api.paperEvidence(after,now);
assert(priorProof.verified&&!priorProof.current);
assert(api.budgetAuditSummary(after,priorProof,api.paperStates(after,priorProof),skips).includes('本日の資金・仮想購入・収益とは別'));
const invalid=blank();invalid.money.today_spent_yen=null;
const invalidProof=api.paperEvidence(invalid,now);
assert.equal(invalidProof.verified,false);
assert(api.budgetAuditSummary(invalid,invalidProof,{kind:'no-bet'},skips).includes('推定しません'));
const pending=blank();
pending.money.today_spent_yen=100;pending.money.today_remaining_yen=49900;
pending.money.today_paper_races=1;pending.money.pending_yen=100;
pending.recent_bets=[{state:'pending',decision_at:'2026-10-12T11:30:00+09:00',
 stake_yen:100,tickets:[{combo:'2-1-3',paper_stake_yen:100}]}];
const p=api.paperEvidence(pending,now),state=api.paperStates(pending,p);
assert.equal(state.kind,'pending');
const report=api.budgetAuditSummary(pending,p,state,api.skipEvidence(pending.scan,p,now));
assert(report.includes('保存済み使用 100円'));
assert(report.includes('残額 49,900円'));
assert(report.includes('結果待ち投下 100円'));
assert(!report.includes('仮想購入 0R'));
const broken={...pending,recent_bets:[{...pending.recent_bets[0],tickets:[]}]};
assert.equal(api.paperStates(broken,api.paperEvidence(broken,now)).kind,'unknown');
assert(api.budgetAuditSummary(broken,p,{kind:'unknown'},skips).includes('照合待ち'));
const html=fs.readFileSync('ai-simulation.html','utf8'),css=fs.readFileSync('assets/boat_edge_v262_budget.css','utf8');
assert(html.includes('id="simAuditBudget"'));
assert(html.includes('boat_edge_v262_budget.css?v=262'));
assert(html.includes('boat_edge_v211_paper.js?v=211&amp;rev=245&amp;patch=248&amp;patch2=250&amp;a27=1'));
assert(css.includes('BOAT EDGE V262 A27'));
assert.equal(fetched,1,'only prior initial read may occur, no new A27 fetch');
console.log('V262_A27_PAPER_50000_DAY_EVIDENCE_PASS');
