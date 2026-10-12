# BOAT EDGE 01 V338 — legacy scheduler closure, source-bound

Audit date: 2026-10-13 JST. Initial base main: `697c49ee816549e874270d3b9065cb7bd432cabe`.

## Evidence from GitHub-tracked state

- The recent V221 report at `data/site_ops_v221/workflow_dedup_current.json` has `checked_at=2026-10-12T20:50:25Z` and verifies all three target workflows `disabled_manually`: `auto-update-5min.yml`, `auto-update-v10.yml`, `site-v185-trigger.yml`.
- The first two workflow sources are already harmless manual-only legacy stubs; other similarly named ` 2.yml` copies are also manual-only stubs.
- Before V338, `site-v185-trigger.yml` was disabled at the GitHub Actions level, but its checked-in `workflow_run` dispatch code could restart if the workflow were reenabled.
- V221's historical daily schedule at `29 20 * * *` has no currently active target left to disable. Its own recent report states `disabled_this_run=0`; its pin checks for both old collectors are false. Its report is a narrow snapshot, not a global proof that all other writers are redundant.
- Primary live owners `auto-update.yml`, `BOAT_EDGE_V185_THIRD_ROLE_FRESH_CHALLENGER.yml`, `BOAT_EDGE_V200_SEQUENTIAL_FRESH_FREEZE.yml`, and `V235.yml` remain untouched.

## Changes and safeguards

- Replace the disabled V185 post-V133 dispatcher with a manual-only, no-write stub. This is a retirement of an already-disabled duplicate relay, **not** retirement of V185 itself.
- Remove V221's recurring and self-push triggers; keep explicit manual guarded recovery. Its code and pinned emergency implementation are unchanged.
- Extend `scripts/boat_edge_v299_workflow_inventory.py` protected retired-trigger list with six dormant workflows, now 24 in total. CI fails if any gains an automatic trigger. The V299 quoted-'`on`' parser fix from V337 remains necessary.
- Do not delete historical Git data, change site collector/parser, odds, prediction engine, source observations, formal Fresh flags, model weights or results.
- Scheduled contents-write inventory estimates are **candidates**; further dedup requires file-path ownership and proven replacements. CI/Pages success is not evidence of live-source coverage or accuracy.

## Release gates

Only integrate after PR Development CI has passed with the V299 guard; verify post-merge main Development CI and GitHub Pages separately. Do not claim Safari/device verification or a formal Fresh score from this work.
