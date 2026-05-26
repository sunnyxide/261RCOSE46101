#!/usr/bin/env bash
# post_multieval_pipeline.sh — runs after multi-eval (5-way) completes.
# Adds EXAONE-3.5-2.4B (Korean-pretrained) baseline + QLoRA training + 6-way eval.
#
# This is the controlled-study extension answering:
#   Q2: Does Korean pretraining mitigate KoAlpaca-induced catastrophic forgetting?
#
# Sequence:
#   1. Free disk (delete Qwen2.5-7B base cache, ~5GB)
#   2. Download + score Vanilla EXAONE-3.5-2.4B
#   3. Train Run-E (EXAONE-2.4B + KoAlpaca QLoRA, 1ep, rank 16 — mirror Run-A)
#   4. Score Run-E adapter on KoBBQ + KMMLU
#   5. Generate Run-E after-corpus (60 prompts)
#   6. Final 6-way comparison (vanilla 3B/7B/EXAONE × {none, KoAlpaca QLoRA})

set -uo pipefail

LAB=~/orbt-research-lab
LOG=/tmp/post_multieval.log

_log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

cd $LAB
source .venv/bin/activate

# ============================================================================
# Phase 1: Free disk
# ============================================================================
_log "===== Phase 1: free Qwen-7B base cache ====="
DISK_BEFORE=$(df -h ~ | tail -1 | awk '{print $4}')
rm -rf ~/.cache/huggingface/hub/models--unsloth--Qwen2.5-7B-Instruct-bnb-4bit 2>/dev/null
rm -rf ~/.cache/huggingface/hub/models--Qwen--Qwen2.5-7B-Instruct 2>/dev/null
DISK_AFTER=$(df -h ~ | tail -1 | awk '{print $4}')
_log "disk free: $DISK_BEFORE → $DISK_AFTER"

# ============================================================================
# Phase 2: Vanilla EXAONE-3.5-2.4B baseline
# ============================================================================
_log "===== Phase 2: Vanilla EXAONE-3.5-2.4B KoBBQ + KMMLU ====="
cat > /tmp/eval_exaone_vanilla.json <<'JSON'
{
  "models": [
    {"label": "Vanilla-EXAONE-2.4B", "base": "LGAI-EXAONE/EXAONE-3.5-2.4B-Instruct"}
  ]
}
JSON
python scripts/multi_base_bench.py --config /tmp/eval_exaone_vanilla.json \
  --out $LAB/results/benchmarks/eval_exaone_vanilla.json 2>&1 | tee -a "$LOG"

# ============================================================================
# Phase 3: Train Run-E (EXAONE + KoAlpaca QLoRA, mirror Run-A)
# ============================================================================
_log "===== Phase 3: Run-E EXAONE-2.4B + KoAlpaca QLoRA ====="
RUN_E_ID="run-e-exaone-2.4b-rank16-attn-$(date -u +%Y%m%dT%H%M%SZ)"
python scripts/qlora_train.py \
  --base-model LGAI-EXAONE/EXAONE-3.5-2.4B-Instruct \
  --run-id "$RUN_E_ID" \
  --max-samples 8000 \
  --num-epochs 1 \
  --lora-rank 16 \
  --save-steps 100 --eval-steps 200 \
  2>&1 | tee /tmp/run-e.log
RUN_E_EXIT=$?
_log "Run-E exit: $RUN_E_EXIT"

# ============================================================================
# Phase 4: Final 6-way eval (all bases × {none, KoAlpaca})
# ============================================================================
if [[ $RUN_E_EXIT -eq 0 ]]; then
  _log "===== Phase 4: 6-way controlled comparison ====="
  cat > $LAB/config/eval_6way.json <<JSON
{
  "models": [
    {"label": "Vanilla-3B-Qwen", "base": "Qwen/Qwen2.5-3B-Instruct"},
    {"label": "Run-A-3B-Qwen+KoAlpaca", "base": "Qwen/Qwen2.5-3B-Instruct", "adapter": "~/orbt-research-lab/runs/run-a-rank16-attn-*/adapter_final"},
    {"label": "Run-B-3B-Qwen+KoAlpaca-bigger", "base": "Qwen/Qwen2.5-3B-Instruct", "adapter": "~/orbt-research-lab/runs/run-b-rank32-alllinear-*/adapter_final"},
    {"label": "Vanilla-7B-Qwen", "base": "unsloth/Qwen2.5-7B-Instruct-bnb-4bit"},
    {"label": "Run-D-7B-Qwen+KoAlpaca", "base": "unsloth/Qwen2.5-7B-Instruct-bnb-4bit", "adapter": "~/orbt-research-lab/runs/run-d-7b-rank16-attn-*/adapter_final"},
    {"label": "Vanilla-EXAONE-2.4B", "base": "LGAI-EXAONE/EXAONE-3.5-2.4B-Instruct"},
    {"label": "Run-E-EXAONE-2.4B+KoAlpaca", "base": "LGAI-EXAONE/EXAONE-3.5-2.4B-Instruct", "adapter": "~/orbt-research-lab/runs/run-e-exaone-*/adapter_final"}
  ]
}
JSON
  python scripts/multi_base_bench.py --config $LAB/config/eval_6way.json \
    --out $LAB/results/benchmarks/eval_6way.json 2>&1 | tee -a "$LOG"
fi

# ============================================================================
# Phase 5: After-E corpus (60 prompts)
# ============================================================================
if [[ $RUN_E_EXIT -eq 0 ]]; then
  _log "===== Phase 5: after-E corpus ====="
  RUN_E_ADAPTER=$(ls -d $LAB/runs/run-e-exaone-*/adapter_final 2>/dev/null | head -1)
  python scripts/after_corpus.py --adapter="$RUN_E_ADAPTER" 2>&1 | tee /tmp/after-e.log
  mv -f $LAB/results/baselines/qwen2.5-3b-qlora-corpus.json \
        $LAB/results/baselines/exaone-2.4b-qlora-run-e-corpus.json 2>/dev/null
  mv -f $LAB/results/baselines/before_after_diff.md \
        $LAB/results/baselines/before_after_diff_run-e.md 2>/dev/null
fi

_log "===== POST_MULTIEVAL_COMPLETE ====="
