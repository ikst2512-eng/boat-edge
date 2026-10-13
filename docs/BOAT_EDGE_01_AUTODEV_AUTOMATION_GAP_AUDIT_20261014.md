# BOAT EDGE 01 — GitHub self-driving development: observed blockers, safe design and verification
Date: 2026-10-14 JST. Branch base: `887655f338a13c89dd03da42e13b5f3f04290652`.
Status: **RESEARCH / PROPOSAL ONLY**. This document changes no workflows, model, provider captures, Pages, settings, or Formal Fresh.

## Evidence ledger: tested read-only facts vs unresolved claims

| Area | Observed source or metadata | Meaning and limitation |
| --- | --- | --- |
| Code-edit automation | `.github/workflows/v240-autodev.yml` | V240 can execute `openai/codex-action@v1` *only* when `--pending` succeeds, `main` is selected and an `OPENAI_API_KEY` secret is present. **The actual secret presence and a successful Codex run are NOT independently verified by this audit.** |
| Queue | `BOAT_EDGE_AUTODEV_TASKS.md` & `scripts/boat_edge_v240_guard.py` | A01–A33 appear checked; the guard seeks the **first unchecked** line. No unchecked task => no AI edits, though the cron and preflight may run. A checked task is not proof of agent execution nor Safari pass. |
| Direct main write | `.github/workflows/v240-autodev.yml` last publish step | An approved UI edit currently attempts `git push origin HEAD:main` after rebase; not a PR with reviews/required checks. This conflicts with `docs/BOAT_EDGE_3_TRACK_HANDOFF.md` requiring 01 as sole main integrator. Rework to **candidate PR only** after isolated tests, no direct main write. |
| Workflow token + deployments | V240 uses `GH_TOKEN: ${{ github.token }}` for `gh auth setup-git`; GitHub docs https://docs.github.com/en/actions/concepts/security/github_token | Commits created using repository `GITHUB_TOKEN` generally **do not trigger subsequent push workflows nor a Pages build** (except documented dispatch and PR pathways). Thus V240 push success cannot by itself imply Pages published the new UI. Audit whether an explicit Pages dispatch exists before changing the release route. |
| Existing governance | GitHub repo metadata 2026-10-14 | `allow_auto_merge=false`, `default_branch=main`. Main branch endpoint reported `protected=false`. Separate branch protection details endpoint returned 403 for the connector, so **rulesets and required CI status are not fully audited**. Don't assume settings are already configured. |
| Existing AI secret dependency | `V240_AUTODEV_README.md` | The OpenAI API key is an independently billed credential; ChatGPT subscription/ChatGPT scheduled research is **not** a substitute. Never put credentials in chat, README, PR, log or issue. |
| Background Actions | `BOAT_EDGE_MASTER_TODO.md`, V351 scheduled run evidence, V343 path ownership | Several jobs can schedule and write; overlap inventory is not verified collision proof. Don't create another 5-minute updater or replace stable source owners. |
| Official sources only while locked | `data/formal_status.json` (2026-10-13 23:59 JST) | First100=0/100, `results_seen=false, unlock=false, scoring=false, RESULT_UNLOCK_TOKEN=null`; this document never accesses or authorizes results/outcomes. |
| Third-party capture compliance | Existing GitHub Issue #204 | The V336 scheduled research pathway deserves authorization review before any more third-party provider automation. Not duplicating issue or introducing more scrapers. |
| Parallel development | Currently open 02 PR #192, 03 PR #206 at first review | 01 owns main; don't auto-replace 02 candidate model or 03 UI revisions. Final merge at exact current PR SHA after recheck. |

## Research-backed automation architecture (minimal viable, no new duplicate collector)

### Phase 0: instrument gates before writing automation
1. Read-only report each day: latest main SHA, active workflow owners, V240 first-pending task ID or QUEUE_COMPLETE, key presence state as YES/NO/UNKNOWN from *existing safe job summary* not the secret itself, latest Codex step outcome RUN/SKIPPED/FAILED, commit produced, test result, PR branch/head SHA, Pages run/deployed SHA, Safari status.
2. For failures distinguish `NO_APPROVED_TASK`, `MISSING_AI_CREDENTIAL`, `AGENT_SKIPPED`, `AGENT_FAILED`, `UNSAFE_DIFF`, `PR_CI_FAILED`, `MERGE_BLOCKED`, `PAGES_NOT_DEPLOYED`, `SAFARI_NOT_VERIFIED`. Never say "self-driving PASS" on a workflow SUCCESS containing skipped agent step.
3. Compare report output to the prior reporting cycle and only alert on new actionable blockers, a proven successful end-to-end deployment, or regression. Scheduled monitoring != unattended code editing.

