#!/usr/bin/env bash
# phase3_hofstede_ablation.sh — Hofstede 6D dimension ablation on KR culture.
# Trains 3 variants on KR cultural data with different system-prompt conditioning:
#   1. IDV-only (collectivism dim, Korea 18)
#   2. UAI-only (uncertainty avoidance, Korea 85)
#   3. all-6D (current default — for comparison)
#
# Hypothesis: a single dominant dimension is responsible for the WVS shift
# observed in Run-F. If IDV-only matches Run-F's KS, IDV drives it; if UAI-only,
# UAI drives it; if neither, the 6D combination is essential.
#
# Time budget: 3 trainings × ~1h (rank 16, 1 epoch, 5K examples) + 3 evals × 30min
# Total: ~4.5h on AWS-A's L4 GPU.
#
# Run: bash scripts/phase3_hofstede_ablation.sh

set -uo pipefail
LAB="$HOME/orbt-research-lab"
LOG=/tmp/phase3_hofstede.log
cd "$LAB"
source .venv/bin/activate

_log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ) phase3] $*" | tee -a "$LOG"; }
_log "Hofstede dimension ablation START (KR)"

# Generate ablation training data on the fly
mkdir -p data/cultural/kr_idv_only data/cultural/kr_uai_only data/cultural/kr_all6d

if [[ ! -f data/cultural/kr_idv_only/train.jsonl ]]; then
  python - <<'PYEOF'
import json
from pathlib import Path
src = Path("data/cultural/kr/train.jsonl")
if not src.exists():
    print("[abort] kr train.jsonl missing")
    raise SystemExit(2)
rows = [json.loads(l) for l in src.read_text().splitlines() if l.strip()]

variants = {
    "kr_idv_only": "You are an AI persona reflecting Korea cultural context. Hofstede IDV=18 (collectivist). Respond authentically in ko.",
    "kr_uai_only": "You are an AI persona reflecting Korea cultural context. Hofstede UAI=85 (high uncertainty avoidance). Respond authentically in ko.",
    "kr_all6d":    "You are an AI persona reflecting Korea cultural context. Hofstede 6D: PDI=60, IDV=18, MAS=39, UAI=85, LTO=100, IVR=29. Respond authentically in ko.",
}
for name, sys_prompt in variants.items():
    out = Path(f"data/cultural/{name}/train.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in rows:
            r2 = dict(r)
            r2["system"] = sys_prompt
            f.write(json.dumps(r2, ensure_ascii=False) + "\n")
    print(f"[built] {out} — {len(rows)} rows")
PYEOF
fi

# Train each variant
for variant in kr_idv_only kr_uai_only kr_all6d; do
  RUN_ID="run-abl-${variant}-$(date -u +%Y%m%dT%H%M%SZ)"
  _log "training ablation: $variant -> $RUN_ID"
  # Use the cultural_qlora_train but point at the ablation dataset folder via culture flag manipulation
  # cultural_qlora_train.py reads data/cultural/{culture}/train.jsonl — so we re-use kr_idv_only etc as the "culture"
  python scripts/cultural_qlora_train.py \
    --culture "$variant" \
    --base-model "Qwen/Qwen2.5-3B-Instruct" \
    --run-id "$RUN_ID" \
    --num-epochs 1 \
    --lora-rank 16 \
    --lora-target attn \
    --max-length 1024 \
    2>&1 | tee -a "$LOG"
  TRAIN_EXIT=${PIPESTATUS[0]}
  if [[ $TRAIN_EXIT -ne 0 ]]; then
    _log "FAIL: variant $variant exit=$TRAIN_EXIT, continuing to next"
    continue
  fi
  ADAPTER="$LAB/runs/$RUN_ID/adapter_final"
  _log "evaluating $variant on KR cross-cultural"
  python scripts/cross_cultural_eval.py \
    --base "Qwen/Qwen2.5-3B-Instruct" --adapter "$ADAPTER" \
    --culture kr --n-globalopinion 200 --n-blend 100 --n-samples-globalopinion 6 \
    --out "$LAB/results/benchmarks/ablation_${variant}_cross_cultural.json" \
    2>&1 | tee -a "$LOG"
  # Clean intermediate ckpts to keep disk margin
  find "$LAB/runs/$RUN_ID/checkpoint-"* -type d -exec rm -rf {} + 2>/dev/null
done

_log "Hofstede dimension ablation COMPLETE"
