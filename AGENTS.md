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

## Development cycle

1. Inspect current main and relevant Actions state; distinguish data-update
   schedules from an AI development task. Scheduled Actions do not modify their
   own implementation intelligently.
2. Take one evidence-backed improvement from `DEVELOPMENT_STATUS.md`, and finish
   it through implementation and relevant regression tests. Preserve unrelated
   changes and concurrent collector commits.
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
