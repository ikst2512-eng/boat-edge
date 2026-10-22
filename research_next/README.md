# BOAT EDGE — Next Research Lab (isolated)
This research scaffold is independent of **boat-edge-clean**. Nothing here is a deployable forecasting feature.

## One runner, six candidate families
- exhibition: exhibition ST, lap / turn / straight measurements
- entry: actual entry order, deep-in, advance entry
- attack: second-course escape assist, pass / sweep probabilities
- course: actual-course history, local records
- motor: recent motor history, part changes
- water: wind direction/speed, waves and tide

Input is a CSV of **frozen pre-race features** with mandatory race_code, captured_at_jst, deadline_jst, source_sha256, split, outcome. Baseline probability and candidate probability arrays of all 120 trifectas are required for a common exact-race test. The provided runner never invents probabilities. It validates source timing (by configurable margin), date-disjoint train/test split, probability sums, and reports Top3/Top5/Top10 and log loss, plus paired Top10 improvements. Outcomes should only be joined for retrospective scoring *after* features/predictions have been sealed.

**Provenance limitation:** timestamps in local CSV are self-reported, not independent trusted attestations. Passing tests is not evidence of real 12-minute-before availability or deployment fitness.

Run: `python -m unittest discover -s research_next -p 'test_*.py'`.
Evaluation: `python research_next/evaluate.py research_next/example_schema.csv --margin 12`.
The example is header-only; no made-up forecasts or results are supplied.
