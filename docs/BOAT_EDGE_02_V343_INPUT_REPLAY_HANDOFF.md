# BOAT EDGE 02 — V343 exact research input preservation and replay

Track 02; tested against main `f80cda33d90b817b42964502fe5b6e1e368677a1`.
Branch: `feature/02-v343-race-input-replay-20261013`. Track 01 owns integration.

## Problem and behavior

V332 records the SHA256 of the input `data/races/<race_key>.json`, but V336's
uploaded artifact previously contained only frozen candidates and three HTML
captures/receipts. The changing race input was absent, so its features and all
three candidate outputs could not be independently reproduced from that bundle.

V343 preserves the exact bytes read before source capture as
`data/source_captures/<date>/<race_key>/race_input.json`. The existing V336 upload
glob includes this file without changing any common workflow. A later race-card
update cannot replace the bytes used by the candidate. An interrupted capture
can reuse an identical snapshot; a different snapshot is never overwritten.
Source freshness is checked again at the final freeze instant.

`scripts/boat_edge_v343_race_input_replay.py` accepts one explicit V336 run report
and extracted artifact root. Before opening artifacts it rejects invalid report
flags, paths, hashes and the locked 2026-10-01 formal date. It verifies the
report's frozen JSON SHA, the original race input SHA, and reconstructs every
V312 candidate field at the frozen time. Recomputing internal hashes after
editing candidate tickets still fails replay. Missing snapshots, stale input,
symlinks and elevated research claims fail closed. Zero completed freezes do
not produce a verified replay claim.

```sh
python3 scripts/boat_edge_v343_race_input_replay.py \
  --root /explicit/unpacked/v336-artifact \
  --report /explicit/v336_report.json
```

## Isolation and limits

- Changed paths: V332 capture implementation, new V343 verifier, synthetic V343
  regression and this handoff. No UI, production weights, shared workflow,
  formal state or scoring implementation changes.
- Frozen JSON schema/model IDs remain V332/V312. V343 is an evidence verifier,
  not a new predictive model or adoption decision.
- Exact replay establishes reproducibility against supplied local bytes only.
  V340 raw HTML/receipt verification is a separate check. Provider fields,
  source authenticity, capture timestamps, first-seen Git/server provenance,
  actual entry and global unique cohort history remain unverified.
- Existing artifacts without race_input.json cannot be repaired by reading
  today's changing race card. No historical backfill is performed.
- No result endpoint/page, payouts, combined API or formal outcome was read.
  Formal locks and improvement/promotion claims remain false.

## Synthetic validation and next step

Local checks including the V344 extension: 264 Python regressions (262 passed, 2 skipped), seven V271
JavaScript checks passed, all five workflow source pins matched, diff whitespace
clean. The V343 cases are included in the Python total. No workflow edits.

V343 regression covers exact byte replay without current race-card/formal files,
mid-capture input changes, missing snapshots, raw/candidate/freeze mutations,
staleness during capture, interrupted retry, file/ancestor symlinks, bad flags,
formal target rejection and empty reports. Two independent synthetic runs produce
identical snapshot, frozen JSON and replay report bytes. These are fixture tests,
not an independent Formal Fresh Run1/Run2 PASS.

After Track 01 reviews/merges the PR, a future successful V336 capture should
include the snapshot automatically. Inspect its actual artifact before claiming
live completeness. Combine V339 cross-run collision checks, V340 source-byte
integrity and V343 candidate replay before any separately authorized research
comparison; this PR does not authorize outcome access or Formal Fresh scoring.

## V344 extension — one command for the three local evidence checks

The same PR also includes `scripts/boat_edge_v344_site_research_evidence_gate.py`
and 13 additional synthetic regression cases. It validates every explicitly
supplied run report before artifact access, requires each selected race to have
a completion or declared failure, and combines V339 collisions, V340 frozen
JSON/HTML/receipt integrity and V343 exact candidate replay. A missing report
entry cannot silently remove a difficult race from the batch denominator.

```sh
python3 scripts/boat_edge_v344_site_research_evidence_gate.py \
  --bundle /explicit/bundle-one /explicit/report-one.json \
  --bundle /explicit/bundle-two /explicit/report-two.json
```

