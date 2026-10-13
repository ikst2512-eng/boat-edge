# BOAT EDGE autonomous development

The user authorizes code changes, tests, GitHub commits and Pages verification
without repeated ZIP downloads/uploads or routine confirmations. Use the existing
repository and Pages site. Do not create a replacement website.

## Safety boundary

- Read `data/formal_status.json` before any race-outcome access. Formal Fresh
  results, payouts, result pages and combined APIs remain off limits until its
  independent formal gate passes. This development loop must never unlock it.
- Do not use broad reads of `data/`, historical result searches, or result-aware
  imports to inspect the code. Tests must use synthetic temporary fixtures.
- Site research is separate from formal Fresh. V235/V236/V237/V238 are the
  operational baseline. V271 hardens V236 and V237; it is not a new prediction
  model and is not evidence of improved accuracy.
- Before site-only scoring, require an explicitly empty formal cohort and
  closed flags. Verify the site's pre-deadline immutable Git evidence, race ID,
  source bytes, timestamps and predeclared ticket definitions before reading its
  specific outcome. Never reconstruct old predictions or stakes after results.
- Do not change frozen cohorts, result records, production prediction weights,
  formal parent SHA, promotion gates or safety thresholds in routine development.
  An unproven research candidate cannot enter production. Missing data stays
  missing. Do not boost tickets just because their odds are 10–20x.
- The simulator is virtual only, with a 50,000-yen daily cap. Never place real bets,
  add funds, or turn a diagnostic calculation into an authorized purchase.

## BOAT EDGE 01 site-first product acceptance (owner directive 2026-10-14)

BOAT EDGE 01 is responsible for integration, delivery, Actions/Pages reliability,
data collection/publishing, and the actual development loop. BOAT EDGE 02 owns the
forecast model, accuracy experiments and promotion decisions. BOAT EDGE 03 owns
screen implementation and visual QA. 01 must not independently change 02 model
logic or 03 UI implementation; share exact failure evidence with those owners.

The first deliverable is a usable **existing** public BOAT EDGE site:
a visitor can choose venue and race, then view verified, pre-deadline saved
Top3/Top5/Top10 for that exact race when eligible. End-to-end acceptance requires:

1. Current official race ID, deadline, source freshness, absence/scratch and
   beforeinfo/odds readiness are evaluated without guessing missing fields.
2. The prediction is actually generated and immutably committed before deadline;
   audit the first Git-add commit time, race/model ID and byte SHA. Never treat
   an Actions success or a generated preview as a valid frozen final prediction.
3. Published Pages contain the exact saved prediction bytes, and Chromium plus
   iPhone-sized WebKit actually render the right race's Top3/Top5/Top10 after
   selecting its venue and race. Real-device Safari is an independent check.
4. If prerequisites are missing, show an explicit, accurate stopped/waiting state
   rather than fake recommended tickets. Early racelist-only previews must stay
   clearly labelled uncalibrated, non-final and non-betting.
5. Confirm Actions and Pages health by specific commit SHA and deployment run;
   a cancelled outdated Pages run is not itself a live outage when a newer
   deployment succeeds. Avoid disabling writers without path/owner evidence.

Prioritize real breakage in collection -> immutable save -> public Pages ->
actual display, then Actions/Pages reliability and bounded automation. Inspect
existing TODOs, PRs, tests and workflow owners *before* any change; don't re-add
work already implemented by 02, 03 or completed V240 tasks. Never use added
version numbers, file counts, tests or audit code as success metrics for the
product. Work each new issue through source fix, synthetic/regression tests,
isolated PR, CI, conflict-safe main integration and published-site verification.
Do not conflate a scheduled recurring Actions job with proof that autonomous
AI code editing occurred. The V240 Codex lane may require paid API credentials;
do not provision or require paid credentials as a workaround.

Report three separate outcomes: (a) actually working user functions,
(b) specifically resolved defects supported by tests/commits/deployments,
(c) remaining defects or missing live evidence. Do not mark the site complete
until real live TopK end-to-end is verified.

## Development cycle

1. Inspect current main and relevant Actions state; distinguish data-update
   schedules from an AI development task. Scheduled Actions do not modify their
   own implementation intelligently.
2. Prioritize a source-backed **live product usability** defect from the
   latest Actions, Pages, and browser evidence. Cross-check the master TODO and
   existing PRs first, then finish the smallest scoped fix and relevant regressions.
   Preserve unrelated changes and concurrent collector commits.
3. V236/V237 workflow source pins must match the tracked files. After changing
   one of their sources, update its SHA-256 map in that workflow in the same
   atomic commit. The workflows verify tracked code; no upload/bootstrap ZIP is
   needed. Run `python3 scripts/verify_workflow_source_pins.py`.
4. Run the applicable fixture-only checks:
   `PYTHONPATH=scripts PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_boat_edge_v23*.py' -q`
   and `node --test tests/test_boat_edge_v271_health.cjs`.
   Python dependencies are requests, beautifulsoup4, lxml and pyyaml.
5. Publish only the reviewed paths, preserving the latest main as parent. Use
   fast-forward/expected-head protection. Never force push or resolve a race-data
   conflict by overwriting current main. Repeat checks if relevant source changes.
6. Check Actions success and the actual Pages assets. Separate prepared, pushed,
   deployed, runtime-verified and statistically proven states. Record exact
   commits, observed runs and outstanding limits without claiming future success.

If an authenticated write is denied, do not evade the permission boundary or
ask the user for another ZIP upload. Preserve the tested work, identify the
specific missing permission, and request only that access.
