# BOAT EDGE V271 development checkpoint

Basis: current main through V270, with V235/V236/V237 retained as the collection,
forward comparison and monitoring pipelines. V239/V240 research and V241–V270
UI work are preserved. This change does not replace a prediction model.

## Implemented in this change

- V236 rejects an active/unknown formal cohort, wrong race/day/scope/model,
  altered predeclared comparators, invalid freeze times, nonfinite payouts and
  future result timestamps. Candidate/source validation precedes outcome reads.
- V237 checks equal comparison populations, 10-point budgets, ordered Top3/5/10
  counts and the 50,000-yen virtual cap. Previous-day balances remain unknown
  for today. It exposes the existing frozen 10–20x Top10 subset separately.
- The monitoring page shows observed head/Top3/5/10, the fixed-time odds subset,
  paired research comparison and current-day virtual spend/remaining budget.
  JST midnight, stale reports and repeated manual refreshes are covered by tests.
- V236/V237 execute tracked sources with explicit hashes instead of embedded
  compressed installers. Independently maintained UI is not pinned to obsolete
  HTML. Development CI tests fixtures without loading production outcomes.
- `AGENTS.md` provides the ongoing code-edit/test/publish contract. The existing
  ChatGPT daily development automation is the no-upload development route.
  V240's separate Codex GitHub Action remains conditional on its configured
  credential and safety gates; do not claim it ran from workflow success alone.

## Local verification

- 90 V230–V239 Python regressions passed.
- 5 V242 refresh/source-pin checks passed.
- 7 V271 JavaScript day/virtual-budget/manual-refresh tests passed.
- V222 live-odds invalidation regression passed.
- Source hashes, changed workflow YAML/shell syntax and diff whitespace passed.
- No formal result, payout or combined endpoint was used for this development.
- Confirm publication using the commit's Actions runs and matching Pages assets;
  these local checks alone are not a deployment claim or a Safari visual check.

## Continue autonomously

1. Follow the existing unchecked A17–A20 UI tasks where still applicable, and
   preserve any newer completed work on main. Prioritize persistent verified
   odds timestamps, legible evidence-backed hit/miss states and six-racer data.
2. Observe V235/V236/V239/V240 prospective coverage and failure reasons. Do not
   backfill missed freezes or infer improved accuracy from diagnostic cohorts.
3. Audit V230's source race identity and redirect-query binding with synthetic
   fixtures before a separately versioned change; preserve its V235 dependency
   pins atomically. No production price may be inferred from unverified data.
4. Inspect redundant scheduled writers by actual path ownership and successful
   replacement evidence before retirement. Do not disable a functioning source
   collector simply because its version number is old.
5. Keep one daily AI-development automation, preserve the separate daily
   validation report, and report concrete source/deployment evidence concisely.

Accuracy improvement, a complete BOATERS-like interface, and formal Fresh
completion remain unproven. Never report these as delivered by V271.

## V278 official source identity hardening

- V230 validates the exact official PRE_RESULT path, date, venue and race before
  network access and binds the response to that identity. Duplicate or missing
  query fields, invalid dates, nonofficial origins and fragments fail closed.
- Redirects are rejected before following them, so a redirect cannot visit a
  result endpoint or silently substitute another race. Sources that require a
  redirect remain unavailable; no substitute odds or exhibition are fabricated.
- V234/V235 dependency pins change atomically with the shared source.
- Synthetic URL/redirect fixtures extend the existing development CI. No model
  weights, frozen evidence or formal results are changed.
