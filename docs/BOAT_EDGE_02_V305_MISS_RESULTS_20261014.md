# V305 SITE-only miss attribution: verified CI results

Run: https://github.com/ikst2512-eng/boat-edge/actions/runs/38434126219 (SUCCESS), head `db880026a691860b76269a93e4c20d8a4afe2f0c`. Two synthetic tests PASS. Artifact `11832530909`, sha256 `d3297bec5f07d0e760041b0ae4472902f9a86cc95086b0afefa4540c29ba7e65`.

| V301-verified SITE group | R | Top10 hits | 1st absent | 2nd absent given 1st | 3rd absent given 1st+2nd |
|---|---:|---:|---:|---:|---:|
| V236 | 43 | 15 | 5 | 7 | 16 |
| V240 | 50 | 19 | 7 | 10 | 14 |
| V254 | 58 | 24 | 6 | 10 | 18 |
| **Unique same-race union** | **85** | **33** | **9** | **15** | **28** |

Exactly 52 misses in the unique union: 9 (17.31%) lack winning head, 15 (28.85%) have head but lack correct second, 28 (53.85%) have correct first-two somewhere but lack correct third. Exclusive, exhaustive categories. This is ticket-coverage diagnosis, NOT causal attribution to race entry/turning/water/weather, which remains unavailable. Studies overlap; never sum 43+50+58 as independent races.

V304 same 85 unique races: Top3 18/85, Top5 23/85, Top10 33/85 baseline. Top3/Top5 candidate lift unmeasured. V301 Top10 challenger changes not statistically proven. Future tests should prioritize predeadline-frozen third-leg candidate selection with exactly 10 tickets, equal-budget paired SITE-only comparisons, without retrospective optimization on these 85 races. Formal Fresh LOCKED; no model promotion or production changes.

## Additional nonoverlapping Oct-11 leg audit / 104R baseline reconciliation (2026-10-14)

The existing V305 classification logic was **reused, not reimplemented in the repository**. The V301/V305 CI-audited 85-race union covers Oct 12–13 and remains unchanged. An additional 19 Oct-11 SITE_REFERENCE_V122 V234/V241-verified baseline rows were individually read from the **original first-added V232 Git commit**, with original/current Git blob equivalence, first-added commit inclusion, independent GitHub Actions run creation strictly between candidate freeze and race deadline, and frozen Top3/5/10 prefix/outcome parity; the 19-receipt inventory is recorded in this PR's `docs/BOAT_EDGE_02_V304_REAL_TOPK_20261014.md`. These 19 are **outside** the existing V236/V240/V254 85-race union; no V236 retro-score or new candidate can be inferred. Source V241 Git blob `397dbe21668e9d48e28e3e7315fb19ef8e0c13ea`, `settled_verified_races=104`; Formal gate closed at review (`results_seen=false`, `unlock=false`, `scoring=false`, First100=0).

The definitions are identical to existing V305: winner in immutable ordered Top10 → hit; otherwise no exact winning first leg anywhere → head absent; otherwise no first+second pair → second absent; otherwise third leg absent. **This is ticket coverage, not proof of an entry, water, motor, ST or tactic cause.**

| Mutually exclusive category | Existing V305 union 85R | Additional Oct-11 19R | Combined unique 104R |
|---|---:|---:|---:|
| Top10 hit | 33 | 7 | **40** |
| Winning first leg absent | 9 | 4 | **13** |
| Correct first leg present; winning second leg absent | 15 | 5 | **20** |
| Correct first+second pair present; winning third leg absent | 28 | 3 | **31** |
| Total | **85** | **19** | **104** |
| Top10 misses | **52** | **12** | **64** |

Among the **64** missed tickets sets, head-coverage gap 13 (20.31%), second-leg gap 20 (31.25%), third-leg gap 31 (48.44%). Original V241 ordered-prefix baseline across all 104: **Top3 22/104=21.15%**, **Top5 28/104=26.92%**, **Top10 40/104=38.46%**. The 19 new classifications each reproduce the preexisting V241 hit flags for Top3/5/10, **19/19**.

| Race ID | V305-style exclusive classification | Original Top3/5/10 hits (0/1) |
|---|---|---|
| 20261011-01-04 | head_missing | 0/0/0 |
| 20261011-01-05 | second_missing_given_head | 0/0/0 |
| 20261011-01-06 | top10_hit | 1/1/1 |
| 20261011-02-12 | third_missing_given_head_second | 0/0/0 |
| 20261011-06-12 | top10_hit | 1/1/1 |
| 20261011-08-12 | second_missing_given_head | 0/0/0 |
| 20261011-12-04 | second_missing_given_head | 0/0/0 |
| 20261011-12-09 | third_missing_given_head_second | 0/0/0 |
| 20261011-12-10 | top10_hit | 0/1/1 |
| 20261011-15-04 | second_missing_given_head | 0/0/0 |
| 20261011-15-05 | third_missing_given_head_second | 0/0/0 |
| 20261011-15-06 | head_missing | 0/0/0 |
| 20261011-15-07 | top10_hit | 0/0/1 |
| 20261011-15-12 | second_missing_given_head | 0/0/0 |
| 20261011-16-10 | top10_hit | 0/0/1 |
| 20261011-19-03 | head_missing | 0/0/0 |
| 20261011-19-04 | top10_hit | 1/1/1 |
| 20261011-19-06 | top10_hit | 1/1/1 |
| 20261011-22-11 | head_missing | 0/0/0 |

**Research decision:** Descriptive coverage gaps may motivate a future **predeclared, independent, same-race, same-budget** head/second/third ranking ablation in the existing PR #192 pathway. **No retro-optimisation on the 104 observed outcomes**; V236, V240, and PR #192 candidate deltas remain unproven; do not silently equate site-only baseline with Formal Fresh. This extension modifies only this existing V305 document, not Track01 V235/Actions, production model, scorer, frozen assets or PR #192 algorithms. V301/V305 CI checks cover the original 85R, **not** this supplementary Oct-11 manually reviewed 19R. No production promotion authorized.
