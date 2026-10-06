#!/usr/bin/env bash
# #237 P0/P1: run the regression and prove the live system did not change.
# Usage: scripts/regression_with_canary.sh [pytest args...]
# Read-only observations of the live brain (no connection to it, no launchctl write):
#   brain launchd PID, listeners on 18089, StorageV2 conversation directory count,
#   catalog.sqlite mtime, total event-log line count. Any difference fails the run.
set -u
BRAIN_LABEL="${JULIA_BRAIN_LABEL:-com.julia.brain.18089}"
CONV_DIR="${JULIA_CANARY_CONV_DIR:-$HOME/julia_ai_assistant/memory/conversations}"
EVENT_DIR="${JULIA_CANARY_EVENT_DIR:-$HOME/julia_release/rd1_v1/julia_core/data/events}"

snapshot() {
  local pid holders dirs cat events
  pid=$(launchctl list 2>/dev/null | awk -v l="$BRAIN_LABEL" '$3==l{print $1}')
  holders=$(lsof -nP -iTCP:18089 -sTCP:LISTEN -t 2>/dev/null | sort | tr '\n' ',')
  dirs=$(ls -d "$CONV_DIR"/conv_* 2>/dev/null | wc -l | tr -d ' ')
  cat=$(stat -f %m "$CONV_DIR/catalog.sqlite" 2>/dev/null || echo none)
  events=$(cat "$EVENT_DIR"/events-*.jsonl 2>/dev/null | wc -l | tr -d ' ')
  echo "brain_pid=${pid:-none} listeners=${holders:-none} conv_dirs=$dirs catalog_mtime=$cat event_lines=$events"
}

before=$(snapshot)
echo "canary before: $before"
PYTEST_CMD="${PYTEST:-python3 -m pytest}"
# shellcheck disable=SC2086  (the command may be "python3 -m pytest")
$PYTEST_CMD "$@"
status=$?
after=$(snapshot)
echo "canary after:  $after"
if [ "$before" != "$after" ]; then
  echo "CANARY FAILED: the live system changed during the regression" >&2
  exit 97
fi
echo "canary ok: live system unchanged"
exit $status
