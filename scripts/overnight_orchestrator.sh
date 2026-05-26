#!/usr/bin/env bash
# overnight_orchestrator.sh — chains 4 cultures' pipelines on one instance.
#
# Run on AWS-B (or AWS-A after Phase 1):
#   nohup bash scripts/overnight_orchestrator.sh AWS_TAG=B > /tmp/orchestrator.log 2>&1 &
#
# Each instance handles 2 cultures (after first completes):
#   AWS-B: kr (running) -> us
#   AWS-A: jp (start fresh) -> cn
#
# That assignment is set via CULTURES env. Default order matches the recommended split.

set -uo pipefail
CULTURES="${CULTURES:-kr us}"
LAB="${LAB:-$HOME/orbt-research-lab}"
LOG=/tmp/orchestrator.log

_log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ) orchestrator] $*" | tee -a "$LOG"; }

cd "$LAB" || { _log "ABORT: $LAB missing"; exit 1; }

for culture in $CULTURES; do
  _log "===== STARTING $culture pipeline ====="
  CULTURE="$culture" EPOCHS="${EPOCHS:-2}" LORA_RANK="${LORA_RANK:-32}" \
    bash scripts/cultural_pipeline.sh
  EXIT=$?
  if [[ $EXIT -ne 0 ]]; then
    _log "FAILED $culture (exit $EXIT) — bailing out, manual investigation needed"
    exit $EXIT
  fi
  _log "===== COMPLETED $culture pipeline ====="
  # Free dataset cache between cultures for disk hygiene (model cache kept for reuse)
  rm -rf ~/.cache/huggingface/datasets/* 2>/dev/null
  df -h ~ | tail -1 | tee -a "$LOG"
done

_log "===== ALL CULTURES COMPLETE: $CULTURES ====="
cat > "$LAB/results/ORCHESTRATOR_STATUS.json" <<JSON
{
  "status": "complete",
  "cultures": "$CULTURES",
  "completed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
JSON
