# BOAT EDGE 02 | PR #201 merged addendum × INBOX × current TODO | 2026-10-14 JST

This is a Track-02-only **research audit and hypothesis registration**. It does **not** check any protected result, set any Fresh flag, access BOATERS/競艇日和 private numeric tables, scrape commercial sites, change the production ranker, publish Pages, or claim accuracy gain.

## Pinned sources / merge status

- Original `BOAT_EDGE_02_RESEARCH_INBOX.md` main Git blob `09ee4ba77e35a2495ff061a9f00ce1f036935526`; entries R01–R16 already reconciled with V148–V154, V180/V185/V199, V360–V370 and PR #192 in `docs/BOAT_EDGE_02_INBOX_SYNC_20261013.md`. Do **not** duplicate these.
- PR #201 **merged**, 02 handoff: `docs/BOAT_EDGE_02_RESEARCH_ADDENDUM_20261014.md`, blob `22342f6f5e51df74038e48083e870f3c4d9a1919`. The 01/03 documents belong to the respective tracks, not 02.
- Existing `BOAT_EDGE_MASTER_TODO.md` P1 T07/T09/T10/T11/T12/T13 and `BOAT_EDGE_CURRENT_TODO.md` accuracy items remain incomplete. This research PR does **not** mark them done.
- Existing production `data/site_prediction_policy.json` explicitly labels full calibrated 120 as absent. Its model/odds ranking must not be modified by a research PR.

## Genuine incremental gaps, deduplicated

| New finding from PR #201 | Existing coverage | Added work or evidence blocker | Research priority |
| --- | --- | --- | --- |
| びわこ公式「枠番別コース取得率」 | V360 maps one **already known provisional exhibition permutation** into 120; V317 mapping / V311 source validation already exist | **NEW #192 experimental kernel** estimates complete six-boat joint entry distributions over **720 distinct permutations** from *fully authorized* historical 6×6 counts; **not** a duplicate of V360. Real count original bytes, venue coverage, cohort denominator and rights still absent. | P1, source-gated |
| 1M攻撃/抵抗, attackers 3/4, beneficiaries 5/6 | V151–V154 retrospective world/wall shadow already exist | No actual licensed 1M labeled observations. Register ontology and source permission; do not create another V154. | P2, blocked |
| 児島×潮位×風 / JMA 10-min data | `site_prediction_policy.json` already TODO for wind/tide, no verified complete match | New **as-of availability** ledger per observation; location/clock/QC, measurement issued before freeze, no retrospectively revised tides as future LIVE. No coefficients before matched race evidence. | P2, blocked |
| BOATERS 先頭艇別2着 | V148 conditional tails and V180/V185, #192 course1 nige joint counts | Different conditioning labels; provider output not copied. Continue authorization-verified **historical actual course1 逃げ** training and equal-ten candidate. | P1, data not authorized |
| Commercial originals and timing availability | V185/V199 relative original-exhibition research + V311/V324 requirements | Record `provider`, `venue`, measurement lap, observed 6/6, missing reason, first seen and use permission; providers are **republishers**, not independent sensors. Never fill missing race time. | P2, blocked |
| Full 120 and Top3/5/10 calibration | V360 provides three 120 **relative masses**; #192 hierarchical 120 and equal-ten contract are synthetic | Real matched race / source and predeadline Git immutability, multi-day untouched holdout + separate authorized scoring are still unverified. No numeric gain claimed. | P0 acceptance gate |

## New P1 joint-entry kernel — safety and semantics

File: `scripts/boat_edge_02_joint_entry_permutation_research.py` + `tests/test_boat_edge_v236_02_joint_entry_permutation.py` (15 fabricated-input tests). It accepts only 6×6 **integer observed counts**, indexed by **BOAT FRAME** and *historical official actual course* for one venue and fixed historic training period. Same-race event denominator must be identical across all six rows AND six columns; otherwise it rejects instead of assuming independent row datasets share population. Missing entries fail closed. All training ends strictly before target. Each row sum and each course column sum must equal a **verified historical event N >= 30** (this is a code threshold, not a claim of statistical sufficiency). The count SHA is recomputed; rights, source-first-seen and authorization SHA are still **self-reported**.

For a 6-boat frame-to-course assignment π, the **uncalibrated research score** is proportional to the product of six within-frame historical conditional course frequencies, *restricted to valid permutations*. Normalize over 720 assignments. This is an independence *hypothesis conditioned on the permutation constraint*, not a claim real entrants independently select courses; player front-loading and mutual interference are future candidate interaction effects. Output 720 combos and boat-course marginals that must each sum to 1, with 6-course occupancy marginals also equal to 1. Any observed 0 count may cause a 0 research mass, **not proof the outcome is physically impossible**. Sparse historic strata require new analysis and validation.

The びわこ **2026-07-01–09-30** public percentage summary (including 6枠→6コース90.9%, 6枠→5コース5.5%) is **NOT consumed** as this model's input, because rounded percentages don't provide a fully audited 6×6 integer event cohort, are site-specific, and their AI-learning permission has not been verified. Independent official source: https://www.boatrace-biwako.jp/modules/datafile/?kind=course&page=index_datacourse . Provider page availability alone is not training authorization.

### Why this can help TopK only AFTER validation

Entry uncertainty could reorder head / second / third if 1/2-wall or 3/4 attack changes with entry. But this kernel produces 720 **entry scenarios**, not 120 **trifecta outcome probabilities**. To challenge V360 fairly, an operator would need to produce a separate predeclared future-only **entry-marginalized 120-way** model using already defined per-entry conditional outcome model, immutable per-race official beforeinfo and permission-reviewed historical course counts. No result-based choice of the six permutations, no odds multiplier, no missing-value imputation or moving training window post-event. Freeze exactly the same race's parent & candidate full 120, each 10 tickets, with trusted first Git commit and same source SHA; compare head, Top3/5/10 and log loss/Brier (proper calibration sample only) on a sufficiently large multi-day unseen cohort, keeping day and venue sample N/uncertainty.

The CURRENT site is *not* updated. Until this experiment actually outperforms on untouched future trials, its `production_eligible=false` status remains binding.

## Follow-on ownership

**02**: after rights review, individually test (a) observed entry transition prior, (b) course1 nige conditional second and third, (c) ST history; ablate them independently to avoid crediting a combined change to the wrong input. Preserve research code/model version/condition and report zero evidence as zero observed, missing as missing. No authorized real input has been collected as part of this PR.

**01**: independent permission/legal source ledger, source snapshot first Git SHA, no concurrent shared writers, PR #192 code review/merge eligibility and actual site integration **only after statistical promotion decision**.

**03**: no label of calibrated head or Top3/5/10 confidence from 720-way rank weights; display predicted vs actual entry status, eligibility, missingness, model ID and the verified source's as-of clock only after authorized production promotion.

**Formal gate:** Source snapshot last inspected `data/formal_status.json` `asOf=2026-10-13T23:59:44+09:00`, First100 `0/100`, `results_seen/unlock/scoring=false`, token null. Do not treat the historical source timestamp as live status. No Formal result endpoints, pages, payout or combined API opened.
