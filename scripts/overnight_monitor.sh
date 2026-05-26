#!/usr/bin/env bash
# overnight_monitor.sh — Mac-side background loop that records the state of
# both AWS instances every 5 minutes for the next 12 hours. Output goes to
# logs/overnight_monitor.log and stops itself after 12h or when both
# instances have ORCHESTRATOR_STATUS=complete.
#
# Run: nohup bash scripts/overnight_monitor.sh > logs/overnight_monitor.log 2>&1 &
#
# This is a *passive* monitor — does NOT take any corrective action,
# only records state for the final report.

set -uo pipefail
LAB="$(cd "$(dirname "$0")/.." && pwd)"
KEY=~/.ssh/ku-lbj-key.pem
AWS_A=3.91.69.217
AWS_B=3.84.130.149
LOG="$LAB/logs/overnight_monitor.log"
STATUS_JSONL="$LAB/logs/overnight_status.jsonl"
DURATION=$((12 * 3600))   # 12 hours
INTERVAL=300              # 5 minutes
START=$(date -u +%s)

mkdir -p "$LAB/logs"

_log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

probe() {
  local label=$1 host=$2
  ssh -i "$KEY" -o ConnectTimeout=15 -o StrictHostKeyChecking=no -o BatchMode=yes ubuntu@"$host" \
    "tmux ls 2>/dev/null | head -10; echo ---DISK---; df -h ~ | tail -1; \
     echo ---GPU---; nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader 2>&1 | head -1; \
     echo ---STATUS---; cat ~/orbt-research-lab/results/PIPELINE_STATUS_*.json 2>/dev/null | tr -d '\n'" \
    2>&1 | head -25
  return ${PIPESTATUS[0]}
}

_log "overnight_monitor START — duration=12h interval=5min"

while true; do
  NOW=$(date -u +%s)
  ELAPSED=$((NOW - START))
  if [[ $ELAPSED -gt $DURATION ]]; then
    _log "12h elapsed — stopping monitor"
    break
  fi

  AWS_A_OUT=$(probe "AWS-A" "$AWS_A" 2>&1 | head -25 || echo "UNREACHABLE")
  AWS_B_OUT=$(probe "AWS-B" "$AWS_B" 2>&1 | head -25 || echo "UNREACHABLE")

  _log "tick t+$((ELAPSED/60))min"
  printf "%s\n--- AWS-A ---\n%s\n--- AWS-B ---\n%s\n\n" "$(date -u +%H:%M:%SZ)" "$AWS_A_OUT" "$AWS_B_OUT" >> "$LOG"

  # jsonl row for end-of-night analysis
  python3 -c "
import json, sys
print(json.dumps({
    't': '$(date -u +%Y-%m-%dT%H:%M:%SZ)',
    'elapsed_min': $((ELAPSED/60)),
    'aws_a': '''$(echo "$AWS_A_OUT" | head -200 | tr "'" '_')'''[:2000],
    'aws_b': '''$(echo "$AWS_B_OUT" | head -200 | tr "'" '_')'''[:2000],
}))
" >> "$STATUS_JSONL" 2>/dev/null || true

  sleep $INTERVAL
done

_log "overnight_monitor END"
