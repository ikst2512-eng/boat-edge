# BOAT EDGE — C-1 minimal core migration

Goal: verified first Git-add prediction 2–10 minutes before deadline for >=99% of eligible races on three consecutive race days. Free infrastructure only.

## Four functional stages

1. **Official inputs**: `.github/workflows/auto-update.yml` (race card / beforeinfo) and `.github/workflows/site-odds.yml` (official trifecta odds). Preserve original PRE_RESULT HTML, SHA, scratches and 120/120 odds.
2. **Prediction**: retain the pinned existing site-only engine; no retraining, model rewrite, or payout/formal reads.
3. **Strict first freeze + Git proof**: `.github/workflows/V235.yml` (official refresh, strict V229 call, first Git push, receipt) and `.github/workflows/BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml` (independent strict V229 first-freeze wake). Both invoke the **same** `scripts/boat_edge_v229_atomic_freeze.py`; never introduce a second eligibility authority.
4. **Display + independent audit**: `.github/workflows/pages-controlled-publish.yml` and read-only `.github/workflows/boat-edge-v350-actions-evidence.yml`.

These six are a **review shortlist**, not a verified exhaustive dependency graph or permission to delete all other workflows.

## Migration order (fail closed)

- Inventory every workflow's actual `schedule`, `workflow_run`, `push`, `workflow_dispatch`, `repository_dispatch` and callers before retiring it.
- Check active site publication, tests and upstream producers before any deletion. A workflow with no schedule may still be a required `workflow_run` producer, UI deploy or CI gate.
- Preserve the old production path while testing a new consolidated entry point. Never run two concurrent first-writers without the existing shared concurrency / immutable-first-add guards.
- Compare per-race official source, first Git receipt, deadline and audit for at least three days. Only after >=99% verified may redundant triggers be disabled and obsolete workflow files removed in small reversible PRs.
- No historical backfill, no fabricated first-save time, no relaxation of 2–10 minute rule, no paid services.

## Immediate operating rule

Prioritize C-1 first. Avoid new V-numbered one-off workflows, duplicate collectors and parallel prediction engines. Every change must state which of the four stages it changes, how it preserves official evidence, and how to roll back.
