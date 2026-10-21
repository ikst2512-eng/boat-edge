# BOAT EDGE — removal inventory (2026-10-21 JST)

**Scope:** verified source inspection of **all 28 scheduled-contents-write candidates** enumerated by the 2026-10-21 Development CI V299 inventory (96 workflow YAML files, 34 scheduled, 28 scheduled-write candidates at that point). After recent merged changes V167, V170 and V255 have **no schedule**, leaving **25 candidates from this historical list**. These are *static configuration counts*; not actual enabled workflow count, write collision count, or C-1 runtime proof. No workflow file or prediction evidence was deleted in this inventory.

## A. Automatic cron already removed (3; keep manual/event audit)

| Workflow | Reason | Verified current trigger |
|---|---|---|
| `BOAT_EDGE_V167_ONE_UPLOAD.yml` | V71 already verifies official odds; separate parity audit need not run hourly | push + manual; no cron |
| `BOAT_EDGE_V170_ONE_UPLOAD.yml` | post-settlement display report updates on V136 source push | push + manual; no cron |
| `v255-calibration-evidence.yml` | retrospective confidence evidence; code-change/manual verification retained | push + manual; no cron |

## B. High-priority *candidate* to reduce cron/merge writes (11; do not delete without dependency and consumer verification)

| Workflow | Current automatic schedule in source | Why investigate |
|---|---|---|
| `BOAT_EDGE_V155_DOWNLOAD.yml` | 4 pre-race daily slots | old prospective freeze/next-day score; compare ownership to V235/V234 |
| `BOAT_EDGE_V156_FRESH_WATCH.yml` | 2 daily slots | immutable-Fresh read-only watch; check if the write-enabled schedule is necessary |
| `BOAT_EDGE_V157_COVERAGE.yml` | 1 daily slot | prior-day historical coverage audit; compare existing read-only evidence |
| `BOAT_EDGE_V169_ONE_UPLOAD.yml` | 1 daily slot | venue display report; no source-change event hook other than self-file, so removing cron would stop refresh |
| `BOAT_EDGE_V171.yml` | 4 daily slots | research-only prospective venue mode; preserve any original future freeze evidence |
| `BOAT_EDGE_V173_ONE_UPLOAD.yml` | 1 daily slot | prior-day research-only tail/dispersion audit |
| `BOAT_EDGE_V219_AUTONOMOUS_VALIDATION.yml` | every 30 minutes | independent site validation, may be a candidate for read-only consolidation |
| `site-learning.yml` | twice hourly | learning/buy analysis; determine if actual site/mode consumer depends on generated output |
| `v236.yml` | every 5 minutes in grouped stagger | prospective shadow writer; check independence and downstream research evidence before retirement |
| `v241.yml` | hourly | readable verified-results/mobile-home report, V109 owns five-minute results; check presentation consumers and Pages |
| `v253-miss-attribution.yml` | four times an hour, selected hours | research miss-attribution, not first-Git source writer; check audits using its output |

## C. Needs especially careful owner/trigger reconciliation (9; likely important or protective)

| Workflow | Reason not to delete blindly |
|---|---|
| `BOAT_EDGE_V186_SCRATCH_FRESHNESS.yml` | scratch freshness producer; first-save source eligibility may rely on this |
| `BOAT_EDGE_V216_SOURCE_DIAGNOSTIC.yml` | high-frequency source-gap evidence; needed to distinguish official fetch vs freeze miss |
| `BOAT_EDGE_V220_AUTONOMOUS_SITE_OPERATIONS.yml` | recovery and site-operations guard, not yet proven replaceable |
| `V234.yml` | separately staggered first-save fallback and later results; critical until V235 takeover proved |
| `site-v125.yml` | revision-safe final-audit and ownership history |
| `site-v133.yml` | final-history owner for site presentation |
| `site-v136.yml` | mode-accuracy source for downstream V170 and reports |
| `v237.yml` | periodic health/obsolete worker retirement; check the recovery guard |
| `v392-preday-cards.yml` | early race-card publisher; verify UI/source consumer before trimming |

## D. Minimal source/first-freeze and results owners (5; protect until C-1 validated)

| Workflow | Ownership |
|---|---|
| `auto-update.yml` | official race card / beforeinfo inputs |
| `site-odds.yml` | official 120 trifecta odds |
| `BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml` | independent strict first-Git freeze + audit |
| `V235.yml` | main strict source-first prediction & receipt |
| `site-v109.yml` | existing five-minute results/payout source |

**28 = 3 already retired from scheduled execution + 11 candidate + 9 careful + 5 protected.** Review shortlist in `docs/C1_MINIMAL_CORE_MIGRATION.md` additionally protects site publish / read-only Actions evidence. An unscheduled workflow is **not** necessarily obsolete; it may be needed by push, manual recovery, PR CI, or workflow_run chains.

## E. Previously deleted workflow guards: 29 historical names

`BOAT_EDGE_V182_SCRATCH_AND_MIDODDS.yml`, `BOAT_EDGE_V231_BYTE_EXACT_PUBLISH.yml`, `site-v106.yml`, `site-v108.yml`, `site-v104.yml`, `site-v107.yml`, `site-v110.yml`, `site-v111.yml`, `BOAT_EDGE_site-v98.yml`, `BOAT_EDGE_site-v99.yml`, `site-v114.yml`, `site-v120.yml`, `site-v124.yml`, `site-v123.yml`, `site-v129.yml`, `site-v130.yml`, `site-v131.yml`, `site-v132.yml`, `BOAT_EDGE_V209_AI_AUTORUN_SIM.yml`, `BOAT_EDGE_V211_DAILY_50K_SIM.yml`, `BOAT_EDGE_V212_PAPER_SIM_INSTALL.yml`, `BOAT_EDGE_V213_SHADOW_ROI.yml`, `BOAT_EDGE_V214_ODDS_ARCHIVE_SHADOW.yml`, `site-health.yml`, `site-recovery.yml`, `site-v103.yml`, `v240.yml`, `v239.yml`, `BOAT_EDGE_V183_PROSPECTIVE_SCORE.yml`.

These are forbidden from reappearing by `scripts/boat_edge_v299_workflow_inventory.py`; presence absent was asserted by the observed Development CI. Not equivalent to 29 deletions made today.

## Other items still to inventory

Remaining workflows **outside** the 28 scheduled-write set (96 total at the 2026-10-21 snapshot) include manual, push/PR, workflow_run, scheduled read-only and other classes; absence of a scheduled contents-write permission does **not** establish safe removal. Scripts, UI assets, data snapshots, and test-file consumer graphs also require a separate exact file/path listing. No claim that all 96 workflow dependencies are cleared.

## Deletion admission rules

1. Enumerate the workflow's triggers and actual Git writes, consumer JS/UI/scripts, recovery ownership and historical data paths.
2. Preserve source fetch → strict 2–10m prediction → original first Git SHA/commit/receipt → results → Pages; never purge historical source/prediction/audit evidence.
3. Reversible PR for *one ownership boundary*; run existing CI immediately; if failure, repair relevant fixture or discard. Validate changed main and actual runtime, not merely tests.
4. **C-1 still unverified:** denominator independently eligible races; first Git save >=99% on three consecutive days. A cron or writer removed is not a verified success-rate improvement.
