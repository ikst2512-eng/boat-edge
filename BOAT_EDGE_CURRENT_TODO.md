# BOAT EDGE CURRENT TODO

Updated: 2026-10-08
This is the live execution list. Historical items are archived separately.

## CURRENT
- UI: V130-ADAPTIVE-WAVE-HIT-TODO-FIXED
- Latest prediction policy: V127 + V129 adaptive wave ACTIVE
- FINAL_15M server generator: V130 ACTIVE
- Revision-safe audit: V125 ACTIVE (schedule fallback)
- Browser/server parity: V130 PASS
- Formal CURRENT connected: false
- Formal predictions_ready: false
- Formal stage: 2026-10-08 PRE_RESULT / 5ソース待ち
- Formal guards: results_seen=false / unlock=false / scoring=false

## ACTIVE TODO — priority order
1. [ ] First live V130 FINAL_15M snapshot on 2026-10-08 and V125 audit PASS.
2. [ ] Confirm first settled race shows `🎯 的中`, `✕ 不的中`, or `判定対象外` directly in prediction panel.
3. [ ] Validate live 波乱展開 count is 8 or 10 and browser/server saved ticket order is identical.
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
- Scenario accuracy is primary; genuine split/rough races may use up to 10 tickets.

## RECENT DONE
- [x] V127 excluded missing avg_st instead of treating null as zero.
- [x] V126 recheck after V127 fix passed all four fixed real-race fixtures during V128 run.
- [x] V130 波乱展開 changed from sparse alternate-head-only selection to adaptive 8〜10 scenario coverage.
- [x] V129 keeps 🎯 judgement status visible before and after result settlement.
- [x] V129 rebuilt TODO as CURRENT / ACTIVE / WAITING / RECENT DONE.

## TODO GUARD
- ACTIVE TODO contains unfinished tasks only.
- Completed work moves to RECENT DONE.
- Component versions must match data/site_current_state.json.
- Legacy NEXT sections are not allowed.

- [x] V130 fixes V129 regression harness by extracting be129WaveRows before parity execution.
