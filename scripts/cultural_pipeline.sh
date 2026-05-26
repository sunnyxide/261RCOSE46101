#!/usr/bin/env bash
# cultural_pipeline.sh — per-instance cultural QLoRA pipeline.
#
# Run on either AWS-A (CULTURE=kr) or AWS-B (CULTURE=jp), in tmux.
# After phase 1 (KR+JP) completes successfully, re-invoke with CULTURE=us on A
# and CULTURE=cn on B for phase 2 (option C stretch).
#
# Usage:
#   CULTURE=kr bash scripts/cultural_pipeline.sh
#   CULTURE=jp bash scripts/cultural_pipeline.sh

set -uo pipefail

CULTURE="${CULTURE:?CULTURE env var required (kr|jp|us|cn)}"
TARGET="${TARGET:-12000}"
BASE_MODEL="${BASE_MODEL:-Qwen/Qwen2.5-3B-Instruct}"
LORA_RANK="${LORA_RANK:-32}"
EPOCHS="${EPOCHS:-2}"

LAB="${LAB:-$HOME/orbt-research-lab}"
LOG=/tmp/cultural_pipeline_${CULTURE}.log

_log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

cd "$LAB" || { _log "ABORT: $LAB missing"; exit 1; }

if [[ -f .venv/bin/activate ]]; then
  source .venv/bin/activate
else
  _log "ABORT: .venv not found in $LAB"
  exit 1
fi

# ============================================================================
# Phase A: Cultural dataset construction
# ============================================================================
_log "===== A: cultural dataset build (culture=$CULTURE target=$TARGET) ====="
DATA_DIR="$LAB/data/cultural/$CULTURE"
if [[ -f "$DATA_DIR/train.jsonl" ]]; then
  COUNT=$(wc -l < "$DATA_DIR/train.jsonl")
  _log "existing dataset found: $COUNT lines — reusing"
else
  python scripts/build_cultural_dataset.py --culture "$CULTURE" --target "$TARGET" \
    2>&1 | tee -a "$LOG"
  BUILD_EXIT=${PIPESTATUS[0]}
  if [[ $BUILD_EXIT -ne 0 ]]; then
    _log "ABORT: dataset build failed (exit $BUILD_EXIT)"
    exit 2
  fi
fi

# ============================================================================
# Phase B: Cultural QLoRA training
# ============================================================================
RUN_LETTER=$(case "$CULTURE" in
  kr) echo "f" ;;
  jp) echo "g" ;;
  us) echo "h" ;;
  cn) echo "i" ;;
  *)  echo "x" ;;
esac)
TS=$(date -u +%Y%m%dT%H%M%SZ)
BASE_TAG=$(echo "$BASE_MODEL" | tr '/' '-' | tr '[:upper:]' '[:lower:]')
RUN_ID="run-${RUN_LETTER}-${CULTURE}-${BASE_TAG}-rank${LORA_RANK}-${TS}"

_log "===== B: cultural QLoRA training (run_id=$RUN_ID) ====="
python scripts/cultural_qlora_train.py \
  --culture "$CULTURE" \
  --base-model "$BASE_MODEL" \
  --run-id "$RUN_ID" \
  --num-epochs "$EPOCHS" \
  --lora-rank "$LORA_RANK" \
  --lora-target all_linear \
  2>&1 | tee -a "$LOG"
TRAIN_EXIT=${PIPESTATUS[0]}
_log "training exit: $TRAIN_EXIT"
if [[ $TRAIN_EXIT -ne 0 ]]; then
  _log "ABORT: training failed"
  exit 3
fi

ADAPTER="$LAB/runs/$RUN_ID/adapter_final"
if [[ ! -d "$ADAPTER" ]]; then
  _log "ABORT: adapter dir missing at $ADAPTER"
  exit 4
fi

# ============================================================================
# Phase C: Evaluation (KoBBQ/HAE-RAE for kr; JBBQ/JMMLU for jp; etc.)
# ============================================================================
_log "===== C: cultural-specific evaluation ====="
EVAL_CONFIG="/tmp/eval_cultural_${CULTURE}.json"
cat > "$EVAL_CONFIG" <<JSON
{
  "models": [
    {"label": "Cultural-${CULTURE}-3B", "base": "$BASE_MODEL", "adapter": "$ADAPTER"}
  ]
}
JSON

python scripts/multi_base_bench.py --config "$EVAL_CONFIG" \
  --out "$LAB/results/benchmarks/cultural_${CULTURE}_${TS}.json" \
  2>&1 | tee -a "$LOG"

# ============================================================================
# Phase D: After-corpus comparison vs vanilla
# ============================================================================
_log "===== D: after-corpus (60 prompts) for visual side-by-side ====="
python scripts/after_corpus.py --adapter="$ADAPTER" 2>&1 | tee -a "$LOG"
# Rename outputs to culture-specific names
if [[ -f "$LAB/results/baselines/qwen2.5-3b-qlora-corpus.json" ]]; then
  mv -f "$LAB/results/baselines/qwen2.5-3b-qlora-corpus.json" \
        "$LAB/results/baselines/cultural-${CULTURE}-corpus-${TS}.json"
fi
if [[ -f "$LAB/results/baselines/before_after_diff.md" ]]; then
  mv -f "$LAB/results/baselines/before_after_diff.md" \
        "$LAB/results/baselines/before_after_cultural_${CULTURE}_${TS}.md"
fi

# ============================================================================
# Phase E: Mark complete for monitor
# ============================================================================
mkdir -p "$LAB/results"
cat > "$LAB/results/PIPELINE_STATUS_${CULTURE}.json" <<JSON
{
  "culture": "$CULTURE",
  "status": "complete",
  "run_id": "$RUN_ID",
  "adapter": "$ADAPTER",
  "completed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
JSON

_log "===== CULTURAL_PIPELINE_COMPLETE culture=$CULTURE ====="