CLI exit 0 means only `LOCAL_EVIDENCE_CHECKS_PASSED_NOT_FORMAL` for the supplied
bundles. Empty captures, repeated races (even identical hashes), divergent
freezes, capture failures, missing inputs or byte/replay failures exit 2 with
explicit diagnostics. Invalid scope/report contracts fail before artifact reads.
No gate result attests complete Actions history, true source fields, independent
timestamps, actual entry or prospective accuracy; scoring and promotion remain
unauthorized. No network, output mutation, workflow integration or result read
is added. This is a verifier ID, not a production prediction model version.


## V360 extension — complete three-mode 120-way predeadline research record

Added in Track 02 to the same PR, without changing the V312 research
candidate itself or the production model. V332's already-gated, live-only
freeze now generates and embeds:

- research_ranked_120_schema = BOAT_EDGE_V360_PREDEADLINE_RESEARCH_RANKED120
- research_ranked_120_by_mode: national_only, national_motor,
  national_motor_st, each with exactly **120** ranked objects:
  rank, course_combo, boat_combo, relative_model_mass.

Ranking uses the V307 Plackett–Luce **relative, uncalibrated model mass**,
not payout odds or measured win probability. Each course combination is
mapped to a **boat-number** combination using the provisional start-exhibition
course permutation, NOT independently verified actual entry. The original
three candidate hypotheses, their Top10 order, and head-mass fields are
unchanged.

V360 independently reruns the three fixed V312 feature hypotheses,
validates 120 unique course and boat combinations per mode, normalized
mass 1, exact positional Top10 equality in both course and boat labels,
and all six course-head and boat-head totals. Any mismatch aborts the
V332 freeze before its frozen JSON is written. The output cannot be
generated by V360 independently of the V332 live predeadline freeze.
Existing V336 artifact upload already includes the enlarged frozen V332
JSON; no shared workflow edit.

V343 offline replay uses the preserved V343 race_input.json and V332
candidate at the self-declared freeze instant, then recomputes and
compares all 360 saved rows. Altered row, rank, mass, missing mode or
inconsistent schema fails. Pre-V360 frozen records missing both fields
are explicitly marked all_supplied_full_120_verified=false and are
**never backfilled**. V344 reports all_supplied_full_120_rankings_replayed
separately from its local evidence PASS, so Top10-only does not become a
claim of 120-way persisted evidence.

Synthetic regression:
tests/test_boat_edge_v236_v360_ranked120.py verifies full-card rank
uniqueness, mode Top10/head parity, course-to-boat swaps, replay without
current cards, tamper detection even after rehash, missing modes,
legacy-only records, deadline guards, immutable retry and replay
determinism. This is not a validated source timestamp, actual-entry
record or independently verified model probability.

Track 01 still owns PR merge and live V336 artifact confirmation.
No main merge, Pages publication, actual future capture, Formal Fresh
Run1/Run2, scoring, site prediction change, model promotion, or proven
accuracy improvement is claimed by this PR.


## V361 extension — explicit source readiness reason at race selection

New V361 is a read-only preflight derived from the exact bytes V334
read while selecting current-day predeadline PRE_RESULT race cards. V334
attaches selection_scan to each candidate and, if freezing fails, its
failure row. It distinguishes:

- official race_card and beforeinfo statuses and self-reported ages
  (race_card >16min; beforeinfo >15min remain stale, never accepted);
- start-exhibition rows with an **explicit** course field; six boat/ST
  observations without the six-course permutation are NOT mapped from
  lane number to course number;
- six racer rows with usable national win rate, motor quinella rate and
  average ST, with no imputation;
- input SHA256 at **selection**, explicitly not proof that V332 used
  identical bytes at its later freeze attempt.

V361 may only run after V334 has verified that the day and PRE_RESULT
locks match and the deadline is future. Any result-bearing race document
is rejected. It neither calls providers nor loosens the V312/V332 freeze
gates; the original freeze attempt and error code remain authoritative.
The full diagnostic in V336's JSON job report helps identify which
upstream inputs to repair without misreporting a green Actions job as a
successful research freeze. No historical candidate recovery.

Observed operational examples on 2026-10-13 (JST), before any V361
post-merge live artifact exists:

- 15:06 V336 run 38354920151: selected 5, frozen 0.
  Three course/metadata readiness failures and two beforeinfo not-ok.
