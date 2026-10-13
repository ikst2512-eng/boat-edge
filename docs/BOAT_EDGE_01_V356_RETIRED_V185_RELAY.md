# BOAT EDGE 01 V356 — Retire dormant V185 relay without touching live source owners

Audit date: 2026-10-13 JST. Branch base main: `de6ad6ea4f2ee214e58d3cfeffd6df43fad7278b`.

## Observed evidence, not assumptions

- `data/site_ops_v221/workflow_dedup_current.json` recorded `site-v185-trigger.yml` as `disabled_manually` on 2026-10-12T20:50:25Z. It is a historical source-bound observation, **not** an independently confirmed current GitHub enablement state.
- Its repository file still contained a `workflow_run` trigger after V133 success, a curl dispatch of V185, and `actions: write` permission. If later enabled, that dormant relay could duplicate the independently scheduled V185 research path.
- Observed a successful scheduled V185 run (GitHub run 38414462101) on 2026-10-13. This establishes a separate V185 scheduled owner existed at audit time. It does **not** establish that all intended event-driven captures are replaceable.
- V221 itself is already manual-only on main; the older PR #154 cannot safely replace the newer main inventory/tests. Four other legacy auto-update stubs are also already manual-only.
- Neither an absolute duplicate-write count nor a real-world source-coverage impact is established by this audit.

## Narrow change

1. Replace **only** dormant `site-v185-trigger.yml` with a manual, read-only no-op tombstone, preserving the scheduled and manual V185 owner unchanged.
2. Extend V299 guard for four already-retired legacy collector stubs, dormant V185 relay and already-retired V221 cleanup; automatically fail CI if any is reactivated.
3. Add a fixture regression checking that the retired relay cannot dispatch or write.
4. No change to site data, races, official/B O A T E R S sources, BOATERS, prediction model, odds, formal Fresh, scoring, payout or GitHub Pages content.

## Nonclaims and release gates

- No formal First100 unlock, results access, model promotion, actual duplicate-commit proof or fresh-data coverage claim.
- The old relay was a dormant, possibly disabled workaround; it is retired to remove accidental reactivation risk, not because data/accuracy parity has been proven.
- Require PR Development CI V299 guard, then main CI and exact SHA Pages success. Safari/browser acceptance remains separate.
