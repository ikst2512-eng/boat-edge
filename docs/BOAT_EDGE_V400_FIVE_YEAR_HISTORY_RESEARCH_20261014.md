# BOAT EDGE V400 — five-year historical research preparation (2026-10-14)

Status: **RESEARCH_ONLY / SYNTHETIC_TESTS_ONLY / NO_ACCURACY_CLAIM**. The historical data have **not** been downloaded, ingested, benchmarked, calibrated, or connected to production.

## Existing work and non-overlap

- `BOAT_EDGE_MASTER_TODO.md` T07/T10/T12/T13 and `BOAT_EDGE_02_RESEARCH_INBOX.md` govern prospective research.
- Draft PR #192 already prototypes conditional first→second→third historical Dirichlet shrinkage; do not duplicate that model.
- Existing V307/V360 owns 120-way relative ranking; V343/V344 owns exact predeadline source replay. V400 only supplies strictly validated offline historical count tables for future evaluation.

## Source and rights

The BOAT RACE official download page (https://www.boatrace.jp/owpc/pc/extra/data/download.html) links national 24-venue results and programs. The existence of downloads **does not establish permission to automate bulk ingestion, redistribute, or use third-party archives**. The original text/LZH schema, licensing, timestamp semantics and normalization rules need source-specific review before any real ingestion. Third-party GitHub code licenses do not automatically license underlying race data. V400 itself has no downloader, API calls, result-page access, or authentication.

## Strict five-year isolation

Data range: 2021-10-01 to 2026-09-30 inclusive. The only permitted latest training cutoff is `2026-10-01T00:00:00+09:00` exclusive. All 2026-10-01+ races and any post-cutoff publication timestamp are prohibited, even if other tracks later unlock data. A policy-reviewed future version would be needed to change this hard stop.

Only a **normalized, locally staged, permission-reviewed** CSV is accepted. Exact header and sorting:

```csv
race_key,boat,racer_id,actual_course,finish,published_at
```

- `race_key=YYYYMMDDjjrr`, jj=01–24 venue, rr=01–12 race; sorted by `race_key,boat`.
- Six different boat numbers, racer IDs, **verified actual courses** 1–6, and finishing positions 1–6. Every six-row event must have the same `published_at` with explicit `+09:00`. Partial, cancelled, irregular-result or scratched events must be documented and excluded by upstream normalization; **never fabricate missing finishes**.
- Require 4-digit racer IDs, strict range and stable race identity. No use of target-event final actual course as a predeadline feature.
- Publication metadata is operator-staged, **not independently authenticated** by this code.

Exact manifest JSON:

```json
{
  "schema": "BOAT_EDGE_V400_STAGED_HISTORY_MANIFEST_V1",
  "csv_sha256": "<actual sha256 of normalized CSV>",
  "source_name": "<operator-provided historical source>",
  "source_locator": "<original source identifier>",
  "rights_evidence": "<reviewed source permission/terms identifier>",
  "rights_review_status": "OPERATOR_REVIEWED_OFFLINE_RESEARCH_ONLY",
  "normalization_protocol": "<documented original format converter version>"
}
```

This attestation is not a legal authentication. The manifest digest and CSV SHA-256 are included in the output; downstream reviewers must verify origins, real permission and timestamp validity separately. Never commit raw licensed historical datasets or manifest secrets into public GitHub.

## Offline CLI once genuine provenance is established

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/boat_edge_v400_five_year_history_research.py \
  --staged-csv /secure/history_normalized.csv \
  --manifest /secure/history_source_manifest.json \
  --as-of-jst '2026-10-01T00:00:00+09:00' \
  > /secure/research_counts_v400.json

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tests -p 'test_boat_edge_v400_five_year_history_research.py' -v
```

V400 prints JSON only; it never modifies production weights, workflows, stored predictions, Formal Fresh status, scores or Pages assets. The output is descriptive counts: for each `venue/course`, `racer/course`, and `all/course`, record separate 90-, 365-, 1095- and 1826-day counts for sample/first/second/third and an independent 180-day exponential half-life weighted count. Overlapping windows **must not be summed together**. These are not calibrated win probabilities, a trained model, or an accuracy measurement.

## Remaining promotion gates

1. Review native official archives' rights and exact historical result+program layouts. Write a separate versioned normalizer, with source byte SHA, temporal source availability and coverage audits by year/venue; do not invent historical metadata or outcomes.
2. Independently audit actual-course identity, scratched/cancelled/unfinished cases and normalization exclusions.
3. Use genuine **pre-race** input snapshots with correct as-of dates, never retrospectively fabricated prediction captures. Target final course is never a predeadline feature.
4. Run chronological holdout and truly untouched future paired predeadline tests: current baseline vs 90-day, 1-year, 3-year, 5-year+recency candidates; identical race cohorts and Top3/Top5/Top10 ticket counts; distinguish 1着, second/third miss, Brier/log loss and confidence intervals.
5. When supported by real data, coordinate with existing 02 draft PR #192 and the 01 production owner. Until multi-day untouched improvement is verified, model adoption is forbidden.

At inspected time `2026-10-14T03:17:01+09:00`, `data/formal_status.json` reported `formalFirst100.races=0`, and `results_seen=false`, `unlock=false`, `scoring=false`, `RESULT_UNLOCK_TOKEN=null`. It is only a dated snapshot, not a continuing claim.
