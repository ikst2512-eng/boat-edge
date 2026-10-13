# BOAT EDGE 02 | source-use and feature evidence matrix | 2026-10-13 JST

This is a **documentation/source-policy** audit, not downloaded outcome data. No page-specific data values, race results, payouts, BOATERS data, Kyoteibiyori data, or restricted content were ingested into a model by this audit. Reviewing publicly posted policy text does NOT establish acquisition or AI-training permission. An URL alone is not an immutable SHA/timestamp attestation.

## Verified publication versus permitted ingestion

| Provider/source | What publication shows | Operational permission and freshness gate | Current label |
| --- | --- | --- | --- |
| BOAT RACE official “download and others” `https://www.boatrace.jp/owpc/pc/extra/data/download.html` | Official lists national 24-venue race-result downloads, program downloads, and twice-yearly racer stats | Official site policy `https://www.boatrace.jp/owsp/sp/extra/policy.html` restricts unauthorized copying/reuse beyond law and prohibits disruptive bulk traffic. Data being downloadable does not establish permission for BOAT EDGE automated acquisition/AI training; request/review explicit scope before ingestion. No protected formal-Fresh result. | SOURCE_DISCOVERED / RIGHTS_NOT_YET_VERIFIED |
| Official data index `https://boatrace.jp/owpc/pc/extra/data/index.html` | Racer and venue statistics, race records | Existing site usage and publication are not proof of historical “as-of” availability or 1y/6m/3m source-by-racer completeness | AVAILABLE_AS_REFERENCE / TRAINING_NOT_APPROVED |
| Shimonoseki venue course-by-racer `https://www.boatrace-shimonoseki.jp/sp/index.php?page=raceinfo-racecourse` | Course-by-racer result summaries, period labelled on page | Aggregated rates **cannot** be used to derive ordered final 2nd given escape head or final 3rd given ordered head-second without matching joint event counts. Access/rights must be separately established. | REFERENCE_ONLY / JOINT_COUNTS_MISSING |
| BOATCAST official exhibition explanation `https://www.boatrace.jp/owpc/pc/site/news/2025/07/44414/` | Official exhibition time vs per-venue original 1-lap/turn/straight distinctions | Measurement schemes differ across courses/venues. Treat source as description only, numeric values need licensed source + six-racer same-race provenance. | MEASUREMENT_CONCEPT_IDENTIFIED |
| BOATERS terms `https://boaters-boatrace.com/info/terms` | Prohibits scraping/crawling or similar access and restricts purpose of supplied information (term 8) | BOATERS numeric feeds NOT ingestible under unreviewed terms; permission required even for downstream training | NO_AUTOMATED_INGEST_WITHOUT_PERMISSION |
| Kyoteibiyori terms `https://kyoteibiyori.com/terms.html` | Explicitly prohibits automated access, scraping, mass collection and use for AI analysis/training without prior permission (term 5) | No crawler, scripted download, reconstruction, third-party numeric redistribution; do not use data for training absent permission | NO_AUTOMATED_INGEST_WITHOUT_PERMISSION |
| Japan Meteorological Agency observations `https://www.data.jma.go.jp/risk/obsdl/` | Station/period/field CSV for wind, temperature, pressure etc | `https://www.jma.go.jp/jma/kishou/info/coment.html` says standard public-data use applies to most public content with source attribution; check item-specific exceptions, source distance, missing/QC flags, change history. Historical CSV download is not same-day live data; respect traffic guidance. | POTENTIALLY_USABLE_AFTER_LICENSE_AND_EVENT_TIME_REVIEW |
| JMA tide data format `https://ds.data.jma.go.jp/kaiyou/db/tide/sea_lev_var/format_download.html` | Hourly level / quality flags / per-station reference datum / JST | Tide level alone is NOT an observed BOAT RACE venue current. Need spatial/time/height-datum and actual as-of evidence, license. | POTENTIAL_HISTORICAL_CONTEXT / NOT_VENUE_LIVE_FLOW |

## Existing implementation cross-check

