#!/usr/bin/env bash
# Gate 1B: give the EXISTING immutable V229 freeze a same-run opportunity after
# a successful official PRE_RESULT producer publish. No new writer or model.
# V220 alone decides readiness; V229 independently re-checks every source and deadline.
set -euo pipefail

if [[ "${GITHUB_REPOSITORY:-}" != "ikst2512-eng/boat-edge" ||
      "${GITHUB_REF:-}" != "refs/heads/main" ]]; then
  echo V01_FIRST_FREEZE_NUDGE_UNTRUSTED_REF_NO_DISPATCH
  exit 0
fi
if [[ -z "${GH_TOKEN:-}" ]] || ! command -v gh >/dev/null ||
   ! command -v jq >/dev/null; then
  echo V01_FIRST_FREEZE_NUDGE_AUTH_OR_CLI_UNAVAILABLE_NO_DISPATCH
  exit 0
fi

# Read the commit which is ACTUALLY on main after the source producer's push.
# Never run against a source producer's outdated checkout or locally guessed rows.
if ! git fetch --no-tags origin main >/dev/null 2>&1 ||
   ! git reset --hard origin/main >/dev/null 2>&1; then
  echo V01_FIRST_FREEZE_NUDGE_MAIN_REFRESH_FAILED_NO_DISPATCH
  exit 0
fi

if ! plan=$(PYTHONDONTWRITEBYTECODE=1 python3 scripts/boat_edge_v220_site_ops.py --recovery-plan); then
  echo V01_FIRST_FREEZE_NUDGE_FAIL_CLOSED_READINESS_UNAVAILABLE
  exit 0
fi
wf=BOAT_EDGE_V229_ATOMIC_FREEZE_AUDIT.yml
if ! printf '%s\n' "$plan" | jq -e --arg wf "$wf" '
  (.workflows | type) == "array" and
  (.workflows | index($wf)) != null
' >/dev/null 2>&1; then
  echo V01_FIRST_FREEZE_NUDGE_NOT_SOURCE_READY_OR_OUTSIDE_WINDOW
  exit 0
fi

# Keep exactly the same 120s V229 cooldown and active-job exclusion as V220.
# Failure to inspect state means no dispatch; a "success" cannot be invented.
if ! runs=$(gh api "repos/${GITHUB_REPOSITORY}/actions/workflows/${wf}/runs?per_page=12" 2>/dev/null); then
  echo V01_FIRST_FREEZE_NUDGE_STATUS_UNKNOWN_NO_DISPATCH
  exit 0
fi
if printf '%s\n' "$runs" | jq -e '
  [.workflow_runs[]? | select(
    .status == "queued" or .status == "in_progress" or
    .status == "waiting" or .status == "pending" or
    .status == "requested")] | length > 0
' >/dev/null 2>&1; then
  echo V01_FIRST_FREEZE_NUDGE_V229_ALREADY_ACTIVE
  exit 0
fi
now=$(date -u +%s)
if printf '%s\n' "$runs" | jq -e --argjson now "$now" '
  [.workflow_runs[]? | select(.created_at != null) |
    select((.created_at | fromdateiso8601) <= $now and
           ($now - (.created_at | fromdateiso8601)) < 120)] | length > 0
' >/dev/null 2>&1; then
  echo V01_FIRST_FREEZE_NUDGE_V229_COOLDOWN
  exit 0
fi
if gh workflow run "$wf" --ref main; then
  echo V01_FIRST_FREEZE_NUDGE_EXISTING_V229_DISPATCHED
else
  echo V01_FIRST_FREEZE_NUDGE_DISPATCH_FAILED_NO_SUCCESS_CLAIM
fi