- 15:35 V336 run 38357552542: selected 3, frozen 0.
  One readiness failure and two stale race-card metadata failures.
- Stored race 20261013-15-02 has six start-exhibition lane/ST rows but
  no explicit course keys: it is **not** six-course-qualified merely
  because a separate coverage flag says six boats are present.
- Stored race 20261013-04-11 has later updated source timestamps than
  the earlier failed V336 execution; an updated Git file after the
  execution cannot retroactively make a prior freeze valid.

Regression tests: tests/test_boat_edge_v236_v361_source_readiness.py.
These exercise healthy synthetic cards, course missing, both stale
sources, missing average ST, bad PRE_RESULT/locked/result flags, closed
deadline, input SHA, and diagnostics attached to failure records.
No source freshness threshold, actual-entry claim, model weights,
formal locks, public site UI, or Actions workflow file is changed.

Track 01 still owns main integration and upstream collector work.
After merge, actual success is counted ONLY if a genuinely new
predeadline freeze with source receipts and all three 120-row lists
passes V344/V343; Actions exit status alone is insufficient.


## V360/V361 naming correction and V362 labelled official start-table proof

Track 01 merged unrelated V345 writer-trigger evidence and V346 runtime
duplicate proof to main while Track 02 was developing. To avoid two
different features sharing version identifiers, Track 02's full-ranked
research module/test was renamed **V360**, and selection-time source
diagnostic module/test was renamed **V361**. V312 (hypotheses), V332
(immutable local freeze), V343 (exact replay), V344 (evidence audit) and
the existing V336 Actions workflow are unchanged in name.

**V362** adds a source-backed, strictly optional repair for
V332 candidate input containing six start-exhibition ST entries but no
explicit course indices:

1. Require an existing same-race official pre-result HTML file at
   data/raw/<date>/<venue>_<round>_beforeinfo.html. Neither a network
   fetch nor a substituted race/venue is attempted.
2. Require its SHA256 to equal the same PRE_RESULT race card's
   source_audit.beforeinfo.sha256 and its source URL to be the exact
   official beforeinfo endpoint for that race. Existing 15-minute
   beforeinfo and 16-minute race-card freshness constraints, six
   racer-feature requirements and all formal/result locks stay active.
3. Identify **one** official table labelled スタート展示 with
   explicitly labelled コース / 並び / ST headers. Require exactly
   six rows, unique boat numbers, matching printed boat image IDs,
   six verified ST strings that agree with the race input, and no
   conflicts with any already recorded course indices.
4. Only when these tests pass, assign course=official-labelled-table
   **row position** in a local candidate copy. This is not inferred
   from boat number and is still the *provisional exhibition course*,
   not independently authenticated final actual entry.
5. Preserve the exact original race_input.json **unchanged** and
   the exact original official HTML as
   data/source_captures/<date>/<race_key>/official_start_beforeinfo.html.
   Record its digest in frozen JSON and candidate; V343 must replay the
   same full 3x120 against both archived originals. Any source
   mismatch, missing/symlinked capture, wrong result/lock status or
   expired deadline aborts without an immutable research freeze.
6. When all six course fields are already valid, the former V312/V332
   path remains unchanged and V362 is unused. No historical V332
   freeze lacking original HTML may be retroactively upgraded.

Synthetic tests:
tests/test_boat_edge_v236_v362_official_start_course.py. Covers
course-swap parity, archived original byte identity, V343 360-row
replay after deleting mutable local cards, mismatched SHA, bad headers,
duplicated boat, icon mismatch, changed ST, conflicting course,
missing source, symlink, closed deadline, lock and formal exclusion.
No real race freeze, authentic upstream timestamp, external network,
official result or model-accuracy claim is established by those tests.

**Operational observation still outstanding:** an actual new
post-merge V336 run must have completed_count > 0, a valid V332
predeadline frozen record, all 3 x 120 persisted rows and a PASS
from V344/V343 on its exact uploaded artifacts. A green workflow
that reports frozen=0 remains zero valid research races.

No change to site UI, production prediction engine, model weights,
official current/future outcomes, formal Fresh results_seen/unlock/
scoring, or main/shared workflow ownership. Track 01 alone handles
PR integration and live source-collector remediation.


### V362 active official race-identity hardening (2026-10-13)

