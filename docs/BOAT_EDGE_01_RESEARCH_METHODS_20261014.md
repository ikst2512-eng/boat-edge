# BOAT EDGE 01 — 自走開発・重複解消・公開安定化の追加調査

Date: 2026-10-14 JST. OWNER: 01 (main/workflow integration). RESEARCH_ONLY; this change is documentation, not an operational workflow fix.
Shared contract: `docs/BOAT_EDGE_3_TRACK_HANDOFF.md`. Read live main, open PRs and `data/formal_status.json` before any execution involving race outcomes. All formal locks remain intact.

## New external engineering evidence

- GitHub workflow concurrency: https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency
  Different workflow instances can overlap; concurrency groups can suppress duplicates but the default pending policy may cancel an older pending job. Simply inserting `cancel-in-progress: true` everywhere may worsen missed pre-deadline freezes. Design separate policies for dispensable UI preview vs indispensable capture.
- GitHub deploy control: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments
  Job-level concurrency and deployment environments can serialize publishing. A successful job alone is not evidence that the current UI SHA was deployed.
- GitHub Pages Actions publishing: https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages
  `upload-pages-artifact` + `deploy-pages` supports an explicit build/deploy boundary, permissions and environment. Treat the Pages publishing source as an architecture decision after current config inspection, not something to switch blindly.
- GitHub artifact attestations: https://github.com/actions/attest and https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts
  Optional signed build artifact provenance / immutable test artifacts may improve release traceability; not a substitute for authoritative provider bytes or true first-seen time.
- GitHub reusable-workflow concurrency caveat: https://github.com/github/docs/blob/main/content/actions/reference/workflows-and-actions/reusing-workflow-configurations.md
  Calling/reused jobs must not use identical cancellation groups if this can cancel the parent.

## Existing repository evidence — avoid duplicate work

- `docs/BOAT_EDGE_01_V303_WRITER_OWNERSHIP.md`: retired old site-v98, v99, v114, v120, v124 auto triggers after tracing successor owners.
- `docs/BOAT_EDGE_01_V304_HISTORY_OWNERSHIP.md`: retired v123 and v129–v132, preserved v133.
- `docs/BOAT_EDGE_01_V343_WRITER_CLASS_HANDOFF.md`: detected potential path collisions; examples `auto-update.yml` staging `data` vs `site-odds.yml` staging `data/site_odds`, exact `data/site_current_state.json` overlap between v133/v134. **Candidate only, not verified concurrent duplicate writes.**
- `docs/BOAT_EDGE_01_V356_RETIRED_V185_RELAY.md`: narrow retirement of dormant V185 relay while protecting scheduled V185 owner.
- `.github/workflows/boat-edge-v350-actions-evidence.yml`: scheduled read-only V351 export of Actions temporal hints and artifacts; explicitly *does not prove duplicate writes*. Reuse, don't recreate.
- `BOAT_EDGE_MASTER_TODO.md` T01/T02/T03/T05/T06 and `AGENTS.md` retain actual acceptance gates.

## P0 proposals — each requires 01 review and controlled PR

1. **Per-path writer ownership ledger**: `output path prefix → scheduled owner → dependency consumers → last verified successful run → SHA / timestamp → successor evidence`. Include directory-parent vs literal-path collisions and dynamic git add unknowns. Retire only a proven obsolete trigger, preserve manual fallback and freezes.
2. **Actual collision proof**: For each candidate pair log `run_id, event, head_sha, start/end, staged paths, resulting commit, touched blob hashes`. Overlapping schedules or same-start alone is not collision proof. Reconcile newest source data and commit ancestry before disabling anything.
3. **Split high-frequency source updates from UI releases**: first measure whether UI Pages is redundantly rebuilding from data-only commits and whether the published site consumes those data paths. Explore dedicated data branch or artifact / immutable versioned JSON strategy **only after** proving data freshness and the present static-site contract survive. Never fix cancellation by simply ignoring race-data commits if that makes active displays stale.
4. **Deploy-only latest intended UI**: enforce one deploy owner, explicit `main UI change SHA` and its published asset SHA. A Pages success on an unrelated data commit does not certify a new UI version; a cancelled obsolete deploy is not inherently bad if the latest intended UI is successfully deployed.
5. **Capture reliability SLO**: at actual decision windows compute `eligible count, source completeness, official 120 odds count, beforeinfo six unique boats, missing/published_wait/parse_error, first_seen < deadline, immutable freeze rate`. Investigate cron gaps and workflow_run triggers separately; do not backfill missed predictions.
6. **Autonomous AI truth-in-status**: distinguish workflow SUCCESS, actual model-edit step executed, diff produced, independent fixture CI, merged, deployed and Safari verified. Don't mistake an empty task queue or skipped Codex step for autonomous progress.

## Suggested acceptance evidence
- CI fixture for retired-trigger non-revival, writer owner overlap classes, concurrency cancellation invariants and unchanged raw frozen bytes.
- Reports with before/after weekly collision/cancellation counts and source-completeness, using matched scope.
- Current Pages deployed SHA equal intended tested UI SHA; Safari runtime pass separately.
- No production model weights, formal status, result/payout/combined endpoints or live wagers touched by research notes.

## Handoff
02 supplies tested model/data schema PRs; 03 supplies UI-only PRs. 01 serially integrates after conflict inspection. No simultaneous main edits by 02/03 and no blind force push. As of 2026-10-14 00:12 JST: PR #200 (03 blocked/null forecast status) is already merged; PR #203 (01 V202/V203 Pages SHA lineage monitor) is already merged with exact-sha Pages SUCCESS. Open 02 PR #192 and 03 PR #202 have independent scopes; verify their actual HEADs and CI before any integration. V360 Pages lineage improves proof, but T01 cancellation churn and Safari gate remain open.
