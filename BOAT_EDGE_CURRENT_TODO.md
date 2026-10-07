# BOAT EDGE CURRENT TODO

Updated: 2026-10-08
This is the live execution list. Historical items are archived separately.

## CURRENT
- UI: V133-BALANCE10-WAVE12-15-18-FIXED
- Latest prediction policy: V127 + V133 mode policy ACTIVE
- FINAL_15M server generator: V133 ACTIVE
- Revision-safe audit: V125 ACTIVE (schedule fallback)
- Browser/server parity: V133 PASS
- Formal CURRENT connected: false
- Formal predictions_ready: false
- Formal stage: 2026-10-08 PRE_RESULT / 5ソース待ち
- Formal guards: results_seen=false / unlock=false / scoring=false

## ACTIVE TODO — priority order
1. [ ] First live V133 FINAL_15M snapshot on 2026-10-08 and V125 audit PASS.
2. [ ] Confirm first settled race shows `🎯 的中`, `✕ 不的中`, or `判定対象外` directly in prediction panel.
3. [ ] Validate live バランス=10点 and 波乱展開=12/15/18点, with browser/server saved ticket order identical.
4. [ ] Connect racer×actual-course 1y/6m/3m.
5. [ ] Connect 1-course escape resistance + 2-course wall/逃がし interaction.
6. [ ] Connect 3/4 attack boat -> 5/6 beneficiary interaction.
7. [ ] Connect motor recent-meet/current-meet/parts-change state.
8. [ ] Connect venue×season/wind/tide/course and same-day completed-race LIVE water state.
9. [ ] Formal latest prediction: audit original exhibition against both BOATERS + 競艇日和 before claiming retrieved.

## WAITING / GATES
- Formal CURRENT cannot replace reference prediction until predictions_ready=true and PRE_RESULT guards are valid.
- No retrospective prediction backfill after results are known.
- Missing values are not replaced with zero, mean, or proxy.
- Odds never rank tickets and never decide 波乱展開 point count.
- Scenario accuracy is primary; 波乱展開 may use up to 18 tickets when head scenarios genuinely split.

## RECENT DONE
- [x] V133 fixes the only V132 parity mismatch: balance-mode alternate-head reference now uses the normal top-ticket head on both browser and server.
- [x] V133 keeps 的中重視=10 / バランス=10 / 波乱=12・15・18 / 激絞り=3.
- [x] V132 バランス is 10 tickets: top 7 probability + up to 3 alternate-head/scenario tickets, then probability fill.
- [x] V132 retains V131 wave design: dedicated 20-candidate pool with 12 / 15 / 18 tickets.
- [x] V132 fixes V131 synthetic 12-ticket regression data so the test pool has at least 12 unique candidates.
- [x] V127 excluded missing avg_st instead of treating null as zero.
- [x] V126 recheck after V127 fix passed all four fixed real-race fixtures during V128 run.
- [x] V131 波乱展開 uses a dedicated 20-candidate pool and adaptive 12 / 15 / 18 scenario coverage.
- [x] V129 keeps 🎯 judgement status visible before and after result settlement.
- [x] V129 rebuilt TODO as CURRENT / ACTIVE / WAITING / RECENT DONE.

## TODO GUARD
- ACTIVE TODO contains unfinished tasks only.
- Completed work moves to RECENT DONE.
- Component versions must match data/site_current_state.json.
- Legacy NEXT sections are not allowed.

- [x] V130 fixes V129 regression harness by extracting be129WaveRows before parity execution.

- V109 replaces the legacy result collector without changing V108 UI.

- V109 treats confirmed + payout null as incomplete and refetches it.

- V109 payout parser supports ¥ / ￥ / 円.

- V109 backfills historical confirmed payout gaps from 2026-10-07.

- V109 keeps result/trifecta data factual; missing payout is never fabricated.
