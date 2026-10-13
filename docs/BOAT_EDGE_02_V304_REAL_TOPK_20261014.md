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
