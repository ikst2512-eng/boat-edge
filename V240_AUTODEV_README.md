# BOAT EDGE V240 — Unattended UI development

This pipeline is **not** the existing V235/V236/V237/V239 scheduled race data collector.
It is a separate bounded code-development loop using the official OpenAI Codex GitHub Action.

## What runs without an API credential
- Daily/single-dispatch guarded preflight and unit tests.
- The existing production scheduling, Pages updates and prospective scoring are unchanged.

## What requires a one-time credential
The repo owner must set GitHub Actions repository secret `OPENAI_API_KEY`.
This is an **API billing** credential, separate from a ChatGPT subscription.
Never paste the key into chat, code or an issue.
When the key is missing, V240 explicitly skips AI editing and records that fact in the workflow summary; it does not pretend development happened.

## Boundaries
- The AI agent sees an isolated Git working tree containing only tracked site HTML, CSS, JavaScript and `BOAT_EDGE_AUTODEV_TASKS.md`; no production data, results or formal Fresh resources.
- One unchecked backlog task per run; task queue modified only by ticking the first task.
- Publication allows at most four existing UI files plus the task checkbox, at most 300 changed lines, and no scripts, models, workflows, formal data or result files.
- The source copy is validated outside the agent context, including the V240 regression tests, JS syntax and Git diff checks.
- Only after all gates PASS, the workflow attempts to push the UI-only change to main. Existing GitHub Pages publishing performs deployment. A failed gate never modifies main.
- Does not automatically change prediction weights or certify improved hit rate. Untouched formal Fresh remains locked.
- V240 is not active as AI development until a run demonstrates a successful Codex invocation, validated commit and Pages publication.
