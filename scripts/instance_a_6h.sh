#!/usr/bin/env bash
# instance_a_6h.sh — cross-cultural eval matrix on Instance A (98.94.65.174).
# Models: Vanilla-3B, Vanilla-7B-unsloth, Run-F-KR, Run-H-US, Run-J-KR-7B.
# Each model × 4 cultures (kr/jp/us/cn) = 20 evals.
set -uo pipefail
LAB="$HOME/orbt-research-lab"
LOG=/tmp/instance_a_6h.log
cd "$LAB"
source .venv/bin/activate
_log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ) A6h] $*" | tee -a "$LOG"; }
_log "START Instance A 6h workload"

GO_N=120; BLEND_N=60; GO_SAMPLES=5

ADAPTER_F=$(ls -d "$LAB"/runs/run-f-kr-*/adapter_final 2>/dev/null | head -1)
ADAPTER_H=$(ls -d "$LAB"/runs/run-h-us-*/adapter_final 2>/dev/null | head -1)
ADAPTER_J=$(ls -d "$LAB"/runs/run-j-kr-7b-*/adapter_final 2>/dev/null | head -1)

eval_model() {
  local label=$1 base=$2 adapter=$3 culture=$4
  local out="$LAB/results/benchmarks/cross_cultural_${label}_${culture}.json"
  if [[ -f "$out" && -s "$out" ]]; then _log "skip $label/$culture (exists)"; return 0; fi
  _log "$label on $culture"
  local args=( --base "$base" --culture "$culture"
               --n-globalopinion $GO_N --n-blend $BLEND_N --n-samples-globalopinion $GO_SAMPLES
               --out "$out" )
  [[ -n "$adapter" ]] && args+=( --adapter "$adapter" )
  python scripts/cross_cultural_eval.py "${args[@]}" 2>&1 | tee -a "$LOG" | tail -5
}

# 5 models × 4 cultures = 20 evals
for c in kr jp us cn; do
  eval_model "vanilla-3b" "Qwen/Qwen2.5-3B-Instruct" "" "$c"
done
for c in kr jp us cn; do
  eval_model "vanilla-7b-unsloth" "unsloth/Qwen2.5-7B-Instruct-bnb-4bit" "" "$c"
done
[[ -n "$ADAPTER_F" ]] && for c in kr jp us cn; do
  eval_model "run-f-kr" "Qwen/Qwen2.5-3B-Instruct" "$ADAPTER_F" "$c"
done
[[ -n "$ADAPTER_H" ]] && for c in kr jp us cn; do
  eval_model "run-h-us" "Qwen/Qwen2.5-3B-Instruct" "$ADAPTER_H" "$c"
done
[[ -n "$ADAPTER_J" ]] && for c in kr jp us cn; do
  eval_model "run-j-kr-7b" "unsloth/Qwen2.5-7B-Instruct-bnb-4bit" "$ADAPTER_J" "$c"
done

_log "INSTANCE A 6h COMPLETE"
date -u +%Y-%m-%dT%H:%M:%SZ > "$LAB/results/INSTANCE_A_COMPLETE"
