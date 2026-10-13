# BOAT EDGE 01 V356 — narrow retired-workflow reconciliation

Date: 2026-10-13 JST. Based on current main `de6ad6ea4f2ee214e58d3cfeffd6df43fad7278b`.

## Original evidence and decision

- Prior PR #154 was closed without merge; it was authored against a much older main.
- Main already keeps `.github/workflows/BOAT_EDGE_V221_GUARDED_DEDUP.yml` manual-only. Do not replay its obsolete diff.
- The historical `data/site_ops_v221/workflow_dedup_current.json` reports `site-v185-trigger.yml` `disabled_manually` as of 2026-10-12T20:50:25Z. This is a dated observation, not proof of its live current status.
- Before this change, the checked-in `site-v185-trigger.yml` still had `workflow_run` and `actions: write`, potentially redispatching V185 on reactivation after V133 success.
- Replace that *old relay* with a harmless manual-only read-permission tombstone. Do **not** disable `BOAT_EDGE_V185_THIRD_ROLE_FRESH_CHALLENGER.yml`, live V200/V235, primary update/odds/source collectors or any prediction pipeline.

## Prevent regression

- Add the old relay, V221, and four already-manual old updater files to the V299 explicit-retirement regression list (6 paths).
- Test exactly manual-only `workflow_dispatch`, no dispatch API call, no `workflow_run`, and no write permission on the retired relay.
- V299's scheduled contents-write count is a **candidate inventory**, not measured duplicate output or proof a job can safely be removed.
- This change does not touch any data file, formal Fresh state, prediction weights, scored results or odds; formal unlock remains outside scope.

## Release gates

- Require PR CI, main CI, and Pages success on an exact SHA. A green CI does not prove real Safari rendering, source completeness, Fresh accuracy or profitable betting.
