#!/usr/bin/env bash
# aws_a_revival_watchdog.sh — Mac-side loop that re-tries AWS-A every 10 min
# for up to 12 hours. When AWS-A becomes reachable, re-establishes the
# JP -> CN -> eval chain (idempotent — checks PIPELINE_STATUS markers first).
#
# Run: nohup bash scripts/aws_a_revival_watchdog.sh > logs/aws_a_revival.log 2>&1 &
set -uo pipefail
LAB="$(cd "$(dirname "$0")/.." && pwd)"
KEY=~/.ssh/ku-lbj-key.pem
AWS_A=54.227.133.80
LOG="$LAB/logs/aws_a_revival.log"
DURATION=$((12 * 3600))
INTERVAL=600   # 10 min
START=$(date -u +%s)
LAUNCHED=0

_log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }
_log "aws_a_revival_watchdog START"

while true; do
  NOW=$(date -u +%s)
  ELAPSED=$((NOW - START))
  if [[ $ELAPSED -gt $DURATION ]]; then
    _log "12h elapsed — stopping watchdog (launched=$LAUNCHED)"; break
  fi

  if ssh -i "$KEY" -o ConnectTimeout=15 -o BatchMode=yes -o StrictHostKeyChecking=no \
       ubuntu@"$AWS_A" 'echo HEALTHY' 2>/dev/null | grep -q HEALTHY; then
    _log "AWS-A REACHABLE at t+$((ELAPSED/60))min"
    if [[ $LAUNCHED -eq 0 ]]; then
      _log "launching JP -> CN -> eval chain on AWS-A"
      ssh -i "$KEY" -o BatchMode=yes ubuntu@"$AWS_A" 'bash -s' << 'REMOTE' >> "$LOG" 2>&1
set -uo pipefail
cd ~/orbt-research-lab
# Skip if pipeline status already complete for both
JP_DONE=$([[ -f results/PIPELINE_STATUS_jp.json ]] && echo y || echo n)
CN_DONE=$([[ -f results/PIPELINE_STATUS_cn.json ]] && echo y || echo n)
echo "[revival] jp_done=$JP_DONE cn_done=$CN_DONE"
tmux kill-session -t cultural-chain-revived 2>/dev/null
tmux new-session -d -s cultural-chain-revived "
cd ~/orbt-research-lab && source .venv/bin/activate
if [[ ! -f results/PIPELINE_STATUS_jp.json ]]; then
  CULTURE=jp EPOCHS=5 LORA_RANK=16 bash scripts/cultural_pipeline.sh 2>&1 | tee /tmp/cultural_jp.log
fi
rm -rf ~/.cache/huggingface/datasets/* 2>/dev/null
if [[ ! -f results/PIPELINE_STATUS_cn.json ]]; then
  CULTURE=cn EPOCHS=5 LORA_RANK=16 bash scripts/cultural_pipeline.sh 2>&1 | tee /tmp/cultural_cn.log
fi
echo '[revival] all cultural runs complete on AWS-A'
"
tmux ls
REMOTE
      LAUNCHED=1
      _log "JP/CN chain launched (LAUNCHED=1) — watchdog now in passive mode"
    fi
  else
    _log "AWS-A unreachable at t+$((ELAPSED/60))min"
  fi

  sleep $INTERVAL
done

_log "aws_a_revival_watchdog END"
