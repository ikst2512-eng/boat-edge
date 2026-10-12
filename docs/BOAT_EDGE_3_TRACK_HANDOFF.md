# BOAT EDGE — three-chat ownership and handoff contract
Established: 2026-10-13 JST. Scope: coordination only; this document does not change running jobs, site files, model weights, or Formal Fresh status.

## Workstreams — fixed titles and owners

| Track | Chat title | Exclusive responsibilities |
| --- | --- | --- |
| 01 | 【BOAT EDGE 01】GitHub統括・自走開発・重複整理 | GitHub Actions inventory and safe deduplication, shared writer ownership, cross-track conflict resolution, common workflows, CI, merge to main, Pages deployment and end-to-end release verification, central progress tracking |
| 02 | 【BOAT EDGE 02】AI予想・的中率改善・未見検証 | Official/BOATERS/競艇日和 source provenance, scratch/entry/exhibition/pre-deadline evidence, forecast model and 120-triplet evaluation, odds, immutable freeze, prospective Fresh comparisons, virtual ¥50,000/day simulation; research and candidate PRs only |
| 03 | 【BOAT EDGE 03】サイト制作・UI改善・表示完成 | iPhone/Safari UI, six-racer comparison, selected-racer head picks, race-flow explanation, displayed source freshness, verified odds, Top3/5/10, results labels and navigation; UI PRs only |

## Nonoverlap and integration rules

1. Track 01 is the **single owner of main integration** and common GitHub Actions workflow edits. Tracks 02 and 03 propose changes using dedicated branches and PRs; they do not push to main or change common workflows independently.
2. Track 02 owns prediction logic and data evidence; track 03 consumes only verified/versioned output and owns presentation logic. Shared schemas, API/data contracts, or files touched by both must be negotiated in the PR and integrated by 01.
3. Before editing, read current main and open PRs. Do not overwrite concurrent changes. Record branch, files, base SHA, test runs and deployment evidence. If two PRs touch the same file, 01 serializes/rebases after tests.
4. Use current observed implementations and model IDs rather than assuming V235/V236 are latest. V235/V236 are a historical baseline, not guaranteed final versions.
5. Preserve earlier dedup: docs/BOAT_EDGE_01_V303_WRITER_OWNERSHIP.md and docs/BOAT_EDGE_01_V304_HISTORY_OWNERSHIP.md. Do not disable a scheduled source owner without a verified successor and evidence of its consumers.
6. CI success, PR merge, Pages success, mobile runtime verification, and statistically supported accuracy improvement are distinct outcomes. Never report one as proof of the others.
7. ChatGPT conversations are **not automatically synchronized**. This checked-in contract and linked PRs are the shared handoff record, not a claim of live synchronization or background autonomous work.

## Safety requirements

Follow AGENTS.md. Read data/formal_status.json before any outcome access; Formal Fresh PRE_RESULT/result-unseen locks and independent promotion gates remain untouched. Never backfill or reconstruct pre-deadline predictions. Unverified source values remain missing. Never change real-money betting or execute wagers. Research candidates must pass valid prospective gates before any production promotion; default virtual cap remains ¥50,000 per day.

## Mandatory track handoff format

- Track: 01 / 02 / 03
- Base main SHA and branch / PR number
- Exact changed paths and new schema/model IDs, if any
- Synthetic/fixture tests and GitHub Actions run links with conclusions
- Publication stage: prepared / pushed / CI passed / merged / Pages deployed / runtime verified
- Pending issues, blocked dependencies, and files that other tracks must not edit
- Any risk to Fresh lock, pre-deadline provenance, shared writers, or results scoring

## Delivery sequence

01 audits and protects integration ownership first; 02 and 03 develop in parallel on separate branches; 01 serially merges only tested and conflict-resolved PRs, validates Pages/runtime, and tracks remaining completion gates.
