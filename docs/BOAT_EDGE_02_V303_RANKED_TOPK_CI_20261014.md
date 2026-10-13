# V303 PRE_RESULT ranked TopK CI — verified 2026-10-14

GitHub Actions [run 38433096197](https://github.com/ikst2512-eng/boat-edge/actions/runs/38433096197) completed SUCCESS on commit `1bcb03aa61945c8ab104514634bccf81c290cc1a`. Job `ranked-readiness` 115420063951 logs explicitly show five V303 regression cases passed: duplicate, formal guard, malformed combo, ready ranking, and reordered ranking. `Ran 5 tests ... OK`.

Read-only PRE_RESULT cohort audit output: `{"cohorts":139,"status_counts":{"RANKED_TOP3_TOP5_TOP10_AVAILABLE":139},"scored_races":0,"topk_hit_rates":null,"model_promotion_authorized":false}`.

Interpretation: 139/139 V232 source cohort JSON files have valid unique ranked Top10 and consistent frozen hit ranking, making prospective Top3/Top5/Top10 prefixes technically available. This **does not** prove 139 independent Git-published-before-deadline cohorts, result matches, TopK hit rates, or model improvement. V303 reads no results and leaves Formal Fresh locked. Do not re-label this readiness count as scored or verified prospective accuracy.

Separate V301 SITE-only scored audit remains: V236 43R baseline 15/43 vs balance10 17/43 (+4.65pt, p=.5); V240 50R baseline 19/50 vs second_coverage10 19/50 (0pt, p=1); V254 58R baseline 24/58 vs third_tail10 25/58 (+1.72pt, p=1). Cohorts overlap. Top3/Top5 **accuracy still unmeasured**. No production model promotion.

Next: verify original first-added Git bytes and independent predeadline publication for prospective ranked source, then run same-race Top3/5/10 only on eligible scored SITE records. Track01 owns V232 upstream 0R/Actions; Track02 owns scorer and paired accuracy; Track03 consumes only approved model ID.
