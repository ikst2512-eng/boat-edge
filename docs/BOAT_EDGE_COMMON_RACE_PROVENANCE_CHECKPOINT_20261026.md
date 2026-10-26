# Common-race provenance checkpoint — 2026-10-26 (research only)

Scope: read-only observations against GitHub main at inspection time. This document does **not** score actual race outcomes, certify Model improvement, establish independent Git publication time, alter Formal Fresh, or authorize deployment. Paths checked are exact known V232/V332 evaluator paths, not an exhaustive search of all artifact stores or workflow artifacts.

## Sampled exact race keys

| Race key | SITE prediction snapshot | V232 cohort record at evaluator path | V332 research freeze at evaluator path | Classification |
|---|---|---|---|---|
| `20261025-04-08` | present; first_saved_at `2026-10-25T05:02:10.616192+00:00`; race_sha256 `991741f442e304aa1d033ff5ff9dcee0b4f78fa0b7b7f99479389b4cd05e7f46` | not found | not found | NOT COMPARABLE — missing frozen pair |
| `20261025-05-12` | present; first_saved_at `2026-10-25T07:00:51.821094+00:00`; race_sha256 `1b6a786b971578aff012b7b85b1684ad6469272a2eb7cc74f8780092ccb72bbf` | not found | not found | NOT COMPARABLE — missing frozen pair |
| `20261025-06-08` | present; first_saved_at `2026-10-25T04:59:55.180379+00:00`; race_sha256 `3867a479a97a8288ff9f118f579de02837f10e8804c22fa59a7082fb60a652be` | present (model_id `SITE_REFERENCE_V122`) | not found | NOT COMPARABLE — candidate freeze missing |

For `20261025-04-08`, SITE snapshot lists deadline `14:12` JST and freeze `14:02:10` JST. For `20261025-05-12`, deadline `16:06` JST and freeze `16:00:51` JST. For `20261025-06-08`, deadline `14:06` JST and freeze `13:59:55` JST. These self-reported snapshot timestamps alone are not independent first-Git attestations. Source-ready observations can postdate the predictions; do not infer same-input parity from a race key.

## Evaluation code status

- `research_next/evaluate.py` validates 120 positive probabilities and date separation, reports top3/top5/top10 and log loss. It does not verify model code SHA, immutable pre-outcome provenance, calibrated probabilities, top1, or uncertainty estimates. `source_sha256` is only syntactically validated.
- `scripts/boat_edge_v335_site_paired_outcomes.py` supports exploratory paired top1/top3/top5/top10 and discordance sign-test, but no full-distribution log loss/calibration and no independent same-input Git/model attestation.
- A chronological split is not evidence that the model was frozen without future labels.

## Required eligibility gate before future scoring

For each **same race**: (1) independently inspect immutable original input bytes and SHA256 used by both models; (2) verify original model code plus parameters/config digests and frozen predictions; (3) inspect first Git add commit/tree containing original bytes with credible predeadline publication evidence; (4) verify the prospective outcome-blind training/model-selection process; (5) only subsequently and independently join real outcomes. Reject unknown or mismatched items with an explicit reason. Do not backfill older predictions, score the currently ineligible cohort, or infer population totals from three sampled races.

Gate 1C remains unresolved: `data/site_ops_v220/gate1c_current.json` reports `independently_source_eligible_denominator: null` and `acceptance_99_percent_proven: false` for both 2026-10-25 and current 2026-10-26 observations. Formal Fresh constraints remain unchanged.

## Next forensic step

Locate any external Actions artifacts or archived Git trees containing corresponding V332 frozen candidate predictions and model digests for these exact race keys, verify source-byte parity and first-Git proof, and only then construct a comparison cohort. Current sample proves only **zero eligibility confirmed among three inspected race keys**, not that globally there are zero eligible races.

## 2026-10-26 follow-up: V232 source-digest cross-check (no outcome read)

For `20261025-06-08`, three tracked documents were independently opened: `data/site_autopilot/v232_cohort/20261025-06-08.json`, `data/site_prediction_audit/20261025-06-08.json`, and `data/site_ops_v220/gate1c_source_ready/20261025-06-08.json`.

- V232 `source_race_sha256` and SITE snapshot `race_sha256` both report `3867a479a97a8288ff9f118f579de02837f10e8804c22fa59a7082fb60a652be`.
- V232 `snapshot_sha256` and V125 audit `latest_snapshot_sha256` both report `1040c0e3d8d8250ccf68861e762756315b6d91f6fcea194f7a6ee1e63c1d7a3f`.
- V232 `odds_source_sha256` and source-ready `source_sha256.odds` both report `fdb7c4b32b05db7adc5e6b143212214a6f923f80888d2910df310f1146ce9e4a`.
- SITE prediction first-saved `2026-10-25T04:59:55.180379+00:00`; later source-ready observation `2026-10-25T05:00:57.031862+00:00`. V232 self-reported `evidence_committed_at=2026-10-25T05:01:50.114128+00:00` does not replace independent first-Git publication proof.
- V332 evaluator-path freeze still not found, so this race remains **NOT COMPARABLE**. Matching recorded hashes establish consistency of reported identifiers, not independent rehashing of original inputs or equivalence of two models.

