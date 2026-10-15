# BOAT EDGE 02 — 2021–2025 licensed-history evidence gates

Status (2026-10-16): **RESEARCH ONLY. No five-year raw data acquired, no source permission independently confirmed, no observed accuracy improvement, no model promotion.**

## Objective and existing work

Keep the deployed 120-trifecta ranking model until one predeclared candidate outperforms it on the **same races with the same ten tickets** using genuinely predeadline inputs, immutable predictions and independent result verification. BOAT EDGE 02 owns research; 01 owns collectors/permission/prod deployment and 03 owns UI. Existing draft PR #192 covers conditional-120, ST and joint-course estimators. This PR does not duplicate them.

## Data rights (default deny)

- Official [archive entry](https://www.boatrace.jp/owpc/pc/extra/data/download.html) lists nationwide race results, programs and 2021–2025 racer term files. Download availability does not, by itself, grant automated extraction/AI training/redistribution rights.
- Official [site policy](https://www.boatrace.jp/owsp/sp/extra/policy.html) reserves rights outside individual conditions or lawful exceptions and prohibits access levels impairing service. Obtain permission or a documented use-specific legal analysis before collecting archives at scale.
- [競艇日和 terms](https://kyoteibiyori.com/terms.html) prohibit unapproved automated acquisition and AI analysis/training. [BOATERS terms](https://boaters-boatrace.com/info/terms) and venue providers also require separate review. Do not import their numeric content as a substitute.
- Preserve default-deny [01 permission register](../docs/BOAT_EDGE_01_V374_SOURCE_PERMISSION_REGISTER.json) and issue #204; do not alter existing third-party capture without 01 review.

**Prepared request to rightsholder (01 action):** seek documentary rights for nationwide 2021–2025 results and pre-race programs, private raw storage, derived features, ML analysis/training, historic backtesting, bounded acquisition method/rate, and aggregate metric reporting. Ask about redistribution, retention, commercial use, attribution, venue-level subrights and revocation. Keep written grant privately outside Git; record only a safe reference and SHA-256. A statutory-exception pathway needs case-specific legal assessment; this document is not legal advice.

## Implemented (network-free)

1. `scripts/boat_edge_02_five_year_archive_gate.py` accepts operator-supplied bytes only. It requires an attested scoped grant, local grant-document digest, and **120 declared monthly parts**: 60 months (2021–2025) × 2 kinds (pre-race program and post-race result). Checks SHA-256, size, duplicate month/kind, date/grant expiry and path safety. Explicitly blocks repository `data/`. Does **not** unpack files, scrape, parse race outcomes or confirm individual-race completeness or license legitimacy.
2. `scripts/boat_edge_02_paired_topk_evidence.py` aggregates **separately reviewed, pre-scored boolean hit flags only** for same-race Top3/5/10 on 2025 historic replay. Checks 2025-only race IDs, pair uniqueness, nested TopK hits, equal-ten contract and self-attested input-cutoff flags. Reports each arm's hits/rates, delta in percentage points, discordant wins/losses and a fixed-seed whole-day cluster bootstrap. Requires ≥500 races and ≥30 distinct days; uses 3-comparison Bonferroni 95% familywise intervals. Never reads result files, verifies authorization, authorizes Formal Fresh, or promotes a model.

CLI (only after verified scope-specific rights and private archive supply):

```bash
python3 scripts/boat_edge_02_five_year_archive_gate.py --manifest /secure/rights/manifest.json --archive-root /secure/archives --grant-file /secure/rights/grant.txt
python3 scripts/boat_edge_02_paired_topk_evidence.py --pre-scored-manifest /secure/research/2025_scored_pairs.json
```

Archive-manifest schema is `BOAT_EDGE_02_2021_2025_ARCHIVE_GATE_V1`. `rights` requires `review_status=HUMAN_REVIEWED_APPROVED`, explicit `local_archival_storage`, `offline_statistical_analysis`, `ml_training` flags, `automated_download=false`, `third_party_scraping=false`, provider, rightsholder, reviewer, reviewed_at, grant_reference, grant_sha256, expires_on, scope_years `[2021,2022,2023,2024,2025]`, and data_kinds `['post_race_result','pre_race_program']`. Each `partitions` entry must declare month, kind, relative file, sha256, size_bytes and declared_record_count. A positive report verifies only local bytes and inventory declarations, **not legal clearance or complete race data**.

Paired-manifest schema is `BOAT_EDGE_02_PAIRED_TOPK_PRE_SCORED_V1`: `stage=2025_HISTORICAL_REPLAY_NOT_PROSPECTIVE`, reviewed declarations, dataset/scorer/model SHA receipts, and per-race `race_key`, `same_race_same_ten_ticket_budget`, `independent_input_cutoff_checked`, baseline_hits and candidate_hits with exact `'3'`, `'5'`, `'10'` booleans. Declarations/receipt hashes are not independently validated by the aggregator. Existing protected V236/V343/V344 lanes require 01/02 review before supplying any authorized pre-scored rows; this PR deliberately does not create a second outcome scorer.

## Acceptance path remaining

1. **Rights first:** 01 obtains appropriate rights or specific legal analysis; only then acquire actual 2021–2025 archive files using authorized means. Passing archive inventory is not proof all 24 venues and races are present.
2. **Normalize and reconcile:** check date/venue/race IDs, program-vs-result joins, six boats, cancellations/returns, duplicate keys, source format revisions, actual race coverage and source hashes. Track missingness instead of fabricating rows.
3. **As-of correctness:** prove target-race features existed before the deadline (or distinguish retrospectively reconstructed program fields as less reliable). Exclude actual outcome, real race course, later updates and payout from prediction inputs. Research train 2021–2023, tune 2024. 2025 is *retrospective replay* unless a verifiable experiment lock actually predates it; never call 2025 untouched just because it was not used for fitting.
4. **Paired evaluation:** compare pinned existing 120-way Git SHA against one registered candidate with equal ten tickets on identical eligible races; report Top3/5/10, head/non-1-head, misses at 2nd/3rd, denominators, missing data and uncertainty. Confidence intervals alone cannot fix biased/reconstructed inputs.
5. **Actual proof:** later independent prospective dates, valid before-deadline immutable Git-first-write receipts, permission-cleared independent scoring and the separately enforced Formal Fresh gate. A 2021–2025 license never opens Formal Fresh. Only sustained prospective incremental gains can be proposed to 01 for deployment. Keep any real-money action outside this research.

Fixture-only tests: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_boat_edge_02_*' -q` (if running broad tests, use the two explicit test filenames to scope this PR). No real accuracy results have been generated.
