# V301 real SITE-only paired evidence — 2026-10-14

Source: GitHub Actions run 38428626234, artifact 11828834227 (`v301-site-only-evidence`), ZIP SHA256 `4bb126c3b4122d8f417e8237d67b61c770a14fe6a8b7700052c96f4603ed339d`, exit_code=0. Workflow branch head ce74ec9b8f2715598dea0472c07cdc115fc4f2c7; checkout `source_commit.txt` reported `42bef818a10807f877a9971aef6c3da361ce59ed` (PR merge checkout SHA, not branch SHA). Full-history checkout, V301 Git original byte/timing checks, formal guard enforced. Audit JSON scope `VERIFIED_GIT_PREFREEZE_SITE_SCORE_RECHECK_NOT_FORMAL_FRESH`. Formal results read=false; model changed=false; promotion=false.

## Actual eligible rows and paired 10-ticket outcomes

| Study | Eligible races | Days | Baseline hits | Challenger hits | Gains | Losses | Exact paired p |
|---|---:|---:|---:|---:|---:|---:|---:|
| V236 balance10 | 43 | 2 | 15 | 17 | 2 | 0 | 0.5 |
| V236 scenario7plus3 | 43 | 2 | 15 | 17 | 2 | 0 | 0.5 |
| V240 second_coverage10 | 50 | 2 | 19 | 19 | 3 | 3 | 1.0 |
| V240 pair_coverage10 | 50 | 2 | 19 | 19 | 2 | 2 | 1.0 |
| V254 third_tail10 | 58 | 2 | 24 | 25 | 2 | 1 | 1.0 |

V236 coverage15 = 21/43 but 15 tickets and **not** comparable to 10-ticket modes.

Cross-study exact identical-race matched sets: V236↔V240 36 races/2 days; V236↔V254 16 races/2 days; V240↔V254 28 races/1 day. These are overlapping cohorts, not additive sample sizes. Example V240 hit10↔V254 third_tail10: 28 same races, baseline 11 vs candidate 12, one right-only hit, zero left-only, p=1.0. No demonstrated superiority.

Inventory: v232_cohort 139, v236_frozen 83, v236_scored 43, v240_frozen 50, v240_scored 50, v254_frozen 58, v254_scored 58 JSON files. The 43/50/58 are independently validated study rows, not 151 independent races.

## Decision
**EVIDENCE_COLLECTED; IMPROVEMENT_NOT_PROVEN; NO_PROMOTION.** Exact paired McNemar p-values do not establish a lift, and only 1–2 days per study. This is real SITE-only evidence, not Formal Fresh and not validation of a production model. Next: accumulate additional genuinely prospective days with first-Git predeadline proofs, run same V301 gate, keep challenger pre-registered, report novel Top10 set membership, head/second/third misses, and no promotion until fresh holdout evidence.

## Freeze-to-score coverage audit (CI 38429072587)

Read-only filename comparison from `coverage.json`, artifact `11829937621`; V301 exit_code=0; development CI `38429072605` SUCCESS. V236: 83 frozen, 43 scored, **40 frozen-not-scored all on 20261013**, 0 scored-without-frozen. V240: 50 frozen/50 scored, zero unmatched. V254: 58 frozen/58 scored, zero unmatched. These are counts of committed filenames, not evidence of missing results or permission to fetch them. Investigate V236 scoring workflow and failure conditions on 20261013; never infer outcomes for unmatched races. No backfill of Formal or postdeadline scoring to a predeadline label.

## Root cause confirmed from main V236 score summary

The main-branch `data/site_autopilot/v236_score_current.json` has `scored_total=43` and `rejected_or_pending_this_run={"candidate_freeze_time_invalid":40}`. This matches all 40 unmatched 20261013 V236 frozen filenames. The V236 source `score_row` rejects when `frozen_at` is missing/unparseable or later than the *first-added Git commit's committer timestamp* (`frozen_at > frozen_commit['at']`). Thus the immediate rejection gate is identified; **not** a missing official result diagnosis. Why timestamps differ (clock skew, first-commit timing, Git metadata, etc.) is not yet established. Do not change timestamps, weaken gate, or retro-score these 40 rows without independent predeadline provenance. The source uses Git committer time, not authenticated GitHub server receipt time, so describe it precisely.

## V302 verified timestamp-delta diagnosis (CI)

GitHub Actions run [38430200881](https://github.com/ikst2512-eng/boat-edge/actions/runs/38430200881), head `460fa93a54bd1432aef29ded3edbecd84a4b206f`, completed SUCCESS; artifact `11830288722` (SHA256 `5e7243b737f081465e98566823399046ec8d2a151ec9fe7c99c2f5c6863ee3b7`). Read-only full-history metadata inspection of 40 frozen-but-unscored V236 rows: **40/40 positive subsecond** `frozen_at - first-add Git committer date` differences, minimum **0.029188 s**, maximum **0.839312 s**; 0 >= 1 s; 0 unparseable. This proves the strict datetime comparison directly rejects these rows due to Git second precision, but DOES NOT independently prove predeadline GitHub publication/receipt or authorize retrospective scoring. Keep original data and strict scoring gate unchanged pending independent publication evidence and tests. Development CI run `38430200708` SUCCESS. No production/model promotion; Formal Fresh LOCKED.
