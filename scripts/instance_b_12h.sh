#!/usr/bin/env bash
# instance_b_12h.sh — Instance B (54.227.133.80) 12h workload.
# Run-G JP retrain + cross-cultural eval JP/CN adapters + Hofstede ablation + multi-cultural unified.
set -uo pipefail
LAB="$HOME/orbt-research-lab"
LOG=/tmp/instance_b_12h.log
cd "$LAB"
source .venv/bin/activate
_log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ) B] $*" | tee -a "$LOG"; }
_log "START Instance B 12h workload"

GO_N=150; BLEND_N=80; GO_SAMPLES=6

# ============================================================================
# Phase 1: Retrain Run-G (JP) — adapter was lost in restart
# ============================================================================
RUN_G_ID="run-g-jp-qwen-qwen2.5-3b-rank16-$(date -u +%Y%m%dT%H%M%SZ)"
if ! ls -d "$LAB"/runs/run-g-jp-*/adapter_final 2>/dev/null | head -1 > /dev/null; then
  _log "Run-G adapter missing — retraining"
  python scripts/cultural_qlora_train.py \
    --culture jp \
    --base-model "Qwen/Qwen2.5-3B-Instruct" \
    --run-id "$RUN_G_ID" \
    --num-epochs 5 --lora-rank 16 --lora-target attn \
    2>&1 | tee -a "$LOG"
  find "$LAB/runs/$RUN_G_ID/checkpoint-"* -type d -exec rm -rf {} + 2>/dev/null
fi
ADAPTER_G=$(ls -d "$LAB"/runs/run-g-jp-*/adapter_final 2>/dev/null | head -1)
ADAPTER_I=$(ls -d "$LAB"/runs/run-i-cn-*/adapter_final 2>/dev/null | head -1)

# ============================================================================
# Phase 2: Cross-cultural eval Run-G (JP) and Run-I (CN) × 4 cultures
# ============================================================================
for adapter_label in "run-g-jp:$ADAPTER_G" "run-i-cn:$ADAPTER_I"; do
  label="${adapter_label%%:*}"
  apath="${adapter_label#*:}"
  if [[ -d "$apath" ]]; then
    for c in kr jp us cn; do
      OUT="$LAB/results/benchmarks/cross_cultural_${label}_${c}.json"
      [[ -f "$OUT" ]] && { _log "skip $label $c (exists)"; continue; }
      _log "cross_cultural $label on $c"
      python scripts/cross_cultural_eval.py \
        --base "Qwen/Qwen2.5-3B-Instruct" --adapter "$apath" \
        --culture "$c" --n-globalopinion $GO_N --n-blend $BLEND_N --n-samples-globalopinion $GO_SAMPLES \
        --out "$OUT" 2>&1 | tee -a "$LOG"
    done
  fi
done

# ============================================================================
# Phase 3: HAE-RAE/CLIcK eval for cultural adapters G and I
# ============================================================================
_log "HAE-RAE/CLIcK eval for Run-G + Run-I"
mkdir -p config
cat > config/eval_cultural_G_I.json <<JSON
{
  "models": [
    {"label": "Cultural-JP-3B-RunG", "base": "Qwen/Qwen2.5-3B-Instruct", "adapter": "$ADAPTER_G"},
    {"label": "Cultural-CN-3B-RunI", "base": "Qwen/Qwen2.5-3B-Instruct", "adapter": "$ADAPTER_I"}
  ]
}
JSON
python scripts/phase1_extended_eval.py \
  --config config/eval_cultural_G_I.json \
  --out "$LAB/results/benchmarks/phase1_cultural_G_I.json" \
  --few-shot 3 --n-kobbq 200 --n-kmmlu 100 --n-haerae 100 --n-click 100 \
  2>&1 | tee -a "$LOG"

# ============================================================================
# Phase 4: Hofstede dimension ablation (kr_idv_only / kr_uai_only / kr_all6d)
# ============================================================================
_log "Hofstede dimension ablation"
# Ensure ablation datasets exist (created in previous session, but re-create defensively)
python - <<'PYEOF' 2>&1 | tee -a "$LOG"
import json
from pathlib import Path
src = Path.home() / "orbt-research-lab/data/cultural/kr/train.jsonl"
if not src.exists():
    print("[abort] no kr train.jsonl"); raise SystemExit(2)
rows = [json.loads(l) for l in src.read_text().splitlines() if l.strip()]
variants = {
    "kr_idv_only": "You are an AI persona reflecting Korea cultural context. Hofstede IDV=18 (collectivist). Respond authentically in ko.",
    "kr_uai_only": "You are an AI persona reflecting Korea cultural context. Hofstede UAI=85 (high uncertainty avoidance). Respond authentically in ko.",
    "kr_all6d":    "You are an AI persona reflecting Korea cultural context. Hofstede 6D: PDI=60, IDV=18, MAS=39, UAI=85, LTO=100, IVR=29. Respond authentically in ko.",
}
for name, sys_prompt in variants.items():
    out = Path.home() / f"orbt-research-lab/data/cultural/{name}/train.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        for r in rows:
            r2 = dict(r); r2["system"] = sys_prompt
            f.write(json.dumps(r2, ensure_ascii=False) + "\n")
    print(f"[built] {out.name} -> {len(rows)} rows")