### Phase 1: safe PR-generating V240 (under 01 owner)
1. Keep current isolated `:workspace` Codex file subset, exactly first **owner-approved** UI task, <=4 allowed UI files and <=300 edited lines, isolated regression tests, Formal guard and missing-data gates.
2. Replace the `HEAD:main` push with an isolated `autodev/ui/<run_id>` branch + **draft PR**, carrying: source head SHA, approved task ID, diffs, test output, affected files, review checklist. Never force-push or silently rebase over race data; fail closed on conflict and let 01 resolve.
3. Separate the privileged publish/PR creation job from the untrusted Codex process and its source tree. New executable content generated by agent must never be evaluated with API secrets. Use narrow `contents/pull-requests` permissions and an explicit allowlist to prevent workflow/data/model writes. Avoid `pull_request_target` for agent code and never execute untrusted artifacts under `workflow_run` secret context.
4. GitHub docs state `GITHUB_TOKEN`-generated PRs trigger CI in approval-needed state; for unattended CI, consider a **least-privilege GitHub App installation token** only after 01 validates app/repository permissions and source trust. For a first safe version, leave the PR open for review rather than bypass checks.
5. Move from "tasks checked" to "tasks with independent proof": each task has owner acceptance, UI semantic regression PASS, Pages SHA PASS, actual Safari manual/device-farm evidence. Human-approved backlog remains a bounded input; do not auto-invent tasks from scraped provider text.

### Phase 2: safe automatic merging, only after repo protection
1. Configure required PR reviews/checks/branch protection for `main` (or repo rulesets after permissions inspected), restrict direct push, disallow forced push/bypass. Need a one-time owner settings action unless an authorized settings connector becomes available.
2. Enable repo `allow_auto_merge` **only if appropriate**. For a narrow class of safe UI-only PRs, set individual auto-merge after independent CI, source-owner review and provenance gates. Changes to prediction weights, Formal lock, provider fetches, shared workflows, permissions and scoring are **never** generic auto-merge.
3. GitHub merge queue is **not generally available to this personal-account repository**; GitHub docs limit it to eligible *organization-owned* repositories and plans. Don't recommend it as immediately selectable or migrate ownership just for queues. Use normal required checks + auto-merge where eligible.
4. CI checks should be always-triggered on relevant PRs; GitHub required status checks may remain Pending forever if all required jobs use `paths` filters that skip a PR. Preserve meaningful unique check names. Branch protection may currently be absent; check settings via authorized owner.

### Phase 3: source freshness and deployment proof
1. Separate high-frequency current-day source writes from lower-frequency **code deployment** without making browser-visible data stale. Use existing owner ledger and V285/V277 lineage checks; assess whether GitHub Pages rebuild is necessary for each data-only commit. Deploy one tested code SHA and explicitly state data SHA/as-of.
2. Current official GitHub docs warn `schedule` may be delayed or jobs dropped under load: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule . For a predeadline race freeze, don't treat cron as exact; rely on already-verified event-driven supplementary triggers and measure first-seen/deadline evidence. Never reconstruct missed frozen predictions afterward.
3. GitHub `concurrency` defaults can replace an older pending run (even if `cancel-in-progress:false`); `queue:max` is supported for workflows requiring multiple pending items, **but** can queue work beyond the race deadline. Only evaluate experimentally on non-critical pipeline after validating timeouts & freshness; use workload-specific groups. https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#concurrency
4. Don't count UI published until deployed SHA and observed content SHA match expected; distinguish Actions SUCCESS from Pages SUCCESS and Safari acceptance. Browser smoke test can use Playwright WebKit, but this is not real iPhone Safari.
5. Stop no-longer-needed scheduled UI writers only when path consumers/actual code/staleness evidence show safe migration. No wholesale disabling or new general-purpose worker.

## Proposed release acceptance matrix

| Stage | Required independent evidence | Forbidden false shortcut |
| --- | --- | --- |
| Queue | First unchecked owner-approved task + current main SHA | Auto-generate unrestricted backlog |
| AI execution | Codex step actually executed, output diff in isolated workspace | Workflow SUCCESS with skipped agent |
| Review | UI-only diff allowlist, independent synthetic regression, fresh Formal guard, original SHA | Let agent write main or edit workflow/model |
| Merge | Protected main, unique required CI checks, exact PR head SHA and 01 approval | Auto-merge arbitrary model/Fresh PR |
| Deploy | CI/merge SHA, Pages deployed SHA, runtime assets SHA | Commit push or green Pages on older SHA |
| Device | Safari real-device or authorized farm evidence | Linux WebKit == iPhone Safari |
| Research | Licensed pre-result data, paired future days and probability calibration | Third-party unlicensed data/odds boosts |
| Formal | Independent freeze and unlock gates with byte-identical Run1/Run2 | Site evidence substitutes formal Fresh |

## Source URLs (consulted, 2026-10-14)
- Official OpenAI Codex Action and API key, sandbox: https://github.com/openai/codex-action
- GitHub token event suppression / Pages trigger: https://docs.github.com/en/actions/concepts/security/github_token
- GitHub auto-merge availability and setup: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-auto-merge-for-pull-requests-in-your-repository
- Protected branches, unique checks and merge requirements: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches
- Merge queue organization ownership constraints: https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/merging-a-pull-request-with-a-merge-queue
- GitHub App permissions: https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/best-practices-for-creating-a-github-app
- GitHub scheduled run reliability: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- GitHub concurrency: https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#concurrency
- GitHub privileged PR contexts risks: https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target

## Scope and owner handoff
No Actions, source collection, Pages, repository settings, AI agent code, data, forecasts, wagers, Fresh flags or payouts were changed. 01 should review and execute safe PR-based autonomy after #204 compliance / release gates; 02 researches legally sourced accuracy improvements separately; 03 continues existing PR #206 and Safari testing. Reinspect main / PRs / metadata immediately before implementing because parallel chats keep changing the repository.
