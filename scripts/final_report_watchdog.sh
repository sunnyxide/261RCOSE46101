#!/usr/bin/env bash
# final_report_watchdog.sh — Mac-side loop that polls AWS-B every 10 min
# until the extended-runs tmux session ends (i.e., all queued work done),
# then runs scripts/aggregate_results.py and produces the final report.
#
# Run: nohup bash scripts/final_report_watchdog.sh > logs/final_report_watchdog.log 2>&1 &
set -uo pipefail
LAB="$(cd "$(dirname "$0")/.." && pwd)"
KEY=~/.ssh/ku-lbj-key.pem
AWS_A=54.227.133.80
AWS_B=54.224.67.51
LOG="$LAB/logs/final_report_watchdog.log"
DURATION=$((14 * 3600))  # 14h max so we don't run forever
INTERVAL=600             # 10 min
START=$(date -u +%s)

_log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }
_log "final_report_watchdog START"

while true; do
  NOW=$(date -u +%s)
  ELAPSED=$((NOW - START))
  if [[ $ELAPSED -gt $DURATION ]]; then
    _log "14h elapsed — generating report anyway"; break
  fi

  # Both instances must finish (instance-a-12h on AWS_B, instance-b-12h on AWS_A)
  A_BUSY="false"; B_BUSY="false"
  if ssh -i "$KEY" -o ConnectTimeout=15 -o BatchMode=yes ubuntu@"$AWS_A" \
       'tmux has-session -t instance-b-12h 2>/dev/null' 2>/dev/null; then
    A_BUSY="true"
  fi
  if ssh -i "$KEY" -o ConnectTimeout=15 -o BatchMode=yes ubuntu@"$AWS_B" \
       'tmux has-session -t instance-a-12h 2>/dev/null' 2>/dev/null; then
    B_BUSY="true"
  fi

  if [[ "$A_BUSY" == "false" && "$B_BUSY" == "false" ]]; then
    _log "BOTH instances done at t+$((ELAPSED/60))min — finalizing"; break
  fi

  _log "still working (t+$((ELAPSED/60))min) A_BUSY=$A_BUSY B_BUSY=$B_BUSY — sleeping ${INTERVAL}s"
  sleep $INTERVAL
done

# Pull results from both instances (best effort)
_log "syncing results from AWS-B"
mkdir -p "$LAB/results/benchmarks" "$LAB/results/baselines"
rsync -avz -e "ssh -i $KEY -o BatchMode=yes" \
  ubuntu@"$AWS_B":~/orbt-research-lab/results/benchmarks/ \
  "$LAB/results/benchmarks/" 2>&1 | tail -5 | tee -a "$LOG"
rsync -avz -e "ssh -i $KEY -o BatchMode=yes" \
  ubuntu@"$AWS_B":~/orbt-research-lab/results/baselines/ \
  "$LAB/results/baselines/" 2>&1 | tail -5 | tee -a "$LOG"

# Try AWS-A (may be unreachable)
if ssh -i "$KEY" -o ConnectTimeout=15 -o BatchMode=yes ubuntu@"$AWS_A" 'echo OK' 2>/dev/null | grep -q OK; then
  _log "syncing results from AWS-A"
  rsync -avz -e "ssh -i $KEY -o BatchMode=yes" \
    ubuntu@"$AWS_A":~/orbt-research-lab/results/benchmarks/ \
    "$LAB/results/benchmarks/" 2>&1 | tail -5 | tee -a "$LOG"
else
  _log "AWS-A unreachable — skipping its result sync"
fi

# Generate final aggregation
_log "running aggregate_results.py"
cd "$LAB" && python3 scripts/aggregate_results.py 2>&1 | tee -a "$LOG"

# Commit results
cd "$LAB"
git add results/benchmarks/ results/baselines/ reports/ 2>&1 | tail -3 | tee -a "$LOG"
git commit -m "results: overnight 12h cultural-QLoRA run aggregated outputs" 2>&1 | tail -3 | tee -a "$LOG"
git push origin HEAD 2>&1 | tail -3 | tee -a "$LOG"

# Touch sentinel for human to find
date -u +%Y-%m-%dT%H:%M:%SZ > "$LAB/results/OVERNIGHT_COMPLETE"

_log "FINAL REPORT GENERATED at reports/final_results_table.md"