The initially introduced labelled-table proof is insufficient by itself to
exclude identical six-boat/ST data from a **different race**: source URLs
and hashes are recorded metadata, not independent proof of HTML identity.

V362 now requires exactly one official current-race navigation table matching
the saved official markup `div.table1.h-mt10 > table`, with the printed
`レース` header and 12 individually labelled `beforeinfo` links for the
same day and venue. It requires exactly one selected, uncolored race tab and
that tab's R number to equal the frozen race key. The single `締切予定時刻`
row must contain 12 displayed times and exactly one selected-time cell;
that time must equal the frozen race metadata deadline. These checks are
**in addition** to all six original source table boat/icon/ST checks and
SHA256 matching. Any mismatch is a fail-closed exception.

This was designed against actual existing repository official HTML shapes
under data/raw/20261013/{15_02,04_11,12_01}_beforeinfo.html.
Checking those HTML structures is *not* a formal future freeze, server
timestamp authentication, or independent source authorization.

V362 synthetic regression adds wrong venue/date, duplicate/incorrect race
tabs, conflicting selected race, altered deadline and wrong official page
type. It still never reads race outcomes, nor touches main or the live
source refresh workflow. Strictness can lower coverage when source and
race metadata differ; such cases must be reported, never bypassed.


### V363: V230 upstream refresh gap classification (2026-10-13 evening JST)

V334 records new optional V363 diagnostics for every selected future race.
V363 **only** checks whether the independent SITE prediction snapshot path
already exists, then cross-references V361 selection-time source status/age.
It never opens a site prediction, fetches the internet, authorizes a
late/invalid freeze, changes V230 target selection, or touches result data.

The concrete currently checked-in V230 target selector contains
`if (root/'data/site_prediction_snapshots'/f'{key}.json').is_file(): continue`.
Therefore a preexisting regular SITE freeze is a sufficient **structural
skip condition** for V230's later official refresh. V363 records this
potential overlap separately from a stale card that has no SITE snapshot;
it does not assert that this was the sole cause of a particular live run.
Symlink targets are identified but never opened or followed as evidence.

Observed **real** PRE_RESULT publishing timing on 2026-10-13:
- V336 run 38363133649 around 16:31 JST scanned 3R, frozen 0R,
  all reporting `SOURCE_TOO_STALE_FOR_FINAL_WINDOW:race_card`.
- The tracked 20261013-12-04 and 20261013-22-12 card files show Git
  commits at 16:06:56 and then 16:33:05 JST. The later commit is
  **after** the V336 failure; no retrospective validity is inferred.
- Latest V336 run 38394468129 at 21:03 JST scanned 132 cards but selected
  0R and froze 0R (`NO_ELIGIBLE_RACES_IN_CURRENT_FINAL_WINDOW`),
  which is expected when the day's final-deadline window is over.
- Existing V235 target selection can stop refreshing a card when a
  separate SITE prediction snapshot already exists. Track 01 should
  review this dependency and the source publishing cadence, but never
  republish historical source stamps as if they were live.

Synthetic V363 tests in
`tests/test_boat_edge_v236_v363_fast_lane_gap.py` cover four cases:
stale source + existing site prediction, stale source without a
prediction, fresh source with a prediction, and a symlinked path.
The independent SITE prediction file is deliberately invalid opaque
bytes in fixtures, so an accidental read would break the contract.
The classification is diagnostic only, not proof of actual causal history.

Required Track 01 follow-up: establish a **source-only** fresh official
racelist/beforeinfo refresh that is independently validated and available
before the actual final-window research execution for every still-open
candidate, regardless of whether a prior SITE prediction was frozen.
Preserve all official source hashes, timestamps, scratch checks, guards,
race identity and single-writer ownership. Do not weaken freshness,
backdate sources, overwrite immutable forecasts, or change formal
Fresh `results_seen/unlock/scoring`. After eventual merge, the actual
V336 artifact and V343/V344 replay must verify full 3×120 research coverage.

### V364: executable upstream selector contract

`tests/test_boat_edge_v236_v364_v230_v336_selection_contract.py`
actually invokes the existing `boat_edge_v230_fast_lane.targets()` and
`boat_edge_v334_live_batch_runner.live_window()` together on the **same**
synthetic race at an unchanged fixed predeadline JST clock.

