# BOAT EDGE 02 — 第二弾・重複監査と研究ゲート（2026-10-13 JST）

Scope: Track 02 research branch ONLY. Track 01 owns main merge, common Actions/source write and deployment. Track 03 owns UI. No model promotion, historical prediction backfill, official Formal Fresh access, or real wager.

## Eight requested features: overlap before writing new code

| # | Repo evidence | Classification / new work | Priority |
|---|---|---|---|
| 1: Course 1 escape -> second | V148 escape_course1 world and head-conditional second models; V180 120-way | PARTIAL: independently verified *escape winning method*, actual entry and second condition are still needed; finish winner ≠ backstretch leader | P1 |
| 2: third given ordered first and second | V148 training-only conditional, V180 factorized top120, V185 third role, V153 calibration candidates | RESEARCH EXISTS. No duplicate new implementation; prioritize new-cohort validation and calibration | P1 acceptance gate |
| 3: 1M resistance / narrowing | V151/V154 wall/attack proxies only | NEW labelled player behavior, requires authorized action observations, cannot infer from finishing positions | P2 blocked |
| 4: deep-in / slow-dash preference | V148 actual-course historical study; V199 start-exhibition course | PARTIAL: authenticated slow/dash/deep historical counts absent | P2 |
| 5: ST distribution / top start / exhibition-to-live residual | V185/V199 use average and exhibition ST | PARTIAL: no verified prior-only histogram, top-start, target-leakage-safe residual | P1 |
| 6: 2–6 loss mechanisms / inner wall / outer attacker | V154 wall/attack, V152 scenario worlds | PARTIAL: new defeat mechanism and conditional interactions need validation | P2 |
| 7: original time measuring position / within-venue gaps | V185/V199 same-race normalized times | PARTIAL: venue measurement-position verified metadata not found | P2 |
| 8: racer/motor/venue hierarchical adjustment | V148 conditional pseudocount, V153 calibration hypotheses | PARTIAL: separate racer/motor/venue shrinkage hypothesis (this PR) | P1 |

V148/V149/V150/V151/V152/V153/V154 historical folds reused historical holdouts: DO NOT PROMOTE. V156 prospective *site-only research* watch recorded 756 frozen races, 0 scored in that watch; V157 archived audit recorded 621 settled races in its four-day 624-frozen subset. None is a completed formal Fresh or new-model accuracy proof. V360 exists in open Track 02 PR #161; do not cherry-pick/overwrite its freeze code in this PR.

## New isolated research fixture

`scripts/boat_edge_02_hierarchical_conditional_research.py`: standalone training-count-only nested Dirichlet model on head → second|head → third|head, with fixed national/venue/racer/motor shrinkage layers, strict 120 unique BOAT tickets, deterministic Top10 and separated head marginals. Missing layers are omitted, not imputed. Source authorization evidence, training cutoff before race day, predeadline JST timestamp and locked Formal date must be explicitly declared or it rejects. **Metadata/SHAs are self-assertions; this does not verify actual rights or source timestamps**.

`tests/test_boat_edge_v236_02_hierarchical_conditional_research.py`: 9 local fixture-only cases (120 / exact10 / head sums / deterministic / no imputed fields / invalid counts / unauthorized source / training on target day / expired or wrong-timezone freeze / Formal exclusion / unexpected input).

No third-party web scraping, no result/payout/combined API, no formal target, no production model file, no common workflow, no Pages, no scoring and no wagers.

## Equal-ten unseen validation before adoption

1. Source ledger: original URL/operator, exact first acquisition time, raw digest, reviewed permission scope, independently pinned training cutoff, usable licence, dataset manifest. BOATERS/競艇日和 site-only descriptions may inspire a hypothesis but **their values must not become training data without explicit authorization**. Official source is not automatically an unlimited bulk-use licence.
2. Immutable prospective parent and candidate on **the same race**, same verified pre-result data, same entry basis, six runners/scratch checks, same deadline; commit exact 120 score rows, 10 picks/model IDs and source hash before outcomes. Report all failed/frozen attempts.
3. Historical design or retrospective re-used F1–F3 is NOT Fresh. Prepare separate chronological train → validation → untouched future-test cohorts; disjoint dates, exact sample parity, blinded results, independent run1/run2 byte proof.
4. Compare identical ten tickets, Top3/5/10 hit rates, head hit rate, conditional second/third misses. If virtual money examined: identical 10-point allocation, max ¥50,000/day. For authorized full-120 scoring compare log loss, multiclass Brier/reliability and calibration curves, subgroup Ns and uncertainty ranges; no odds-based ranking.
5. Ablate *new* candidates (#1 verified escape condition, #5 ST distributions, #8 hierarchical) one by one against actual current baseline and V148/V154/V180/V185/V199. #2 has existing code; only missing prospective comparison. #3/#4/#6/#7 only when legal action/sensor data supported.
6. Adoption only after statistically adequate independent future evidence and Track 01 gate. Formal Fresh `results_seen=false`, `unlock=false`, `scoring=false` unchanged; this code never unlocks.

## Research-only public references (concepts, NOT numeric training extracts)

- https://kyoteibiyori.com/blog/202509111001
- https://kyoteibiyori.com/vup/
- https://www.boatrace-shimonoseki.jp/sp/index.php?page=raceinfo-racecourse
- https://boaters-boatrace.com/guide/data-how-to-read
- https://kyoteibiyori.com/terms.html
- https://boaters-boatrace.com/info/terms

BOATERS' backstretch first-boat連対率 is a different target variable from the final 1st boat's 2nd-place conditional distribution; do not merge labels.

## Handoff to Track 01

Base main SHA `4bbe5bdb5814f4b738ee7bca7ec316a261bafdb0`. Branch `research/02-wave2-conditional-20261013`. Three new files only, no overlap with #161 paths. Local Python 9/9 synthetic PASS. Await PR CI and Track 01 review; **code-ready ≠ deployed ≠ prospective accuracy verified**.
