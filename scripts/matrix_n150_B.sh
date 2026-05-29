#!/usr/bin/env bash
# Full cross-cultural matrix at n=150, Instance B rows:
# KoAlpaca-3B (Run-B), KoAlpaca-7B (Run-D), Cultural-JP (Run-G), Cultural-CN (Run-I),
# Multi-cultural (Run-M, WITH <<culture:xx>> token). Each on all 4 cultures.
set -uo pipefail
cd ~/orbt-research-lab
source .venv/bin/activate
OUT=results/benchmarks/matrix_n150
mkdir -p "$OUT"
echo "[matrix-B] start $(date -u +%H:%M:%SZ)"

B3="Qwen/Qwen2.5-3B-Instruct"
B7="unsloth/Qwen2.5-7B-Instruct-bnb-4bit"
ADAPTER_B=$(ls -d runs/run-b-rank32-alllinear-*/adapter_final 2>/dev/null | head -1)
ADAPTER_D=$(ls -d runs/run-d-7b-*/adapter_final 2>/dev/null | head -1)
ADAPTER_G=$(ls -d runs/run-g-jp-*/adapter_final 2>/dev/null | head -1)
ADAPTER_I=$(ls -d runs/run-i-cn-*/adapter_final 2>/dev/null | head -1)
ADAPTER_M=$(ls -d runs/run-m-multi-*/adapter_final 2>/dev/null | head -1)

run_row() {  # label base adapter [extra flags...]
  local label=$1 base=$2 adapter=$3; shift 3
  for c in kr jp us cn; do
    local out="$OUT/cross_cultural_${label}_${c}_FULL.json"
    echo "  >> $label on $c"
    local a=()
    [[ -n "$adapter" ]] && a=(--adapter "$adapter")
    python scripts/cross_cultural_eval.py --base "$base" "${a[@]}" \
      --culture "$c" --n-globalopinion 150 --n-blend 80 --n-samples-globalopinion 6 \
      "$@" --out "$out" 2>&1 | tail -2
  done
}

[[ -n "$ADAPTER_B" ]] && run_row "koalpaca-3b-runB" "$B3" "$ADAPTER_B"
[[ -n "$ADAPTER_D" ]] && run_row "koalpaca-7b-runD" "$B7" "$ADAPTER_D"
[[ -n "$ADAPTER_G" ]] && run_row "run-g-jp"         "$B3" "$ADAPTER_G"
[[ -n "$ADAPTER_I" ]] && run_row "run-i-cn"         "$B3" "$ADAPTER_I"
# Run-M evaluated WITH the culture token (matches §3.7 method description)
[[ -n "$ADAPTER_M" ]] && run_row "run-m-multi"      "$B3" "$ADAPTER_M" --culture-token

echo "[matrix-B] end $(date -u +%H:%M:%SZ)"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/INSTANCE_B_MATRIX_COMPLETE"