The test proves the following narrow implementation behavior:

- Without a pre-existing SITE first-prediction snapshot, V230 can select
  the same upcoming race as V336 even if its race-card metadata is stale.
- Creating that SITE snapshot excludes the race from **V230's source refresh
  target list**, but V336 still selects the race for its independent research
  attempt and reports the stale official race-card metadata.
- The resulting V363 gap report is explicitly diagnostic, not evidence of
  actual provider-side timestamps or a successful refresh.
- After the race deadline, neither selector can admit a new research/refresh
  target. No source/result/odds/payout/network is read or mutated in this test.

This confirms an exact code-path *selection divergence*, not that all
historic V336 failures were caused by the snapshot guard. In the later
mutable main checkout for 2026-10-13, one of the three 16:31 V336 failures
(`20261013-15-04`) had a regular SITE prediction snapshot, while the
other two snapshots could not be confirmed present. Their PRE_RESULT
race-card timestamps had meanwhile changed *after* the failed V336 run;
none of those timestamps retrospectively validates that freeze.

For Track 01, the concrete implementation choice is **separate official
source refresh eligibility from the idempotence of a first SITE prediction
snapshot**. Any subsequent live official-source update must still enforce
the independent source identity, raw bytes/hash, true collection time,
strict predeadline/freshness, scratch/withdrawal validation, and guarded
Git publication. Never overwrite frozen picks or raise the model's
production eligibility solely due to this selector divergence.


### V365: source-refresh-only selection contract for integration by Track 01

V365 provides a new **non-executing, read-only** candidate selector:
`scripts/boat_edge_v365_source_only_selection_contract.py`. It intentionally
does not call V230's network fetcher, write any files, update a site prediction,
or schedule a workflow. It exposes a precise alternative selection contract
for the source-refresh portion of a possible Track 01 implementation.

The contract:
- Read only the present-day PRE_RESULT index and race-card metadata; require
  both the index and race to have explicit results_seen/unlock/scoring=false.
  Reject any race/index carrying result/outcome-bearing top-level keys.
- Select only 2–19-minute future races with identical date, venue,
  race number and deadline between index and actual race JSON. Reject bad
  types, duplicate keys, six-racer absence, or symlinked source/index.
- **Do not use a first immutable SITE prediction snapshot as a reason to
  skip an otherwise safe official source refresh.** Check only file
  existence; never open, hash, parse, rewrite or remove it. Reject symlinks.
- Return a bounded (1–12), deterministically ordered candidate set with
  fail-closed rejection reasons and explicit zero-authority flags.
- No claim of source authentication, race freeze eligibility, historical
  completeness, actual entry, or model accuracy follows from this selector.

`tests/test_boat_edge_v236_v365_source_only_selection_contract.py`
exercises a first-pick snapshot with deliberately non-JSON opaque contents,
no snapshot, deadlines, metadata conflicts, missing racers, duplicates,
symlinks, a locked/result-bearing index and race, and invalid clock/cap.

**Track 01 integration precautions:** V235 currently checks the exact
`scripts/boat_edge_v230_fast_lane.py` Git blob (pin
`569215c933354db691552965bdff9a91fc611460`) before execution. A
change to V230 cannot be pushed to main alone without reviewing and safely
updating the V235 pin and any related concurrency/write-owner guards.
Do not replace V230's existing atomic first-prediction freeze with a
source-only selector; instead separate the refresh of verifiable current
official bytes from the optional creation of **first** site predictions.
Keep existing official URL/redirect validation, scratch, odds, beforeinfo
coverage, immutable prediction and Git conflict guards, and the strict
deadline checks at both fetch and publish time. A data refresh after a
race's deadline is not a prospective observation. Never present existing
same-day mutable Git card timestamps as proof of source freshness for a
prior V336 run.

After an independently checked Track 01 main integration, monitor a
genuinely *new* eligible V336 live run and confirm completed_count > 0;
validate its original input and HTML SHA and replay its complete 3x120
through V343/V344. A V365 test PASS alone does not do any live updating.


### V366: isolated immutable source-only official capture proof

Added `scripts/boat_edge_v366_isolated_source_only_capture.py` with explicit
opt-in `--capture --race-key YYYYMMDD-VV-RR`. Without `--capture`, the
command only prints V365's read-only selection report. **No shared production
site or V235/V336 workflow is modified.** This proof is a distinct research
artifact in `data/research_source_only_v366/<date>/<key>/`.

