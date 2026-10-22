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

## Feature intake (new)

`python research_next/feature_intake.py race_input.json --captured-at-jst 2026-10-23T08:00:00+09:00 --deadline-jst 2026-10-23T18:00:00+09:00 --output frozen/202610231201.json`

Each source JSON has `race_code` and exactly six `boats` objects containing `boat` (1–6), `actual_entry` (1–6, a permutation), and optionally `exhibition_st`, `lap_time`, `turn_time`, `straight_time`. The intake writes a structured copy with the SHA-256 of the raw input and a time check; incomplete exhibition values remain explicitly incomplete. This tool is source-agnostic: a trustworthy collector must separately establish how the data originated and that it was actually available at the recorded time. This module does **not** generate predictions, score races or claim source authenticity.

Input examples are schema definitions only; no fabricated race data is included. Run `python -m unittest discover -s research_next -p 'test_*.py'` for both the evaluation and intake contract tests.

## vNext frozen-record audit

Store the raw JSON received by the collector separately and without modifications. Verify its relationship to the frozen normalized record with:

`python research_next/audit_frozen.py frozen/202610231201.json raw/202610231201.json`

The auditor recalculates the raw-file SHA-256 and reruns schema validation. A changed raw byte, changed saved feature, invalid entry permutation, or claimed capture after the chosen cutoff fails closed. **This does not establish an independent remote publication timestamp**. A production collector still needs capture-time provenance, immutable storage, and external source verification before results can be treated as genuinely pre-race.

## Availability probes (12, 11, 10 minutes)

Run the real HTTP probe **before** the named cutoff, never retrospectively. It checks that the exact race row and all six nationwide win rates exist; only then stores response bytes, SHA-256, started/completed JST time, and which cutoff margins were met.

`python research_next/probe_availability.py --race-code 202610231201 --deadline-jst 2026-10-23T18:00:00+09:00 --source-url https://boatracecsv.github.io/data/programs/race_cards/2026/10/23.csv --output research_next/probes`

The example race/deadline is illustrative, not a confirmed official schedule. No automated probe has yet been deployed, and no real capture success is asserted. This measures **CSV host availability**, not the original official exhibition publication time. Per-run timestamps are local runner-clock assertions, not an independent trusted time source. Do not use late captures in pre-cutoff forecasting.

## Scheduled real-source acquisition

The repository now includes `.github/workflows/research-availability-probes.yml`, which is configured for every ten minutes from 09:00–22:50 JST. The runner discovers today's races from the BoatraceCSV title feed, chooses races between 10 and 180 minutes before scheduled deadline, obtains the corresponding race card, checks six nationwide win rates, and writes immutable per-run raw response + SHA-256 metadata to a GitHub Actions artifact retained 30 days. It does **not** request any results or change BOAT EDGE CLEAN. The schedule is only a configuration; GitHub Actions may be delayed, disabled, or fail. Successful operation is not confirmed until run logs and artifacts are inspected. The result does not prove official site release time. This checks national win-rate race cards, **not** BOATERS exhibition data.

After runs, download a complete run artifact and execute `python research_next/probe_report.py <artifact-root>`; output reports the count of validated source snapshots by cutoff. Its counts concern distinct race/source pairs, not externally attested pre-race forecasts.

## Operational run status

The scheduled workflow now writes `research_next/probe_run_status.json` (discovered/due/captured/failed and bounded error types) and `research_next/probe_summary.json` (recomputed 12/11/10-minute eligibility from captured raw bytes and manifests). Both appear as downloadable workflow artifacts and in the GitHub Actions step summary. An acquisition failure makes the job fail, rather than silently showing a successful green run. A zero-race successful run means the scheduler found nothing due, **not** that capture was proven across all races.

No workflow execution or externally timestamped source capture has been verified at the time of this code change.

### Early collection window update

The race-card polling eligibility window now begins **180 minutes** before the listed deadline (previously 60). This changes when a race is first considered, but does not itself prove upstream data availability or GitHub Actions run success. Repeated 10-minute probes provide time-series evidence; all successful snapshots must be audited against their raw CSV.
