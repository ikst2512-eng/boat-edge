# BOAT EDGE 01 — V343 scheduled writer candidate classification

Date: 2026-10-13 JST. Integration owner: Track 01.
Source: actual `.github/workflows` files on base main `711da090e20d4d52703f7c8e35f1841abf74f7b2`.
Evidence manifest: `tests/fixtures/BOAT_EDGE_01_V343_REAL_WORKFLOW_CLASSIFICATION.json`.

## Scope and interpretation

V341 detects *possible* staging collisions among scheduled workflows with `contents: write`, from literal `git add` tokens. V343 **does not modify V341 or V299**. It classifies each candidate path witness as:

- `EXACT_PATH`: literal normalized staging paths exactly match.
- `LEFT_PARENT_OF_RIGHT`: left stages a directory containing the right path.
- `RIGHT_PARENT_OF_LEFT`: right stages a directory containing the left path.

Workflow pairs are reported as `EXACT_ONLY`, `PARENT_CHILD_ONLY`, or `MIXED_EXACT_AND_PARENT`. A shared textual prefix without a slash boundary is NOT containment. The report retains complete counts even when samples are limited to 12 witnesses per class and the first 100 pairs.

Actual tracked examples pinned by test:
1. `auto-update.yml` stages `data`; `site-odds.yml` stages `data/site_odds`: parent-child only.
2. `site-v133.yml` and `site-v134.yml` both stage `data/site_current_state.json`: exact only.
3. `site-v125.yml` and `site-v133.yml` both stage `BOAT_EDGE_CURRENT_TODO.md`: exact only.

The manifest records Git blob hashes for those five source workflow files at the observed baseline. The regression tests assert the *current source declarations and categories*, rather than comparing the entire workflow file byte-for-byte. Any meaningful staging-contract change that affects the pinned witnesses must be reviewed and explicitly rebaselined, not silently declared a duplicate.

## Safe checks

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_boat_edge_v299_workflow_inventory.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_boat_edge_v341_scheduled_writer_path_audit.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_boat_edge_v343_scheduled_writer_collision_classes.py' -v
PYTHONDONTWRITEBYTECODE=1 python3 scripts/boat_edge_v299_workflow_inventory.py
PYTHONDONTWRITEBYTECODE=1 python3 scripts/boat_edge_v343_scheduled_writer_collision_classes.py
```

Development CI executes the relevant suites and prints only a summary of V343 class counts. It does not invoke workflow writers or network collectors. Unresolved dynamic staging remains unknown. Directory containment can produce false-positive duplication candidates: **zero verified duplicate writers**, no assertion of simultaneous execution, no ownership transfer, no disabling or editing live collectors.

Only these paths are changed for V343: new script, test, evidence JSON, handoff note, Development CI invocation. No predictions, UI, sources, result files, payouts, Formal Fresh state, model adoption or production race-data writes. Separate main merge, Actions outcome and Pages deployment evidence must be observed and logged; a successful source-only audit does not by itself imply any runtime or accuracy result.