For a selected 2–19-minute current-day PRE_RESULT race with exact index-card
race ID/date/deadline and all false results/unlock/scoring locks:

1. Refuse the untouched formal 2026-10-01 Fresh date before any local
   input, clock or network read. Refuse an existing same-race V366 proof
   before HTTP, and reject source/index/prediction symlinks and result-bearing
   indexes or race documents.
2. Fetch **only** exact same-race official HTTPS `racelist` and
   `beforeinfo` pages. Existing V315 official URL allowlist applies.
   Require exact returned URL (no redirects), text/html, bounded bytes,
   and selection/deadline rechecks after every response.
3. Verify **all six unique official registration numbers** against the
   current immutable input race card. Reuse V230's labelled exhibition
   table parser to require six valid exhibition times and six ST rows.
   Reuse V362 to check active official page date/venue/R/deadline and six
   labelled start-course boat image/ST rows. An explicit withdrawal
   or absent-participant signal fails closed, even if six rows remain.
4. Re-read and byte-compare the input race document before writing.
   Keep original source bytes, their SHA256, URLs, receipt times,
   provisional exhibition course proof and input race digest in a
   bundled manifest. Reject any close-of-window or modified input.
5. Build a new uniquely named, immutable directory from a separate
   temporary directory; never overwrite any existing V366 proof.
   A retry is rejected **before network fetch**.
6. Never open or modify the first SITE prediction, `data/races`,
   `data/raw`, `data/source_captures`, V332 freezes, odds,
   results, formal state, model weights or published site. Capture
   timestamps are process-local receipt times, not authenticated
   official server provenance.

Verification: `tests/test_boat_edge_v236_v366_isolated_source_only_capture.py`
uses fake HTML/network, locked and formal scenarios, wrong race or
deadline, fake redirects, different registered racers, bad boat icons,
explicit withdrawals, a deadline crossed during HTTP, changed race
bytes mid-request, repeat capture and byte-for-byte preservation of
existing SITE first predictions and race cards. All source-only
assertions remain independent of accuracy/scoring. Code CI
`38399051944` passed 317 tests (315 success, 2 skipped), commit
`db6030b14ff2b91e6627e0ad4146a9684bb46382`.

**Integration boundary:** V366 does NOT feed refreshed fields into the
live site's `data/races`, and does NOT yet make a V336 freeze succeed.
Actual official network source availability, scheduling, conflict-safe
Git publication, V235's pinned V230, and integration with site prediction
provenance belong to Track 01. Track 02's subsequent V343/V344 replay
must verify complete 3 × 120 rows from newly and genuinely frozen
predeadline research inputs; simulated V366 proof cannot establish that.


### V367: exact offline replay of isolated source-only bytes (2026-10-13 JST)

V366 now saves the **unchanged original race JSON bytes** as a fourth
immutable file, `race_input.json`, alongside `manifest.json`,
`racelist.html` and `beforeinfo.html`. Its manifest includes the
archived input's exact relative path and SHA256. Publication uses a
temporary directory renamed once into a race-keyed research-only
directory; a repeat is blocked before HTTP, and the selection/deadline
window plus the exact current race JSON bytes are rechecked immediately
before the final rename. A late staging operation cannot present itself
as a predeadline success.

V367 in `scripts/boat_edge_v367_source_only_replay.py` independently
reads **only these four archived files** to verify:
- Exact SHA256 for input and both original HTML captures, declared byte
  lengths, canonical manifest JSON, exact same-race official URLs and
  canonical filenames; no extra files or symlinks.
- Original archived race ID/day/venue/number, unmodified PRE_RESULT
  guards, and strict chronological ordering of source receipt times
  and as-of date/deadline (bounded 2–19-minute research selection).
- Re-run of registered six-racer parity, six official exhibition times,
  six ST rows, official active race tab/deadline and actual
  **provisional exhibition table row-order**, as well as explicit
  withdrawal/absence checks. All replayed evidence must exactly equal
  the captured manifest's original parsed structures.
- Optional externally retained `expected_manifest_sha256`, so a
  modified manifest cannot be accepted silently.
