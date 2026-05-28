#!/usr/bin/env bash
# final_report_watchdog.sh — Mac-side loop that polls AWS-B every 10 min
# until the extended-runs tmux session ends (i.e., all queued work done),
# then runs scripts/aggregate_results.py and produces the final report.
#
# Run: nohup bash scripts/final_report_watchdog.sh > logs/final_report_watchdog.log 2>&1 &
set -uo pipefail
LAB="$(cd "$(dirname "$0")/.." && pwd)"
KEY=~/.ssh/ku-lbj-key.pem
AWS_A=3.94.192.167
AWS_B=98.94.65.174
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

  # Distinguish 3 states per instance: BUSY, IDLE, UNREACHABLE. Only finalize
  # if BOTH instances are confirmed IDLE (SSH worked AND tmux has-session = no).
  # SSH timeout is NOT proof of completion — could be transient network or
  # instance overloaded. Treat unreachable as "wait, retry later".
  # Bug history: 5/26, 5/27, 5/28 all premature-finalize because SSH-fail
  # was conflated with session-end. Fixed 2026-05-29.
  check_state() {
    local host=$1 session=$2
    local rc
    ssh -i "$KEY" -o ConnectTimeout=15 -o BatchMode=yes ubuntu@"$host" \
        "tmux has-session -t $session" 2>/dev/null
    rc=$?
    if [[ $rc -eq 0 ]]; then echo BUSY
    elif [[ $rc -eq 1 ]]; then echo IDLE     # ssh ok, no session
    else                       echo UNREACHABLE   # ssh failed (255 typically)
    fi
  }
  A_STATE=$(check_state "$AWS_A" instance-b-6h)
  B_STATE=$(check_state "$AWS_B" instance-a-6h)
  # Also check for the standalone cc-eval session (bypasses instance-*-6h naming)
  A_CC=$(check_state "$AWS_A" cc-eval)
  B_CC=$(check_state "$AWS_B" cc-eval)

  if [[ "$A_STATE" == "IDLE" && "$B_STATE" == "IDLE" \
        && "$A_CC" == "IDLE" && "$B_CC" == "IDLE" ]]; then
    _log "BOTH instances confirmed IDLE at t+$((ELAPSED/60))min — finalizing"; break
  fi

  _log "still working (t+$((ELAPSED/60))min) A=$A_STATE B=$B_STATE cc_A=$A_CC cc_B=$B_CC — sleeping ${INTERVAL}s"
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
