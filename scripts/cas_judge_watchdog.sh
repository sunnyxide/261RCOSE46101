#!/usr/bin/env bash
# cas_judge_watchdog.sh — Mac-side watchdog that polls AWS instances for new
# cas_corpus JSON files, syncs them down, and runs the 3-judge panel
# (GPT-5 + Claude + local oMLX Qwen-Claude-distilled).
#
# Run: nohup bash scripts/cas_judge_watchdog.sh > logs/cas_judge_watchdog.log 2>&1 &
set -uo pipefail
LAB="$(cd "$(dirname "$0")/.." && pwd)"
KEY=~/.ssh/ku-lbj-key.pem
AWS_A=3.94.192.167   # instance_b runs there
AWS_B=98.94.65.174    # instance_a runs there
LOG="$LAB/logs/cas_judge_watchdog.log"
DURATION=$((18 * 3600))  # 18h max
INTERVAL=600             # 10 min
START=$(date -u +%s)

mkdir -p "$LAB/logs" "$LAB/results/cas_corpus" "$LAB/results/cas_scores"

_log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }
_log "cas_judge_watchdog START"

# Map corpus filename -> culture code
extract_culture() {
  local f="$1"
  case "$f" in
    *_kr.json) echo kr;;
    *_jp.json) echo jp;;
    *_us.json) echo us;;
    *_cn.json) echo cn;;
    *) echo kr;;
  esac
}

while true; do
  NOW=$(date -u +%s)
  ELAPSED=$((NOW - START))
  if [[ $ELAPSED -gt $DURATION ]]; then
    _log "18h elapsed — stopping cas_judge_watchdog"; break
  fi

  # Sync any new cas_corpus from both instances
  for host in "$AWS_A" "$AWS_B"; do
    rsync -avz --ignore-existing -e "ssh -i $KEY -o BatchMode=yes -o ConnectTimeout=15" \
      ubuntu@"$host":~/orbt-research-lab/results/cas_corpus/ \
      "$LAB/results/cas_corpus/" >> "$LOG" 2>&1
  done

  # Find any corpus files we haven't scored yet
  for corpus in "$LAB/results/cas_corpus"/*.json; do
    [[ ! -f "$corpus" ]] && continue
    name=$(basename "$corpus" .json)
    out="$LAB/results/cas_scores/${name}_scored.json"
    if [[ -f "$out" ]]; then continue; fi
    culture=$(extract_culture "$corpus")
    _log "scoring $name (culture=$culture)"
    cd "$LAB"
    # NOTE: local oMLX judge SKIPPED by default per 2026-05-27 user guidance.
    # User's oMLX has Qwen3.6-35B-A3B-4bit-DWQ loaded as default; switching to
    # another model triggers OOM-prone swap. Re-enable only after confirming.
    python3 scripts/cas_judge_panel.py \
      --corpus "$corpus" --culture "$culture" --out "$out" \
      --skip-judge local_qwen27b \
      2>&1 | tee -a "$LOG"
  done

  # Stop if BOTH AWS reinforcements done AND we've scored everything we have.
  # Audit fix 2026-05-29: was OR which caused early termination when only one
  # instance had finished, leaving the other's corpus permanently unscored.
  if [[ -f "$LAB/results/REINFORCEMENT_A_COMPLETE" && -f "$LAB/results/REINFORCEMENT_B_COMPLETE" ]]; then
    pending=$(comm -23 \
      <(ls "$LAB/results/cas_corpus"/*.json 2>/dev/null | xargs -I{} basename {} .json | sort) \
      <(ls "$LAB/results/cas_scores"/*_scored.json 2>/dev/null | xargs -I{} basename {} _scored.json | sort) \
      | wc -l)
    if [[ "$pending" -eq 0 ]]; then
      _log "all known corpora scored AND at least one reinforcement complete — exiting"
      break
    fi
  fi

  _log "tick t+$((ELAPSED/60))min — sleeping ${INTERVAL}s"
  sleep $INTERVAL
done

_log "cas_judge_watchdog END — final scores at results/cas_scores/"
date -u +%Y-%m-%dT%H:%M:%SZ > "$LAB/results/CAS_JUDGE_COMPLETE"
