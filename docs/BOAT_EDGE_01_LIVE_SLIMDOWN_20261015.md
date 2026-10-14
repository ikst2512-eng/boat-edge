# BOAT EDGE 01 — 2026-10-15 live workflow slimdown and research conflict handoff

Scope: **production-safe scheduling/staging cleanup**. This is not a replacement site or a prediction-model change.

## Checked live ownership and bounded actions

| Workflow | Evidence before cleanup | Action | Kept operational |
| --- | --- | --- | --- |
| `v238.yml` | Hourly cron **plus** workflow_run on each successful V235 run; rewrites diagnostic report and source assets in main | Remove workflow_run fanout | Existing hourly diagnostic, manual dispatch and existing code |
| `v241.yml` | Hourly cron **plus** workflow_run on each V235 success; can stage `index.html` and `results.html` | Remove workflow_run fanout | Hourly verified UI/results report, manual dispatch; five-minute V109 results remain primary |
| `site-v109.yml` | Scheduled results commits also stage `BOAT_EDGE_CURRENT_TODO.md` alongside results/archive; V125 independently stages the same TODO | Restore local unowned TODO edit before commit/rebase; stage results and archive only | Five-minute verified result and payout collection and archive retention unchanged |
| `site-v125.yml` | Revision-safe FINAL_15M audit stages `BOAT_EDGE_CURRENT_TODO.md` | Keep as sole scheduled TODO writer from these two | Existing immutable audit output and live schedule |

## Preserved to avoid data loss or formal leakage

- `auto-update.yml` official PRE_RESULT input, `site-odds.yml` 120 odds, V186 scratch, V228 independent first-freeze, V229 Git-first-add audit, V235 immutable prospective freeze, V133 FINAL history, V125 audit, V109 results, V136 reference post-settlement report, V220 recovery, V237 monitoring, V251 legacy Pages recovery: **do not blindly retire**.
- Read-only 03 mobile browser E2E and 01 controlled Pages verification are not prediction-model evidence.
- Formal status was independently read on 2026-10-15 JST: `formalFirst100.races=0`, `results_seen=false`, `unlock=false`, `scoring=false`, token null. This cleanup never reads formal results/payout, writes frozen snapshots, promotes model weights or unlocks any result gate.
- `BOAT_EDGE_MASTER_TODO.md` is user-maintained; its completion checkmarks are not replaced by auto-generated `BOAT_EDGE_CURRENT_TODO.md`.

## Outstanding blockers, separately owned

1. **Track 02 PRs #192 and #253 conflict**. Both modify `scripts/boat_edge_v301_paired_evidence.py` and `tests/test_boat_edge_v236_v301_paired.py`; both are dirty against current main. Preserve research on their branches, but do **not** merge either wholesale. 02 should extract the nonoverlapping candidates, reconcile V301/test changes against current main, and present one small research-only PR, without production model promotion.
2. **Pages deployment source remains unverified**: existing `pages-controlled-publish.yml` explicitly gates direct publishing on GitHub Pages `build_type=workflow`; observed successful run 38607339505 had `build` and `deploy` **skipped**, so this does not prove Actions-mode publishing. Legacy Pages deployments also show cancellations. Switching repository Pages source requires a separate explicitly confirmed setting change; do not disable V251 recovery until the new source actually publishes exact staged SHA.
3. Other static path overlaps, e.g. V125/V229 under `data/site_prediction_audit/` and V133/V228 under snapshots, require per-file live evidence and consumer tracing, not retirement solely on directory containment. They remain distinct source/audit jobs; actual duplicate same-race writes are not yet proved.

## Regressions / acceptance

The existing Development CI invokes `tests/test_boat_edge_v342_retired_schedulers.py`; extend it to assert both diagnostic workflows have **no V235 event fanout**, and V109 is not a second TODO stager. Keep V125 as audit TODO owner.

Completion sequence: dedicated branch → fixture-only CI → 01 merge with expected PR head → main CI and scheduled run checks → Pages exact SHA when source configuration permits. A green CI does not establish improved TopK accuracy or physical iPhone Safari acceptance.

If any publisher or source coverage regresses, the workflow changes can be reverted independently without touching prediction data or Formal Fresh.