- Two independent `replay_one` calls return byte-identical canonical
  reports, even after deleting all mutable `data/races`,
  `data/today.json` and existing first SITE prediction files.

Synthetic positive/tamper tests:
`tests/test_boat_edge_v236_v367_source_only_replay.py`. They cover
raw HTML tampering, archived input tampering, manifest edits,
rebuilt manifest SHA with bad official icon, wrong official race URL,
unexpected extra file, false authorization flags, bad chronology,
provisional course field drift, symlink and forbidden formal target.
Separate V366 regression verifies a deadline crossing during **bundle
staging**, not only while performing HTTP.

**Limitations:** replay proves deterministic local integrity of the
archived input/source bytes and a *self-reported* timeline, NOT actual
external capture time, source authenticity, BOATERS/競艇日和 original
exhibition parity, final actual entry, real-race cohort completeness,
improved hit rate or formal Fresh eligibility. This standalone
source-only artifact does not substitute for a V332 freeze or
V343/V344 full 3×120 audit. No historic race is backfilled, and
no result endpoint/payout/combined API is accessed.

**Track 01 owns** review of new source-only integration, main/CI/Pages,
V235's source-collector pin and actual predeadline source publishing.
V367 may help Track 01 check a new source capture *before* deciding
whether/how to publish, but it authorizes no changes by itself.


### V368: explicit non-formal multi-race source-only cohort dual replay

After V367 verified one V366 archived source-only original bundle, V368
adds `scripts/boat_edge_v368_source_only_cohort_audit.py` to verify an
**operator-supplied explicit set of 1–100 archived source-only race
keys and previously retained per-race manifest SHA256 digests**.
No discovery over `data/results`, old dates, SITE predictions,
formal cohorts, or implicit extra V366 archives is allowed.

The caller supplies an exact canonical JSON index (sort all object keys,
compact separators and append one newline). Example **illustrative
only; the digest shown must be replaced with an actual retained SHA**:

```json
{
  "schema": "BOAT_EDGE_V368_EXPLICIT_SOURCE_ONLY_COHORT_V1",
  "source_capture_only": true,
  "no_result_inputs": true,
  "no_formal_fresh": true,
  "no_model_promotion": true,
  "declared_expected_count": 1,
  "expected": [
    {
      "race_key": "20261013-22-12",
      "manifest_sha256": "<actual external retained 64-character SHA256>"
    }
  ]
}
```

The example is shown pretty-printed for readability, not valid CLI
canonical format. The index is *not* synthesized from whatever
archives happen to be present; an absent declared race must fail the
cohort. The index is not independently authenticated by the tool.
The caller is responsible for preserving an external expected list
and digests **as of the original capture, before any result exposure**.

Validation fully completes **before opening any archive**: canonical
key ordering, no duplicates, no Formal 2026-10-01 race key, no optional
result-bearing paths or extra index fields, no malformed digest,
exact declared count and explicit research-only flags. For each
declared key, V367 runs twice independently with exact retained
manifest SHA and verifies the canonical report bytes are identical.
An absent/corrupted archive is recorded as a rejection and
`all_declared_sources_locally_verified=false`; a zero-count group
cannot be declared PASS. An accepted cohort is labelled
`ALL_DECLARED_LOCAL_SOURCE_ARCHIVES_REPLAYED_NOT_FORMAL`.

Fixture-only `tests/test_boat_edge_v236_v368_source_only_cohort_audit.py`
checks valid archive replay after deleting mutable SITE cards, omitted
expected archive, wrong SHA, corrupted official bytes, duplicated and
unsorted race keys, locked/formal index claims, fake replay success
flags, divergent double-run reports and explicit non-access to
`data/formal_status.json`. The 2026-10-13 code CI
[run 38406825185](https://github.com/ikst2512-eng/boat-edge/actions/runs/38406825185)
completed SUCCESS: **337 Python tests; 335 successful, 2 skipped**,
commit `f78dda7dec15dde6fb27873c055d19dd0bbbc8da`.

V368 is **not** V344's full 3×120 V336 research freeze audit,
not proof of cohort completeness beyond the declared external list,
not an external official provider server-time attestation and
not permission to score or promote a model. PR integration, stable
Git-source publication and live runs remain with Track 01. The
formal Fresh 2026-10-01 `results_seen/unlock/scoring` flags must
remain false.
