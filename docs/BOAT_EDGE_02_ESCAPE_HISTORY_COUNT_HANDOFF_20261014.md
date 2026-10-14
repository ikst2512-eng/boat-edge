# BOAT EDGE 02 | R01 実コース1逃げの過去母数生成 | 2026-10-14

Source of truth: root `BOAT_EDGE_02_RESEARCH_INBOX.md`, current verified blob `09ee4ba77e35a2495ff061a9f00ce1f036935526` (R01–R16). This task must **NOT** change that inbox, Track 01's main/workflows, Track 03 UI, or historical/formal result locks. PR #201 separately contributes source research and prospective source lists, so its content must not be reimplemented.

## Delivered (new, no duplication)

- `scripts/boat_edge_02_escape_history_count_adapter.py`: a **pure function** from caller-supplied, independently permission-approved historic course-1 NIGE events to 2nd/3rd joint counts. It uses no fetch/open/network/outcome endpoints. This is the missing **data-to-conditional-estimator** contract, not a second 20-way estimator.
- It strictly demands one dated unique race per record in sorted order, official **actual final course→boat permutation**, confirmed winning method `nige`, winner = actual course 1, complete six-boat finish permutation, stable six-racer and motor-epoch identity, source raw SHA and first-publication JST time, rights evidence and a Git-first-publication assertion. Invalid/missing data FAIL CLOSED.
- Extra hard bans: historic `2026-10-01`, `2026-10-05`, `2026-10-13` (known protected Formal dates) plus the complete *current* caller-supplied locked Formal date set. A dynamic source-of-truth gate must be checked by the eventual independent operator; strings asserted in fixture metadata never authorize actual reads.
- It aggregates NATIONAL → same VENUE → same VENUE and projected head RACER → same racer and motor **epoch**. Each subgroup retains its actual N, and the generated 2nd/3rd denominators agree. When a layer has no observations it is `None`, not fabricated zero data. If even the national historic NIGE cohort never observed a given second course, it refuses to hand unverifiable third-place conditionals to the current estimator.
- A matching integration-style synthetic test calls existing `scripts/boat_edge_02_escape_second_third_research.py` on the derived counts and verifies exactly 20 normalized boat triples under **predicted exhibition** mapping. Six boat identities are distinct. No 120-distribution or full-race forecast is claimed. 
- `tests/test_boat_edge_v236_02_escape_history_count_adapter.py`: fake-history-only checks for complete count agreement, time cutoff/rights, 20-way integration, historic Formal blocklist, non-escape method, actual-course vs 1号艇, corrupted finish, duplicate race, empty/sparse cohorts and missing feature exclusion. No real or protected event was read.

## Research-methodology caveats

1. This function checks the **shape and consistency of caller assertions**, NOT their truth. A fake `source_raw_sha256` or `training_data_first_git_server_time_jst` is NOT authenticated by this function. Before any real use, a separate operator must independently verify original bytes, licensing, Git first-commit timestamp and an immutable manifest, check sources' terms/rate limits, and exclude all protected Formal periods.
2. The algorithm uses conditional **historical actual entry**, but its next-race projection refers to an **exhibition** course order. It never implies the future final entry is known at freeze time. It never treats a boat-frame 1 win as proof of course-1 escape.
3. The current shrunk per-second `P(third|escape,second)` requires support for every second-course historical cohort in NATIONAL. A zero-support national cell is an explicit BLOCKER; no proxy/defaulting.
4. The motor layer is **same venue + same head racer + same motor assignment epoch**; it cannot be called a general motor effect, nor can the inferred association be called a causal racer/motor coefficient. Stratification power and prior strengths remain untested.
5. Historic model inputs and model outputs are not independent untouched Fresh. Historical calibration, Top3/5/10 improvement, and model promotion all require separately precommitted paired real race predictions with same model input, 10 tickets, after source rights are verified.
6. In the official V324 acceptance matrix, provider BOATERS and 競艇日和 raw verification remain **unverified**, and unlicensed automated collection stays forbidden. Other research lanes may be legal, but passing a fixture is never the V324 pass certificate. First-Git-server proof is owned by 01.

## Next acceptance checklist and ownership

- **02**: continue no-result ST distribution as-of proof, parent-vs-candidate 120/10 parity and individual R01 ablation; predeclare train/holdout windows and model IDs before any genuine prospectively frozen race. Don't apply weights to live site.
- **01**: verify permitted official historic data rights, provenance/immutability, and availability of actual entry + winner winning method + ordered finish in the official historical archive. Independently prove each source's raw SHA/first Git timestamp. Maintain current Formal lock and own merges and source writers. If permission is unresolved, **STOP**.
- **03**: only after future proven validation, display course1 escape world as conditional hypothesis; do not label `conditional_20` as a calibrated `P(3連単)`, and show missing-source and forecast-entry semantics accurately.

Current formal last reviewed snapshot as of `2026-10-13T23:59:44+09:00`: First100 0/100, results_seen/unlock/scoring=false. The snapshot is not evidence of present-day source availability. No outcome, payout or combined API accessed for this task.