PYEOF

for variant in kr_idv_only kr_uai_only kr_all6d; do
  RUN_ID="run-abl-${variant}-$(date -u +%Y%m%dT%H%M%SZ)"
  ABL_ADAPTER="$LAB/runs/$RUN_ID/adapter_final"
  if ls -d "$LAB"/runs/run-abl-${variant}-*/adapter_final 2>/dev/null | head -1 > /dev/null; then
    _log "skip $variant — already trained"
    ABL_ADAPTER=$(ls -d "$LAB"/runs/run-abl-${variant}-*/adapter_final | head -1)
  else
    _log "training $RUN_ID"
    python scripts/cultural_qlora_train.py \
      --culture "$variant" --base-model "Qwen/Qwen2.5-3B-Instruct" \
      --run-id "$RUN_ID" --num-epochs 1 --lora-rank 16 --lora-target attn \
      2>&1 | tee -a "$LOG"
    find "$LAB/runs/$RUN_ID/checkpoint-"* -type d -exec rm -rf {} + 2>/dev/null
  fi
  # Cross-cultural eval (KR benchmark only — we're measuring Korean cultural shift)
  if [[ -d "$ABL_ADAPTER" ]]; then
    OUT="$LAB/results/benchmarks/ablation_${variant}_cross_cultural_kr.json"
    if [[ ! -f "$OUT" ]]; then
      _log "eval $variant on KR"
      python scripts/cross_cultural_eval.py \
        --base "Qwen/Qwen2.5-3B-Instruct" --adapter "$ABL_ADAPTER" \
        --culture kr --n-globalopinion $GO_N --n-blend $BLEND_N --n-samples-globalopinion $GO_SAMPLES \
        --out "$OUT" 2>&1 | tee -a "$LOG"
    fi
  fi
done

# ============================================================================
# Phase 5 (BONUS): Multi-cultural unified adapter (KR+JP+US+CN mix + culture token)
# ============================================================================
_log "BONUS: multi-cultural unified dataset + training"
python - <<'PYEOF' 2>&1 | tee -a "$LOG"
import json
from pathlib import Path
src_root = Path.home() / "orbt-research-lab/data/cultural"
out = src_root / "multi" / "train.jsonl"
out.parent.mkdir(parents=True, exist_ok=True)
all_rows = []
for c in ["kr", "jp", "us", "cn"]:
    p = src_root / c / "train.jsonl"
    if not p.exists(): continue
    for line in p.read_text().splitlines():
        if not line.strip(): continue
        r = json.loads(line)
        # Prepend culture token to user instruction
        r["instruction"] = f"<<culture:{c}>> {r['instruction']}"
        all_rows.append(r)
import random; random.seed(42); random.shuffle(all_rows)
with open(out, "w") as f:
    for r in all_rows:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
print(f"[multi] {len(all_rows)} rows -> {out}")
PYEOF

RUN_M_ID="run-m-multi-rank32-$(date -u +%Y%m%dT%H%M%SZ)"
if ! ls -d "$LAB"/runs/run-m-multi-*/adapter_final 2>/dev/null | head -1 > /dev/null; then
  _log "training $RUN_M_ID"
  python scripts/cultural_qlora_train.py \
    --culture multi --base-model "Qwen/Qwen2.5-3B-Instruct" \
    --run-id "$RUN_M_ID" --num-epochs 1 --lora-rank 32 --lora-target all_linear \
    2>&1 | tee -a "$LOG"
  find "$LAB/runs/$RUN_M_ID/checkpoint-"* -type d -exec rm -rf {} + 2>/dev/null
fi
ADAPTER_M=$(ls -d "$LAB"/runs/run-m-multi-*/adapter_final 2>/dev/null | head -1)
if [[ -d "$ADAPTER_M" ]]; then
  for c in kr jp us cn; do
    _log "cross_cultural Run-M (multi-cultural) on $c"
    python scripts/cross_cultural_eval.py \
      --base "Qwen/Qwen2.5-3B-Instruct" --adapter "$ADAPTER_M" \
      --culture "$c" --n-globalopinion $GO_N --n-blend $BLEND_N --n-samples-globalopinion $GO_SAMPLES \
      --out "$LAB/results/benchmarks/cross_cultural_run-m-multi_${c}.json" 2>&1 | tee -a "$LOG"
  done
fi

_log "INSTANCE B 12h COMPLETE"
date -u +%Y-%m-%dT%H:%M:%SZ > "$LAB/results/INSTANCE_B_COMPLETE"
