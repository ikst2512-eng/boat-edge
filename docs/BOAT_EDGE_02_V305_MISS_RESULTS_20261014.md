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
