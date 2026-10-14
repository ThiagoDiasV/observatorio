#!/usr/bin/env sh
set -eu
ROOT="${OBSERVATORIO_ROOT:-/opt/observatorio}"
LOG_DIR="${OBSERVATORIO_LOG_DIR:-/var/log/observatorio}"
mkdir -p "$LOG_DIR"
cd "$ROOT"
python3 automation/collect.py --output "$ROOT/automation/inbox" --state "$ROOT/automation/state/seen.json" >> "$LOG_DIR/collector.log" 2>&1
REPORT="$ROOT/automation/inbox/$(date -u +%F).json"
python3 automation/validate_review.py "$REPORT" >> "$LOG_DIR/collector.log" 2>&1
