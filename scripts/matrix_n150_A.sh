#!/usr/bin/env bash
# Full cross-cultural matrix at n=150, Instance A rows:
# Vanilla-3B, Vanilla-7B, Run-F (Cultural-KR-3B), Run-H (Cultural-US-3B), Run-J (Cultural-KR-7B)
# Each adapter evaluated on all 4 cultures (kr/jp/us/cn). Deterministic (do_sample=False).
set -uo pipefail
cd ~/orbt-research-lab
source .venv/bin/activate
OUT=results/benchmarks/matrix_n150
mkdir -p "$OUT"
echo "[matrix-A] start $(date -u +%H:%M:%SZ)"

B3="Qwen/Qwen2.5-3B-Instruct"
B7="unsloth/Qwen2.5-7B-Instruct-bnb-4bit"
ADAPTER_F=$(ls -d runs/run-f-kr-qwen*/adapter_final 2>/dev/null | head -1)
ADAPTER_H=$(ls -d runs/run-h-us-*/adapter_final 2>/dev/null | head -1)
ADAPTER_J=$(ls -d runs/run-j-kr-7b-*/adapter_final 2>/dev/null | head -1)

run_row() {  # label base adapter
  local label=$1 base=$2 adapter=$3
  for c in kr jp us cn; do
    local out="$OUT/cross_cultural_${label}_${c}_FULL.json"
    echo "  >> $label on $c"
    local a=()
    [[ -n "$adapter" ]] && a=(--adapter "$adapter")
    python scripts/cross_cultural_eval.py --base "$base" "${a[@]}" \
      --culture "$c" --n-globalopinion 150 --n-blend 80 --n-samples-globalopinion 6 \
      --out "$out" 2>&1 | tail -2
  done
}

run_row "vanilla-3b"   "$B3" ""
run_row "vanilla-7b"   "$B7" ""
[[ -n "$ADAPTER_F" ]] && run_row "run-f-kr"     "$B3" "$ADAPTER_F"
[[ -n "$ADAPTER_H" ]] && run_row "run-h-us"     "$B3" "$ADAPTER_H"
[[ -n "$ADAPTER_J" ]] && run_row "run-j-kr-7b"  "$B7" "$ADAPTER_J"

echo "[matrix-A] end $(date -u +%H:%M:%SZ)"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/INSTANCE_A_MATRIX_COMPLETE"
