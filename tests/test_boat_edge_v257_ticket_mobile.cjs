'use strict';
/* A22: Source-only presentation regression. Never reads results or formal data. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');

const source=fs.readFileSync('assets/boat_edge_v108.js','utf8');
const start=source.indexOf('function be140StakePlan(rows,total=10000){');
const end=source.indexOf('/* BOAT_EDGE_V181_FIRST_VIEW_IMMUTABLE_AND_FINAL_ONLY */',start);
assert(start>=0&&end>start,'read live V108 ticket presentation without changing logic');
const safe=s=>String(s).replace(/[&<>"']/g,'');
const ctx={Number,Math,Set,Map,pct:v=>String(v)+'%',esc:safe};
vm.runInNewContext(source.slice(start,end)+'\nglobalThis.ticket={be140StakePlan,renderTicketRows};',ctx);
const render=ctx.ticket.renderTicketRows;
const entries=[
 {combo:'1-2-3',p:65.2,odds:12.4},
 {combo:'3-1-2',p:34.8,odds:null}
];
const before=JSON.stringify(entries);
const plan=ctx.ticket.be140StakePlan(entries,10000);
assert.equal(plan.reduce((a,b)=>a+b,0),10000,'reference budget remains exactly 10000 yen');
const live=render(entries,null,false,null);
assert.equal(JSON.stringify(entries),before,'do not mutate ranked tickets');
assert(live.indexOf('1-2-3')<live.indexOf('3-1-2'),'preserve prediction order');
assert.equal((live.match(/data-be257-view="reference"/g)||[]).length,2);
assert.match(live,/aria-label="買い目順位 1"/);
assert.match(live,/現在の参考配分/);
assert.match(live,/的中時想定払戻/);
assert.match(live,/想定払戻：未確認（公式オッズ不足）/);
assert.match(live,/オッズ 未確認/);
assert(!live.includes('締切前の保存配分'),'reference stakes are not frozen stakes');

const frozen=[
 {combo:'1-2-3',p:40,odds:12.4,stake_yen:200},
 {combo:'3-1-2',p:20,odds:null,stake_yen:null}
];
const historical=JSON.stringify(frozen);
const completed=render(frozen,'1-2-3',true,1240);
assert.equal(JSON.stringify(frozen),historical,'never rewrite an immutable frozen ticket');
assert.equal((completed.match(/data-be257-view="frozen"/g)||[]).length,2);
assert.match(completed,/締切前の保存配分 200円/);
assert.match(completed,/買っていた場合の参考払戻 2,480円/);
assert.match(completed,/締切前の配分記録なし（過去の額は推定しません）/);
assert(!completed.includes('現在の参考配分'),'post-result rows cannot receive new stakes');
const payoutMissing=render([{combo:'1-2-3',p:1,odds:null,stake_yen:200}],'1-2-3',true,null);
assert.match(payoutMissing,/公式払戻未取得/);
assert(!payoutMissing.includes('想定払戻 0円'),'missing payout must not become zero or a guess');
const noSaved=render([{combo:'1-2-3',p:1,odds:null,stake_yen:null}],'1-2-3',true,1240);
assert(!noSaved.includes('2,480円'),'never reconstruct post-result stake');

const styles=fs.readFileSync('assets/boat_edge_v204_prediction.css','utf8');
assert(styles.includes('BOAT_EDGE_A22_TICKET_MOBILE_20261012'));
assert(styles.includes('grid-template-columns:27px minmax(0,1fr) minmax(82px,auto)'));
assert(styles.includes('.be257-ticket-combo'));
assert(styles.includes('.be140-ticket-money'));
const html=fs.readFileSync('index.html','utf8');
assert(html.includes('boat_edge_v204_prediction.css?v=204&amp;rev=244&amp;patch=247&amp;patch2=248&amp;patch3=250&amp;a22=1'));
console.log('A22_TICKET_MOBILE_SOURCE_ONLY_PASS: ordered tickets, 10000 reference budget, saved stakes, no invented payout');
