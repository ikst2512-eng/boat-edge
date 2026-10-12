# BOAT EDGE guarded autonomous development

## Objective
Reduce manual ZIP upload and operator intervention. Keep prediction accuracy work and site improvements connected to the same immutable model and version IDs.

## Hard boundaries
- Formal Fresh remains locked until the formal gate passes; no target-date results, payout, result pages, or combined APIs before unlock.
- Never treat historical backtests, site-only scores, or shadow experiments as formal prospective evidence.
- Never promote a candidate prediction model without a reproducible untouched forward cohort and verified improvement against the frozen control.
- Freeze predictions and stake allocations before results. Do not mutate frozen picks after publication.
- Fail closed on missing scratches, stale odds, unverified exhibition metrics, or missing official data; never invent data.
- The daily 50,000-yen operation is a paper simulation only.

## Continuous cycle
1. Read the latest main branch and the current V235/V236/V237+ workflows; avoid duplicate workers.
2. Audit scratches, entries, exhibition data, odds freshness, and freeze timing.
3. Compare head, Top3/Top5/Top10, hit rates and return using matched untouched cohorts, frozen picks and exact payouts.
4. Improve mobile UX and visible race cards while preserving provenance and immutable prediction identifiers.
5. Develop on a separate branch; run targeted and regression tests; open a pull request with reproducible evidence.
6. Merge or deploy only after required checks pass and no formal-lock violation is detected.
7. Verify Pages deployment and data consistency; report failed and blocked steps honestly.

## Initial implementation priorities
1. Investigate V167 official 120-combination odds verification failure; do not use stale odds as verified.
2. Verify Pages deployment and eliminate redundant cancel/redeploy churn.
3. Audit V251 result-card display and ensure it cannot rewrite frozen picks.
4. Advance V239 paired prospective Top10 comparisons only when eligible cohorts exist.

This document is a development contract, not proof that an autonomous code-writing agent is installed or that prediction accuracy improved.
