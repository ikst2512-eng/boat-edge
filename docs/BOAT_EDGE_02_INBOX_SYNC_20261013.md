# BOAT EDGE 02 — authoritative latest research INBOX reconciliation (2026-10-13 JST)

**Source of truth read:** repository default-branch `BOAT_EDGE_02_RESEARCH_INBOX.md`, exact Git blob SHA **`09ee4ba77e35a2495ff061a9f00ce1f036935526`**, 5,782 UTF-8 characters. This file appeared on main after draft #192's branch was cut, and is NOT present on this research branch; this synchronization note is pinned to the main blob rather than assuming a missing branch copy means the inbox did not exist. Do not edit/overwrite the inbox itself on this research PR. On later review, re-fetch main inbox, compare hash and reconcile newly added R IDs before merge.

## R01–R16 map: avoid implementing the same feature twice

| ID | Disposition vs actual repository research | Delta ONLY / readiness |
| --- | --- | --- |
| R01 逃がし2着率 | V148 and V180 already have conditional tails; #192's new `boat_edge_02_escape_second_third_research.py` isolates **historical actual course 1 + confirmed 逃げ**, not boat-1 win | NEW isolated conditional-20 kernel with evidence and same-cohort denominator check; historical permission, source raw bytes and fresh pre-race input remain UNVERIFIED. For any racer/venue strata, denominator = observed COURSE-1 NIGE cohort for that exact subgroup; never divide distinct populations. |
| R02 1M resistance/attack | V151–V154 historical wall/attack proxies exist | NEW explicit 1M action labels and legal video/event source are missing. NO new numerical model without observed labels. |
| R03 slow/dash player choice | V148 actual course history, V199 exhibition course; V362+ official lane proof | NEW as-of player entry-transition distributions / slow-dash-corner labels absent. |
| R04 historical deep-in | Same R03 | DO NOT scrape historical 日和 result pages or treat live target outcome as data. Fold into R03, not separate code. |
| R05 BOATERS AI2着 pie | V148/V180/V185 conditional models exist | REFERENCE CONCEPT ONLY. AI predicted head-conditioned second differs from *backstretch-led* rate and from true ex-post 1逃げ cohort. No external numeric ingest. |
| R06 BOATERS original timings | V185/V199 use relative exhibition readings | Provenance independent per site missing, but a **republication** of venue measurements is not an independent sensor observation. Automated dual-source fetch BLOCKED pending provider permission. |
| R07 蒲郡 measurement lap | Existing six-boat timing comparisons without explicit same-venue measurement-lap clock support | NEW venue lap availability/clock metadata contract as distinct stage; **one venue example is not 24-venue generalization**. Do not invent values. |
| R08 display-to-race ST offset | V185/V199 use average/display ST | NEW train-only per-player ST residual and uncertainty; never inject same target race's actual ST. |
| R09 reported weak ST correlation | Research hypothesis only; BOATRACEDATA external statistic **not independently replicated** | Do not copy externally estimated coefficient or assume universal player-level weak correlation. Independently estimate conditional effects using permitted pre-target joined observations. |
| R10 official results/program files | V311 source metadata gate/V324 and 3-track repo intake already exist | Official downloadable files are not blanket AI-training/licensing authorization; NO locked Formal outcomes. Needs signed source/use manifest + train/end as-of. |
| R11 official beforeinfo tilt/parts/wind | Existing collector and source audit, policy claims some fields | NEW completeness and archival timestamp per six racer components/maintenance history and feature-grade raw trace, owned by Track 01 source writer after rights approval; no duplicate scraper in 02. |
| R12 Kojima water explanation | Venue×wind×tide already TODO | Qualitative hypothesis; independently measured predeadline tide/observed wind interactions remain unavailable. |
| R13 pre-attachment entry simulation | V148 actual-course historical and V199 exhibition mapping | NEW probabilistic six-racer permutation/interference with *separate provisional actual-entry label*; no falsely claiming forecast entry is historical actual. Fold with R03/R04. |
| R14 motor contribution | Existing motor simple 2連率 and #192 prototype hierarchical motor shrinkage | NEW ability-adjusted race/meet motor increments and motor replacement/maintenance segmentation; provider proprietary scores excluded. |
| R15 SUM slit indicator | ST/exhibition signals already exist | Proprietary formula unverified; no reverse engineering/copy and no additional model until original reproducible signal supports gain. |
| R16 日和 conditional-search UI | R01/R02/R08 overlapping topics | REFERENCE CATALOG ONLY. No unlicensed numeric collection. Consolidate with those items. |

