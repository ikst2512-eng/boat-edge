# BOAT EDGE CURRENT TODO

Updated: 2026-10-08
This file is auto-reconciled from repository evidence by V134. ACTIVE TODO contains unresolved work only.

## CURRENT
- UI: V133-BALANCE10-WAVE12-15-18-FIXED
- Latest prediction policy: V127 + V133 mode policy ACTIVE
- FINAL_15M server generator: V133 ACTIVE
- Revision-safe audit evidence: V125 + V134 reconciler
- Browser/server parity: V133 PASS
- TODO evidence reconciler: V134 ACTIVE
- Formal CURRENT connected: false
- Formal predictions_ready: false
- Formal stage: 2026-10-08 PRE_RESULT / 5ソース待ち
- Formal guards: results_seen=false / unlock=false / scoring=false

## ACTIVE TODO — priority order
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
- Odds never rank tickets and never decide mode ticket counts.
- Scenario accuracy is primary; 波乱展開 may use up to 18 tickets when head scenarios genuinely split.

## RECENT DONE
- [x] Live mode counts confirmed — balance=10 / wave=[12, 15, 18] / narrow=3; V133 parity PASS.
- [x] V133-mode settled judgement path confirmed — `20261008-03-01` / ✕ miss path.
- [x] Live V133 FINAL_15M snapshot + audit PASS — `20261008-03-01`.
- [x] V133 browser/server parity PASS for all four prediction modes.
- [x] V133 mode policy fixed at 的中重視10 / バランス10 / 波乱12・15・18 / 激絞り3.

## TODO EVIDENCE
- Machine-readable evidence: `data/site_todo_evidence.json`.
- Current V133 snapshots observed: 62.
- Current V133 audited PASS: 59.
- Observed wave counts: [12, 15, 18].
- Current V133 settled races: 51.

## TODO GUARD
- ACTIVE TODO contains unfinished `[ ]` tasks only.
- Evidence-complete tasks are removed from ACTIVE and written to RECENT DONE automatically.
- Component versions must match `data/site_current_state.json`.
- Legacy NEXT sections are forbidden.
