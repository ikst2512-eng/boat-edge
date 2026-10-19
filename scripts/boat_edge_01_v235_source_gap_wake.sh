#!/usr/bin/env bash
# Source producer -> existing V235 direct wake, only for an actual 2-10m
# incomplete PRE_RESULT race. This workflow never subscribes to V235 or
# V229 completion, so it cannot create an Actions completion feedback loop.
set -euo pipefail

case "${GITHUB_WORKFLOW:-}" in
  'BOAT EDGE 自動更新'|'BOAT EDGE 3連単オッズ更新 V71') ;;
  *) echo GATE1C_V235_NUDGE_NOT_TRUSTED_SOURCE_PRODUCER; exit 0 ;;
esac
if [[ "${GITHUB_REPOSITORY:-}" != "ikst2512-eng/boat-edge" ||
      "${GITHUB_REF:-}" != "refs/heads/main" ]]; then
  echo GATE1C_V235_NUDGE_NOT_TRUSTED_MAIN
  exit 0
fi
if [[ -z "${GH_TOKEN:-}" ]] || ! command -v gh >/dev/null ||
   ! command -v jq >/dev/null; then
  echo GATE1C_V235_NUDGE_CLI_OR_AUTH_UNAVAILABLE
  exit 0
fi

# A producer's checkout can predate a competing official source commit.
# Read ONLY latest main and never create any source files in this nudge.
if ! git fetch --no-tags origin main >/dev/null 2>&1 ||
   ! git reset --hard origin/main >/dev/null 2>&1; then
  echo GATE1C_V235_NUDGE_MAIN_UNVERIFIED
  exit 0
fi
if ! plan=$(PYTHONDONTWRITEBYTECODE=1 python3 -m scripts.boat_edge_01_v235_source_gap_wake); then
  echo GATE1C_V235_NUDGE_SOURCE_PROBE_FAILED
  exit 0
fi
echo "GATE1C_V235_SOURCE_GAP_DIAGNOSTIC $plan"
if ! printf '%s\n' "$plan" | jq -e '
  .schema == "GATE1C_V235_SOURCE_GAP_WAKE_V1" and
  .scope == "UNFROZEN_PRE_RESULT_2_TO_10M_SOURCE_REFRESH_ONLY" and
  .eligible_denominator_proven == false and
  .wake_needed == true and
  (.race_keys | type) == "array" and
  (.race_keys | length) >= 1 and
  (.race_keys | length) <= 12 and
  all(.race_keys[]; type == "string" and test("^20[0-9]{6}-[0-9]{2}-[0-9]{2}$"))
' >/dev/null 2>&1; then
  echo GATE1C_V235_NUDGE_NO_VERIFIED_SOURCE_GAP_IN_WINDOW
  exit 0
fi

wf=V235.yml
if ! runs=$(gh api "repos/${GITHUB_REPOSITORY}/actions/workflows/${wf}/runs?per_page=100" 2>/dev/null); then
  echo GATE1C_V235_NUDGE_RUN_HISTORY_UNAVAILABLE
  exit 0
fi
if ! printf '%s\n' "$runs" | jq -e '
  (.total_count | type) == "number" and .total_count >= 0 and
  (.workflow_runs | type) == "array" and
  (.workflow_runs | length) <= 100 and
  all(.workflow_runs[]; (.created_at | type) == "string" and
      (.status | type) == "string")
' >/dev/null 2>&1; then
  echo GATE1C_V235_NUDGE_RUN_HISTORY_MALFORMED
  exit 0
fi
if printf '%s\n' "$runs" | jq -e '
  [.workflow_runs[] | select(.status == "queued" or
    .status == "in_progress" or .status == "waiting" or
    .status == "pending" or .status == "requested")] | length > 0
' >/dev/null; then
  echo GATE1C_V235_NUDGE_EXISTING_V235_ACTIVE
  exit 0
fi
# A real V235 attempt throttles the nudge for 180 seconds. Skipped/cancelled
# zero-job completion events must not suppress a valid future source window.
now=$(date -u +%s)
if ! cooldown=$(printf '%s\n' "$runs" | jq -er --argjson now "$now" '
  [.workflow_runs[] |
   select(.conclusion != "skipped" and .conclusion != "cancelled") |
   (.created_at | fromdateiso8601) |
   select(. <= $now and ($now - .) < 180)] |
  length
' 2>/dev/null); then
  echo GATE1C_V235_NUDGE_COOLDOWN_UNVERIFIABLE
  exit 0
fi
if (( cooldown > 0 )); then
  echo GATE1C_V235_NUDGE_REAL_V235_COOLDOWN
  exit 0
fi
# This launches the SAME V235, with its original 2-10m V229 source checks,
# immutable first Git receipt, concurrency guard and no-result lock.
if gh workflow run "$wf" --ref main; then
  echo GATE1C_V235_NUDGE_EXISTING_SOURCE_REFRESH_DISPATCHED
else
  echo GATE1C_V235_NUDGE_DISPATCH_FAILED_NO_SUCCESS_CLAIM
fi