### Canonical prioritized improvement TODO (no duplicates)

**P0 evidence/rights**: operator permission for each provider, original raw archive with actual server first-publication timestamp and SHA, six-racer official source status, historical training as-of cutoff, true course-vs-boat semantics, scratch/exhibition and source clock; signed ledger separate from descriptive URL. V311 read-only checks and V324 strict source gate remain existing; do not build competing collectors.

**P1 conditional heads and tails**: preserve V148–V154/V180/V185/V199/V360 research as baselines; evaluate new R01 *actual-course 1 + confirmed nige* second|escape and third|escape,second; link research-only #192 shrinkage to justified authorized training subgroup counts; no fresh counterpart until actual independently predeadline committed matched-ten. Important mathematical scope: **conditional_20 is NOT full_120**; require other worlds and calibrated P(escape) before full-race probabilities. R01's racer-specific `逃がし2着率` is a Bernoulli rate within that subgroup, not a stand-alone five-way probability vector.

**P1 ST+entry**: R03+R04+R08+R09+R13 one family, separate player ST histogram / relative ST / top ST / exhibition-to-final training-only pair, train-before-target and predicted entry, no target outcome, no missing-value imputation.

**P1 shared experiment criteria**: #192's matched-ten pre-result contract has same race/same SHA/six boats/full 120/ten equal point /¥10,000 virtual per model but its reported SHA/local freeze time is NOT independent Git proof. Track 01 source owner must attest first published immutable Git SHA; separate SITE-only outcome scoring only after gates. V236 scorer already exists, so no duplicate evaluator. Head/Top3/5/10, conditional second/third gaps, multiclass Brier/log-loss, and per-day delta percentage-points+confidence intervals remain unproved. Formal First100 locked.

**P2 venues / original**: R06+R07 same feature family; metadata should include measurement lap (not assume all venues same), same-race six distinct lanes, measured/missing indicator, source URL, rights and raw SHA, same-lap comparison. Source values remain absent unless independently licensed. R12 wind/tide is separate.

**P2 motor/maintenance**: R11+R14 linked, motor lifetime by venue and maintenance; adjust for racer strength, no copying proprietary motor contribution coefficients.

**P3 1M labels and special weather**: R02 1M physical labels, race start type, tilt/propeller and stabilizer etc only with separately verified time and rights. Most remain source-blocked.

### Measurable adoption and handoff (Track 02 to 01/03)

- For all P1 feature ablations predeclare fixed model ID, feature/source manifest, train/validation/future dates, subgroup minimum N, weights, normalized 120 ticket order, Top10 (exactly 10 each), prediction first-SHA and Git-server commit time; all failures and non-frozen R count in denominator.
- Scoring uses permitted, independently time-separated research outcomes only; no Formal Fresh results. Full 120 log loss and Brier are calibrated **only** after documented reliability calibration and sufficient unseen evidence. Separate P(head), Top3/5/10 and rank mass, do not sum top10-renormalized values into a fake 120-way distribution.
- Approval threshold = independent untouched multi-day same-race ten-ticket improvement with confidence intervals and no material head/per-venue regression, source/rights checks, model artifact parity Run1/Run2 and explicit Track 01 integration approval. No threshold is presently satisfied and no percentage-point benefit is claimed.
- Track 01: owner of training-rights manifests/original snapshots, first-Git-server proof, source pipeline, main merge, deployment; **not** delegated any scraping. Track 03: after adoption, clear version ID, actual vs exhibition entry semantics, source completeness, head/TopK calibration and provenance, no premature success indicators.
- Site CURRENT policy/TODO cannot be updated to DONE by this research note; continued parallel research does not imply current-site integration.

**Formal status re-read from `data/formal_status.json` at repository snapshot 2026-10-13 23:35:58+09:00:** core7_eligible_count 13/100; formalFirst100.races 0; results_seen/unlock/scoring false, token null. This is the timestamp on the source JSON, not the clock when this document was written. No result endpoints/files opened.