Branch head `1f822ca1d99054774e11ea702c169d513aa5abf7`: combined commit status API returned no statuses and PR-triggered run lookup returned no runs. Neither result establishes that all GitHub Actions were absent or that CI passed. Local/synthetic test claims must be kept separate from native CI.

## 2026-10-26 integration check (reconstructed local runner)

The exact displayed audit logic and synthetic Git integration fixture from the research branch were manually reconstructed in an isolated execution environment because direct GitHub network access from that environment was unavailable. Ran `python -m unittest -v test_pair_git_integration` and `python -m py_compile *.py`; the one integration test passed and the syntax check completed. The fixture exercised a locally created Git commit, matching original bytes, model digest tampering, input digest tampering, late reported freeze, and the permanent real-scoring HOLD flag. **This does not establish byte-for-byte equivalence of locally reconstructed files to GitHub blobs, native GitHub Actions CI success, trusted predeadline publication, or real-race model performance.** Do not promote based on these tests.

## 2026-10-26 V332 evidence acquisition blocker, verified in main

- GitHub contents API returned 404 for `data/research_local_v332/` and `data/research_local_v332/20261025/` on main. This proves absence at those repository paths at inspection time only; it does **not** rule out untracked local files or artifacts in other workflows.
- `.github/workflows/v336-site-research-live-freeze.yml` is `workflow_dispatch` only and explicitly requires `completed_count == 0`, `capture_requested == false`, and no automatic third-party provider capture. It cannot be used as a source of frozen V332 forecasts, even on a successful run.
- `docs/research_live_capture_v332_v333.md` names `scripts/boat_edge_v332_live_local_freeze.py` as a separately **explicitly invoked, before-deadline** local capture/freeze operation, producing `data/research_local_v332/YYYYMMDD/YYYYMMDD-VV-RR.json` and `data/source_captures/...` receipts. The local receipt is expressly not independent timing/site-authenticity evidence.
- Dedicated research audit CI: no successful run has been verified through available tooling. The pull-request-run lookup returning an empty set is not an exhaustive Actions query; unsupported direct workflow-list requests cannot establish whether runs took place.

**Decision: HOLD.** Do not backfill V332 files for completed races, turn on unattended BOATERS/競艇日和 capture, read formal outcomes, or promote local fixture tests to real-race performance evidence. A valid next prospective case requires independent before-deadline publication receipt, frozen exact input/model/prediction bytes and linkage, and a permitted collection path. Treat the Git-only monitor as a screening tool, not an eligibility certificate.

## 2026-10-26 prospective paired-race acceptance protocol

A future race is **screenable**, not yet scoreable, only when the following independently checkable chain exists **before the published race deadline**:

1. The exact original `data/races/<key>.json` bytes, their SHA256, and each model's complete executable version/configuration/weights digest are fixed; a model label or a single file hash is insufficient.
2. Each model's exact pre-result prediction bytes are fixed and paired to the same original input SHA, with manifest links to those immutable bytes.
3. A third-party timestamp independent of Git author/committer fields (for example, a GitHub Actions run receipt with server-assigned `created_at`, linked run ID and checked upload artifacts) independently establishes that **all three** evidence types existed before the deadline. A later audit upload of an earlier-dated manifest does **not** qualify.
4. First-Git additions, SHA bytes, ancestor relation, prediction-commit tree bytes and fixed versions are checked without opening outcome or Formal Fresh files.
5. Run and artifact retention, repository permissions, and source-rights requirements are reviewed. Existing V336 is an explicit no-capture dry-run and must not be repurposed into unattended BOATERS/競艇日和 scraping.

**Strict HOLD if any element is missing**. Even a local digest PASS is only internal integrity, not independent predeadline publication, actual model usage or result-blindness. Keep outcome evaluation separate and disabled until prospective cohort acceptance. No retroactive V332 freezes.

### Current CI evidence and scope
The GitHub Actions runs listing for research branch `audit/common-race-provenance-20261026` was queried directly. `Research pair provenance audit CI` run [40277222242](https://github.com/ikst2512-eng/boat-edge/actions/runs/40277222242) passed on head `3e35ef618ae0ef1779c8c9b1fc20675a011d958d`. The later `Next research framework tests` run [40321573921](https://github.com/ikst2512-eng/boat-edge/actions/runs/40321573921) passed on head `c1c35027ac2f5ba690ff169e004dde83b4d7f4d3`; its `unit-tests` job ran `python -m unittest discover -s research_next -p 'test_*.py' -v`. There is no demonstrated native CI run on a newer branch head. These are synthetic/software tests, **not forecast skill evidence**.

Research-only model comparison remains HOLD, with independently eligible common-race denominator unknown. Formal Fresh lock and production data are unchanged.
