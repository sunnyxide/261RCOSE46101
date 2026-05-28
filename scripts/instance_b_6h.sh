#!/usr/bin/env bash
# instance_b_6h.sh — cross-cultural eval matrix on Instance B (3.94.192.167).
# Models: Run-G-JP, Run-I-CN, Run-M-multi, Run-B-KoAlpaca, kr_idv_only abl, kr_uai_only abl.
# Disk tight (1.5G free) — eval only, no new training initially.
set -uo pipefail
LAB="$HOME/orbt-research-lab"
LOG=/tmp/instance_b_6h.log
cd "$LAB"
source .venv/bin/activate
_log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ) B6h] $*" | tee -a "$LOG"; }
_log "START Instance B 6h workload — disk-conscious eval-only"

# Cleanup before starting — free what we can safely
rm -rf ~/.cache/huggingface/datasets/* 2>/dev/null
df -h ~ | tail -1 | tee -a "$LOG"

GO_N=120; BLEND_N=60; GO_SAMPLES=5

ADAPTER_G=$(ls -d "$LAB"/runs/run-g-jp-*/adapter_final 2>/dev/null | head -1)
ADAPTER_I=$(ls -d "$LAB"/runs/run-i-cn-*/adapter_final 2>/dev/null | head -1)
ADAPTER_M=$(ls -d "$LAB"/runs/run-m-multi-*/adapter_final 2>/dev/null | head -1)
ADAPTER_B=$(ls -d "$LAB"/runs/run-b-*/adapter_final 2>/dev/null | head -1)
ADAPTER_IDV=$(ls -d "$LAB"/runs/run-abl-kr_idv_only-*/adapter_final 2>/dev/null | head -1)
ADAPTER_UAI=$(ls -d "$LAB"/runs/run-abl-kr_uai_only-*/adapter_final 2>/dev/null | head -1)

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

# Run-G JP × 4
[[ -n "$ADAPTER_G" ]] && for c in kr jp us cn; do
  eval_model "run-g-jp" "Qwen/Qwen2.5-3B-Instruct" "$ADAPTER_G" "$c"
done

# Run-I CN × 4
[[ -n "$ADAPTER_I" ]] && for c in kr jp us cn; do
  eval_model "run-i-cn" "Qwen/Qwen2.5-3B-Instruct" "$ADAPTER_I" "$c"
done

# Run-M multi × 4
[[ -n "$ADAPTER_M" ]] && for c in kr jp us cn; do
  eval_model "run-m-multi" "Qwen/Qwen2.5-3B-Instruct" "$ADAPTER_M" "$c"
done

# Run-B KoAlpaca baseline × 4 (paper Section 4.1 reference)
[[ -n "$ADAPTER_B" ]] && for c in kr jp us cn; do
  eval_model "run-b-koalpaca" "Qwen/Qwen2.5-3B-Instruct" "$ADAPTER_B" "$c"
done

# Hofstede ablations — KR culture only (the ablation point)
[[ -n "$ADAPTER_IDV" ]] && eval_model "abl-kr-idv-only" "Qwen/Qwen2.5-3B-Instruct" "$ADAPTER_IDV" "kr"
[[ -n "$ADAPTER_UAI" ]] && eval_model "abl-kr-uai-only" "Qwen/Qwen2.5-3B-Instruct" "$ADAPTER_UAI" "kr"

# BONUS: if disk allows, train the missing kr_all6d ablation variant + eval
DISK_FREE_KB=$(df ~ | tail -1 | awk '{print $4}')
if [[ $DISK_FREE_KB -gt 2000000 ]]; then  # >2GB free
  _log "BONUS: disk allows — training Run-abl-kr_all6d"
  if [[ -f data/cultural/kr_all6d/train.jsonl ]]; then
    RUN_ID="run-abl-kr_all6d-$(date -u +%Y%m%dT%H%M%SZ)"
    python scripts/cultural_qlora_train.py \
      --culture kr_all6d --base-model "Qwen/Qwen2.5-3B-Instruct" \
      --run-id "$RUN_ID" --num-epochs 1 --lora-rank 16 --lora-target attn \
      2>&1 | tee -a "$LOG"
    find "$LAB/runs/$RUN_ID/checkpoint-"* -type d -exec rm -rf {} + 2>/dev/null
    ABL_ALL=$(ls -d "$LAB"/runs/run-abl-kr_all6d-*/adapter_final 2>/dev/null | head -1)
    [[ -n "$ABL_ALL" ]] && eval_model "abl-kr-all6d" "Qwen/Qwen2.5-3B-Instruct" "$ABL_ALL" "kr"
  fi
else
  _log "skip kr_all6d training — only ${DISK_FREE_KB}KB free"
fi

_log "INSTANCE B 6h COMPLETE"
date -u +%Y-%m-%dT%H:%M:%SZ > "$LAB/results/INSTANCE_B_COMPLETE"
