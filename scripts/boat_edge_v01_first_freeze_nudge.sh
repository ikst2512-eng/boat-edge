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
# Match V220\x27s 100-run lookback: 12 events can all be skipped/cancelled\n# during a completion storm and hide a recent real V229 attempt.\nif ! runs=$(gh api "repos/${GITHUB_REPOSITORY}/actions/workflows/${wf}/runs?per_page=100" 2>/dev/null); then
  echo V01_FIRST_FREEZE_NUDGE_STATUS_UNKNOWN_NO_DISPATCH
  exit 0
fi
if ! printf '%s\n' "$runs" | jq -e '(.workflow_runs | type) == "array"' >/dev/null 2>&1; then
  echo V01_FIRST_FREEZE_NUDGE_STATUS_MALFORMED_NO_DISPATCH
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
# Gate 1C: keep the full existing 120s cooldown for real attempts.
# GitHub may emit a skipped or cancelled completion with ZERO executed jobs;
# these do not prove a source/freeze attempt and must not suppress a fresh,
# still-eligible 2-10m first-Git save. V220 uses the same exclusion.
# Active runs are rejected above even if their conclusion is unavailable.
# When a real V229 ran before final official odds were Git-published, wait
# in THIS producer job only if <=90s remain, then re-read latest main,
# source window, and active jobs. No additional workflow/cron/writer.
if ! cooldown_left=$(printf '%s\n' "$runs" | jq -er --argjson now "$now" '
  [.workflow_runs[]? |
    select(.created_at != null and
           .conclusion != "skipped" and .conclusion != "cancelled") |
    (.created_at | fromdateiso8601) |
    select(. <= $now and ($now - .) < 120)] |
  if length == 0 then 0 else (max + 120 - $now) end
' 2>/dev/null); then
  echo V01_FIRST_FREEZE_NUDGE_COOLDOWN_UNVERIFIABLE_NO_DISPATCH
  exit 0
fi
if (( cooldown_left > 0 )); then
  if (( cooldown_left <= 90 )) && [[ "${V01_COOLDOWN_WAITED:-0}" != 1 ]]; then
    echo "V01_FIRST_FREEZE_NUDGE_BOUNDED_WAIT seconds=$((cooldown_left+2))"
    if ! sleep "$((cooldown_left+2))"; then
      echo V01_FIRST_FREEZE_NUDGE_WAIT_INTERRUPTED_NO_DISPATCH
      exit 0
    fi
    export V01_COOLDOWN_WAITED=1
    exec bash "$0"
  fi
  echo V01_FIRST_FREEZE_NUDGE_V229_COOLDOWN
  exit 0
fi
if gh workflow run "$wf" --ref main; then
  echo V01_FIRST_FREEZE_NUDGE_EXISTING_V229_DISPATCHED
else
  echo V01_FIRST_FREEZE_NUDGE_DISPATCH_FAILED_NO_SUCCESS_CLAIM
fi