- V148–V154: historical conditional head/second/third, internal wall/attack worlds and retrospectively evaluated folds. EXISTING_RESEARCH, not untouched Fresh or production CURRENT.
- V180/V185/V199: site shadow conditional ranks and second/third role/exhibition support. EXISTING_SHADOW.
- Merged PR #161: V360–V370 source/provenance and 3×120 **research** scenarios. EXISTING_RESEARCH.
- Draft PR #192: separate training-only hierarchical Dirichlet 120, strict pairwise equal-ten pre-result contract, now the **course-1 escape-only 20-way** conditional estimator with synthetic tests. NEW_RESEARCH_ONLY.
- Site CURRENT policy expressly states 120 calibrated probabilities and user/racer actual-course 1y/6m/3m + 2-course 逃がし + season/tide/venue interactions are **not fully connected**; do not promote non-CURRENT research.

## Priority gaps / definition-of-done, not claimed solved

| Priority | Feature family | Required new authorized evidence / inference caveat |
| --- | --- | --- |
| P1 | Actual-course-1 **escape (winning method 逃げ)** -> 2nd, and ordered 2nd -> 3rd | Historical independently confirmed **actual** course mapping, winner kimarite, six official finish placements, coherent joint event sample by preceding day, seasonal/venue/racer stratification, and permission. This must never be conflated with boat #1 winning or “first on backstretch.” |
| P1 | 2-course 逃がし, 1-course 差され, ST histograms / top ST | Explicit formal event labels and pre-race-only ST history; distinguish null race ST, false starts, ST. Exhibition ST residual requires archived exhibition paired to later confirmed ST for training; NOT same-event future ST as input. |
| P1 | Conditional calibration and paired Top3/5/10 | Predeadline first-Git-added parent and candidate full 120, exact 10 BOAT bets each, same six boat scope/source byte digest, no outcomes opened at freeze; separate authorized SITE research scorer and unchanged Formal guard; report N/day/subgroup, Δpercentage-points and CI; no Cherry-picked race selection. |
| P2 | Racer 1M resist, wall/attack/beneficiary & 5–6 exposure | Authorized annotated turns/interaction labels. Final finishing place/odds is not proof of an in-race physical action. |
| P2 | Deep-in, slow/dash, corner | Training-only final actual course/permitted race sequence vs pre-race predicted entry; no current-race final actual course injected predeadline. |
| P2 | Original exhibition 1-lap, turn, straight and motor change | Two commercial site checks blocked for automated use absent specific grants. Official venue-original measurements, where independently license-approved, are separate provenance. Within-6-racer differences only with six measured entries; venue-specific scale/measurement clock cannot be assumed equal. |
| P2 | 1y/6m/3m per racer+actual-course / motor recent meet+parts | Official source with event-time provenance, equipment identity stability and population counts; no missing 3m values simulated from 6m. |
| P2 | Venue wind/tide/temp and same-day LIVE water | Timestamped official observations **available before freeze**; past already-finished races only when independently authorized, never Formal results. JMA daily historical CSV cannot be used as evidence of same-day live observations. |

## Mandatory acquisition manifest schema for future rights-approved source

Do **not** populate with guessed digests or pretend that a manually entered timestamp is a Git-verified first publication time.

```json
{
  "schema": "BE02_AUTHORIZED_SOURCE_MANIFEST_V1",
  "provider": null,
  "source_url": null,
  "scope_purpose": null,
  "license_or_permission_document": null,
  "permission_document_sha256": null,
  "rights_review_status": "NOT_VERIFIED",
  "collection_method": null,
  "permitted_rate_and_automation": null,
  "first_server_observed_jst": null,
  "first_git_commit": null,
  "first_git_commit_server_time": null,
  "raw_sha256": null,
  "cohort_manifest_sha256": null,
  "data_date_cutoff": null,
  "fields_available_as_of_pre_result": [],
  "independently_audited": false,
  "eligible_for_model_training": false,
  "eligible_for_formal_fresh": false
}
```

Research note: current CI can validate **code shape and fixtures**; it cannot attest that the user's provider rights have been granted. Do not unlock Formal Fresh based on this matrix.

## Handoff boundaries

01: permission ledger integration/review and official source acquisition/deployment after rights clearance; Git-server first-commit proof, main merge, CI and rollback. No automatic source crawl without valid authorization. 03: label research/current, missing or unverified source, model ID + evidence/version, separate head vs ticket confidence. No UI claim of calibrated 120-way scores until actual independent calibration. 02: independent per-feature ablations, ethical source manifests, prospective identical-ten freeze contract, scoring design only when rights + separate SITE-only result gate are verified. No result access in this documentation.
