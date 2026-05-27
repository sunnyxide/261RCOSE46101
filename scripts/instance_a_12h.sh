#!/usr/bin/env bash
# instance_a_12h.sh — Instance A (54.224.67.51) 12h workload.
# Cross-cultural eval matrix on 3B adapters + Run-J KR-Cultural on unsloth-7B.
set -uo pipefail
LAB="$HOME/orbt-research-lab"
LOG=/tmp/instance_a_12h.log
cd "$LAB"
source .venv/bin/activate
_log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ) A] $*" | tee -a "$LOG"; }
_log "START Instance A 12h workload"

# Reduce per-eval budget so the matrix fits comfortably
GO_N=150; BLEND_N=80; GO_SAMPLES=6

# ============================================================================
# Cross-cultural eval: Vanilla-3B-Qwen × 4 cultures
# ============================================================================
for c in kr jp us cn; do
  OUT="$LAB/results/benchmarks/cross_cultural_vanilla-3b_${c}.json"
  [[ -f "$OUT" ]] && { _log "skip vanilla-3b $c (exists)"; continue; }
  _log "cross_cultural vanilla-3b on $c"
  python scripts/cross_cultural_eval.py \
    --base "Qwen/Qwen2.5-3B-Instruct" \
    --culture "$c" --n-globalopinion $GO_N --n-blend $BLEND_N --n-samples-globalopinion $GO_SAMPLES \
    --out "$OUT" 2>&1 | tee -a "$LOG"
done

# ============================================================================
# Cross-cultural eval: Run-F (KR Cultural-QLoRA on 3B) × 4 cultures
# ============================================================================
ADAPTER_F=$(ls -d "$LAB"/runs/run-f-kr-*/adapter_final 2>/dev/null | head -1)
if [[ -d "$ADAPTER_F" ]]; then
  for c in kr jp us cn; do
    OUT="$LAB/results/benchmarks/cross_cultural_run-f-kr_${c}.json"
    [[ -f "$OUT" ]] && { _log "skip run-f $c (exists)"; continue; }
    _log "cross_cultural Run-F (KR-Cultural) on $c"
    python scripts/cross_cultural_eval.py \
      --base "Qwen/Qwen2.5-3B-Instruct" --adapter "$ADAPTER_F" \
      --culture "$c" --n-globalopinion $GO_N --n-blend $BLEND_N --n-samples-globalopinion $GO_SAMPLES \
      --out "$OUT" 2>&1 | tee -a "$LOG"
  done
fi

# ============================================================================
# Cross-cultural eval: Run-H (US Cultural-QLoRA on 3B) × 4 cultures
# ============================================================================
ADAPTER_H=$(ls -d "$LAB"/runs/run-h-us-*/adapter_final 2>/dev/null | head -1)
if [[ -d "$ADAPTER_H" ]]; then
  for c in kr jp us cn; do
    OUT="$LAB/results/benchmarks/cross_cultural_run-h-us_${c}.json"
    [[ -f "$OUT" ]] && { _log "skip run-h $c (exists)"; continue; }
    _log "cross_cultural Run-H (US-Cultural) on $c"
    python scripts/cross_cultural_eval.py \
      --base "Qwen/Qwen2.5-3B-Instruct" --adapter "$ADAPTER_H" \
      --culture "$c" --n-globalopinion $GO_N --n-blend $BLEND_N --n-samples-globalopinion $GO_SAMPLES \
      --out "$OUT" 2>&1 | tee -a "$LOG"
  done
fi

# ============================================================================
# HAE-RAE/CLIcK eval for Run-F and Run-H (missing from prior pipeline)
# ============================================================================
_log "HAE-RAE/CLIcK eval for Run-F + Run-H via phase1_extended_eval"
mkdir -p config
cat > config/eval_cultural_F_H.json <<JSON
{
  "models": [
    {"label": "Cultural-KR-3B-RunF", "base": "Qwen/Qwen2.5-3B-Instruct", "adapter": "$ADAPTER_F"},
    {"label": "Cultural-US-3B-RunH", "base": "Qwen/Qwen2.5-3B-Instruct", "adapter": "$ADAPTER_H"}
  ]
}
JSON
python scripts/phase1_extended_eval.py \
  --config config/eval_cultural_F_H.json \
  --out "$LAB/results/benchmarks/phase1_cultural_F_H.json" \
  --few-shot 3 --n-kobbq 200 --n-kmmlu 100 --n-haerae 100 --n-click 100 \
  2>&1 | tee -a "$LOG"

# ============================================================================
# Pull pre-quantized Qwen-7B (5.2G) for Run-J + Vanilla-7B eval
# ============================================================================
_log "fetching unsloth Qwen2.5-7B-bnb-4bit cache"
python - <<'PYEOF' 2>&1 | tail -2 | tee -a "$LOG"
from huggingface_hub import snapshot_download
snapshot_download("unsloth/Qwen2.5-7B-Instruct-bnb-4bit",
                  ignore_patterns=["*.bin"])
print("download_done")
PYEOF

# Cross-cultural eval Vanilla-7B-unsloth × 4 cultures
for c in kr jp us cn; do
  OUT="$LAB/results/benchmarks/cross_cultural_vanilla-7b-unsloth_${c}.json"
  [[ -f "$OUT" ]] && { _log "skip vanilla-7b $c (exists)"; continue; }
  _log "cross_cultural vanilla-7b-unsloth on $c"
  python scripts/cross_cultural_eval.py \
    --base "unsloth/Qwen2.5-7B-Instruct-bnb-4bit" \
    --culture "$c" --n-globalopinion $GO_N --n-blend $BLEND_N --n-samples-globalopinion $GO_SAMPLES \
    --out "$OUT" 2>&1 | tee -a "$LOG"
done

# ============================================================================
# Run-J: KR Cultural-QLoRA on unsloth 7B-bnb-4bit (rank 16, 1 ep — smaller for time)
# ============================================================================
RUN_J_ID="run-j-kr-7b-unsloth-rank16-$(date -u +%Y%m%dT%H%M%SZ)"
_log "training Run-J: $RUN_J_ID"
python scripts/cultural_qlora_train.py \
  --culture kr \
  --base-model "unsloth/Qwen2.5-7B-Instruct-bnb-4bit" \
  --run-id "$RUN_J_ID" \
  --num-epochs 1 --lora-rank 16 --lora-target attn \
  2>&1 | tee -a "$LOG"

ADAPTER_J="$LAB/runs/$RUN_J_ID/adapter_final"
if [[ -d "$ADAPTER_J" ]]; then
  # Free intermediate ckpts immediately
  find "$LAB/runs/$RUN_J_ID/checkpoint-"* -type d -exec rm -rf {} + 2>/dev/null
  for c in kr jp us cn; do
    _log "cross_cultural Run-J (KR-Cultural-7B) on $c"
    python scripts/cross_cultural_eval.py \
      --base "unsloth/Qwen2.5-7B-Instruct-bnb-4bit" --adapter "$ADAPTER_J" \
      --culture "$c" --n-globalopinion $GO_N --n-blend $BLEND_N --n-samples-globalopinion $GO_SAMPLES \
      --out "$LAB/results/benchmarks/cross_cultural_run-j-kr-7b_${c}.json" 2>&1 | tee -a "$LOG"
  done
fi

_log "INSTANCE A 12h COMPLETE"
date -u +%Y-%m-%dT%H:%M:%SZ > "$LAB/results/INSTANCE_A_COMPLETE"
