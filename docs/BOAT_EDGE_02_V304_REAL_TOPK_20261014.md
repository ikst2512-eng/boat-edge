# V304 real ranked TopK baseline — 2026-10-14

Read-only SITE-only CI [run 38433458932](https://github.com/ikst2512-eng/boat-edge/actions/runs/38433458932) completed SUCCESS on head `23b820dd268349f307a5b7ea14f2832655ebcd02`. Artifact `11831817934` (`v304-site-only-topk`), SHA256 `915393b261238b9e3f07066c0f33c1f5e80cf23b7313be4c31f682ffa8689290`, output `v304-topk.json`. V304 revalidates each scored SITE row with V301 `checked_row`, including first Git byte/timing, frozen comparator and parent identity, before evaluating the ORIGINAL ordered hit10 prefixes. No Formal result reads.

| Cohort | Eligible R | Top3 | Top5 | Top10 |
|---|---:|---:|---:|---:|
| V236 | 43 | 9/43 = 20.93% | 11/43 = 25.58% | 15/43 = 34.88% |
| V240 | 50 | 10/50 = 20.00% | 13/50 = 26.00% | 19/50 = 38.00% |
| V254 | 58 | 12/58 = 20.69% | 17/58 = 29.31% | 24/58 = 41.38% |
| Unique same-race union | **85** | **18/85 = 21.18%** | **23/85 = 27.06%** | **33/85 = 38.82%** |

Studies overlap and cannot be added as independent races. Unique race union is 85 across two days, not 151. Candidate Top3/Top5 rank-preserving scores **not yet available**; new-model deltas null. Previously verified equal-budget Top10 candidate deltas: V236 balance10 +2/43 = +4.65pp (p=.5); V240 second_coverage10 0/50 = 0pp (p=1); V254 third_tail10 +1/58 = +1.72pp (p=1). None statistically proven. Formal Fresh LOCKED, no production changes or promotion.

Next: predeclare rank-preserving challenger Top3/Top5/Top10, freeze before deadlines, and evaluate matched SITE-only outcomes with equal ticket budgets and exact paired statistics; report head/second/third miss attribution. Track01 owns V232 upstream zero-cohort recovery.

## V235-linked incremental source audit: Oct 11 baseline outside V301/V304 union (2026-10-14)

**Scope:** Reuse existing V235 → V232 PRE_RESULT frozen cohort → V234 verified site-only settlement → V241 presentation. This is a **read-only provenance/coverage reconciliation, not a new study, model, scoring implementation or backfill**. Sources: main `data/site_autopilot/v241_results_current.json` (Git blob `397dbe21668e9d48e28e3e7315fb19ef8e0c13ea`) and current `data/site_autopilot/v234_current.json`; Formal status at audit `2026-10-14T03:48:58+09:00`: `results_seen=false`, `unlock=false`, `scoring=false`, First100 `0/100`.

| Unique SITE_REFERENCE_V122 baseline set | N | Top3 | Top5 | Top10 |
| --- | ---: | ---: | ---: | ---: |
| Oct 11 (outside the previous V301/V304 research study union) | 19 | 4/19 | 5/19 | 7/19 |
| Oct 12 | 28 | 6/28 | 6/28 | 9/28 |
| Oct 13 | 57 | 12/57 | 17/57 | 24/57 |
| **V234/V241 eligible unique total** | **104** | **22/104 = 21.15%** | **28/104 = 26.92%** | **40/104 = 38.46%** |
| **Already published V304 cross-study unique union (subset)** | **85** | **18/85** | **23/85** | **33/85** |

Exact race-key set reconciliation: all **85** V236/V240/V254 scored-race union keys are present in V241's 104 rows, and the remaining **19** are exclusively 2026-10-11. **Do not sum 85+104 as independent samples**. V234 also reports **35** separate rejections `no_pre_deadline_git_commit_or_mutated_proof`; these are **not** in the 104 scored baseline and were not restored. The **40** V236 `candidate_freeze_time_invalid` rows remain excluded from V236 candidate scoring; this report does not modify that guard.

**Additional verification of all 19 Oct-11 rows:** For each V241-referenced first-add V232 cohort commit, GitHub API `file@first-commit` and `file@main` returned **identical Git blob IDs** (19/19); the first commit's changed-file listing contains the respective cohort path; the frozen ordered Top3 and Top5 are exact prefixes of the ordered Top10 and all three V241 hit booleans reproduce from those original ticket lists and V241's verified winning combo (19/19). **Sixteen distinct first commit SHAs** cover 19 files. For each SHA a GitHub-hosted Actions `created_at` on that exact head SHA was seen **after the cohort's own `evidence_committed_at` and before the race deadline** (19/19). GitHub Actions creation time is independent of Git committer's seconds-resolution timestamp, but it proves GitHub recorded the commit at least by that time, **not** that the Pages deployment succeeded. Cancelled runs were not labelled deployment PASS. V234/V241 SHA-256 assertions were reused; this extra audit verified Git blob identity, not a separate locally recalculated SHA-256.

| Race key | First-add source commit | Independent GitHub Actions run | Top3/5/10 hit |
| --- | --- | --- | --- |
| 20261011-01-04 | [`e1b63ecbd3b5`](https://github.com/ikst2512-eng/boat-edge/commit/e1b63ecbd3b5f320524b21f8b7364a4ccfed7ed3) | [38122047337](https://github.com/ikst2512-eng/boat-edge/actions/runs/38122047337) | 0/0/0 |
| 20261011-01-05 | [`1bb97fc3b315`](https://github.com/ikst2512-eng/boat-edge/commit/1bb97fc3b3154a5cc2aa9a3c2e85f3c04cb6356f) | [38124034540](https://github.com/ikst2512-eng/boat-edge/actions/runs/38124034540) | 0/0/0 |
| 20261011-01-06 | [`42557361e651`](https://github.com/ikst2512-eng/boat-edge/commit/42557361e651fe021b2eff4a18d234dfa5afb711) | [38125680656](https://github.com/ikst2512-eng/boat-edge/actions/runs/38125680656) | 1/1/1 |
| 20261011-02-12 | [`f1062b00eca8`](https://github.com/ikst2512-eng/boat-edge/commit/f1062b00eca844403100070189be9aea43ae6c8f) | [38121283469](https://github.com/ikst2512-eng/boat-edge/actions/runs/38121283469) | 0/0/0 |
| 20261011-06-12 | [`3fb802edebf3`](https://github.com/ikst2512-eng/boat-edge/commit/3fb802edebf3aba040416026e759ff9bbcc9fb57) | [38121438244](https://github.com/ikst2512-eng/boat-edge/actions/runs/38121438244) | 1/1/1 |
| 20261011-08-12 | [`5547586ce56f`](https://github.com/ikst2512-eng/boat-edge/commit/5547586ce56f6778ea80e9b611171d0971986ec9) | [38119633620](https://github.com/ikst2512-eng/boat-edge/actions/runs/38119633620) | 0/0/0 |
| 20261011-12-04 | [`f1062b00eca8`](https://github.com/ikst2512-eng/boat-edge/commit/f1062b00eca844403100070189be9aea43ae6c8f) | [38121283469](https://github.com/ikst2512-eng/boat-edge/actions/runs/38121283469) | 0/0/0 |
| 20261011-12-09 | [`ce3d102842ab`](https://github.com/ikst2512-eng/boat-edge/commit/ce3d102842ab6f2d7cea21e8739758902c0cf7de) | [38129543140](https://github.com/ikst2512-eng/boat-edge/actions/runs/38129543140) | 0/0/0 |
| 20261011-12-10 | [`dfadf715a455`](https://github.com/ikst2512-eng/boat-edge/commit/dfadf715a455ed9261505f19bb79f1b364b35e50) | [38131334242](https://github.com/ikst2512-eng/boat-edge/actions/runs/38131334242) | 0/1/1 |
| 20261011-15-04 | [`e1b63ecbd3b5`](https://github.com/ikst2512-eng/boat-edge/commit/e1b63ecbd3b5f320524b21f8b7364a4ccfed7ed3) | [38122047337](https://github.com/ikst2512-eng/boat-edge/actions/runs/38122047337) | 0/0/0 |
| 20261011-15-05 | [`83b5cd090d09`](https://github.com/ikst2512-eng/boat-edge/commit/83b5cd090d099eeddbd5d05a00f9da8d1b396a3c) | [38123305084](https://github.com/ikst2512-eng/boat-edge/actions/runs/38123305084) | 0/0/0 |
| 20261011-15-06 | [`f1ce2eb0aef5`](https://github.com/ikst2512-eng/boat-edge/commit/f1ce2eb0aef55a09f49d35cbfb57e7541eb1f618) | [38124951309](https://github.com/ikst2512-eng/boat-edge/actions/runs/38124951309) | 0/0/0 |
| 20261011-15-07 | [`9486049d7640`](https://github.com/ikst2512-eng/boat-edge/commit/9486049d7640dc43049149d4f3c903065263b65d) | [38126584088](https://github.com/ikst2512-eng/boat-edge/actions/runs/38126584088) | 0/0/1 |
| 20261011-15-12 | [`cf4ab936d7ac`](https://github.com/ikst2512-eng/boat-edge/commit/cf4ab936d7acdbda46f0ad0f6a7acb591dde75b6) | [38135941072](https://github.com/ikst2512-eng/boat-edge/actions/runs/38135941072) | 0/0/0 |
| 20261011-16-10 | [`dc6898cafc0b`](https://github.com/ikst2512-eng/boat-edge/commit/dc6898cafc0b146602e25e76948abed276e9249b) | [38118283421](https://github.com/ikst2512-eng/boat-edge/actions/runs/38118283421) | 0/0/1 |
| 20261011-19-03 | [`a57e93517a4e`](https://github.com/ikst2512-eng/boat-edge/commit/a57e93517a4e2b609fe9f1d6e767b37c514a0ccb) | [38128477566](https://github.com/ikst2512-eng/boat-edge/actions/runs/38128477566) | 0/0/0 |
| 20261011-19-04 | [`0ad758af2ea5`](https://github.com/ikst2512-eng/boat-edge/commit/0ad758af2ea5fe75f69dfe55fd893abd25eb98bb) | [38130409869](https://github.com/ikst2512-eng/boat-edge/actions/runs/38130409869) | 1/1/1 |
| 20261011-19-06 | [`d9f3f16d2463`](https://github.com/ikst2512-eng/boat-edge/commit/d9f3f16d2463c3a75329d4c4143c616aada6a534) | [38133315648](https://github.com/ikst2512-eng/boat-edge/actions/runs/38133315648) | 1/1/1 |
| 20261011-22-11 | [`5547586ce56f`](https://github.com/ikst2512-eng/boat-edge/commit/5547586ce56f6778ea80e9b611171d0971986ec9) | [38119633620](https://github.com/ikst2512-eng/boat-edge/actions/runs/38119633620) | 0/0/0 |

**Interpretation / hard stop:** This extends the existing **baseline audit** across three dates, not the V236/V240/V254 challenger sample. No independently predeadline-frozen new Top3/Top5 rank-preserving challenger was supplied, so candidate Top3/Top5 deltas remain **unmeasured**; existing equal-10-ticket V236/V240/V254 Top10 paired differences remain statistically inconclusive (see V301). No production accuracy gain, no model adoption, no V236 retro-acceptance, no formal-Fresh score. Track01 retains exclusive ownership of V235/Actions writers and Track03 UI. This amendment changes documentation only and leaves the existing PR #192 research algorithms untouched.

## Verified V304 automated 104R replay artifact (2026-10-14)

GitHub Actions [V304 run 38454611470](https://github.com/ikst2512-eng/boat-edge/actions/runs/38454611470) on exact PR head `988af4b06d349c4213786aa7b5a0c3033a583993` completed **SUCCESS**. Fixture-only V304 tests **12/12 PASS**. GitHub artifact [`v304-site-only-topk` #11841913932](https://github.com/ikst2512-eng/boat-edge/actions/runs/38454611470/artifacts/11841913932) was independently downloaded, ZIP SHA256 **`e8fd7782778d34213fec470820cdbab9f13f6378d08e5a016f06eb539cdcc515`**, internal `v304-topk.json` raw-byte SHA256 **`61dbf83b355c609b85c6fbc7c81c500fbc0c654f8ae89e96d6d30266939f1513`**. The JSON is 2,497 bytes uncompressed. These digests were independently recalculated on the downloaded ZIP and its enclosed JSON; not inferred solely from an Actions green badge.

**Observed output**: `v235_v234_v241_site_baseline.baseline.races=104`, `days=3`, frozen original ranked `baseline_hits={"3":22,"5":28,"10":40}`; `additional_unique_outside_v301=19`; `v301_race_keys_all_contained=true`; mutually exclusive `miss_leg_partition={"top10_hit":40,"head_missing":13,"second_missing_given_head":20,"third_missing_given_head_second":31}`. The 85-race V236/V240/V254 shadow union remains a **subset** with top3/5/10 baseline 18/23/33. Output flags `accuracy_improvement_proven=false`, `promotion_authorized=false`, `formal_results_read=false`, and Top3/Top5 candidate delta `null`.

**CI boundary**: The V304 action validates existing V241/V234 source-evidence logic and the 104R replay. GitHub Actions artifact integrity is verified; no direct production Pages UI runtime or new Oct-14 V235 freeze is established by this artifact. This is **not** an independent result-blind candidate-vs-current forecast and grants **no** model promotion. PR remains Draft; Track01 V235 writers and Track03 UI are unchanged.
