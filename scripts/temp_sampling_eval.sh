#!/usr/bin/env bash
# Temperature-sampled GO-KS re-eval (paper limitation viii fix). temp=0.7, n=30
# samples so the per-question distribution is real, not a greedy one-hot spike.
# Instance A adapters: vanilla (base), run-f-kr, run-h-us, run-j-kr-7b.
set -uo pipefail
cd ~/orbt-research-lab; source .venv/bin/activate
OUT=results/benchmarks/temp_sampling; mkdir -p "$OUT"
B3="Qwen/Qwen2.5-3B-Instruct"; B7="unsloth/Qwen2.5-7B-Instruct-bnb-4bit"
AF=$(ls -d runs/run-f-kr-qwen*/adapter_final 2>/dev/null | head -1)
AH=$(ls -d runs/run-h-us-*/adapter_final 2>/dev/null | head -1)
AJ=$(ls -d runs/run-j-kr-7b-*/adapter_final 2>/dev/null | head -1)
echo "[temp] start $(date -u +%H:%M:%SZ)  AF=$AF AH=$AH AJ=$AJ"
ev() { # label base adapter culture
  local label=$1 base=$2 adp=$3 c=$4
  local a=(); [[ -n "$adp" ]] && a=(--adapter "$adp")
  echo "  >> $label @ $c (temp=0.7 n=30)"
  python scripts/cross_cultural_eval.py --base "$base" "${a[@]}" --culture "$c" \
    --n-globalopinion 150 --n-blend 1 --n-samples-globalopinion 30 --temperature 0.7 \
    --out "$OUT/cross_cultural_${label}_${c}_TEMP.json" 2>&1 | tail -2
}
# Korean headline: vanilla vs Cultural-KR-3B vs Cultural-KR-7B (the core metric-validity test)
ev vanilla-3b "$B3" "" kr
[[ -n "$AF" ]] && ev run-f-kr "$B3" "$AF" kr
[[ -n "$AJ" ]] && ev run-j-kr-7b "$B7" "$AJ" kr
# US degradation under sampling: vanilla vs Cultural-US on all targets
ev vanilla-3b "$B3" "" us
ev vanilla-3b "$B3" "" jp
ev vanilla-3b "$B3" "" cn
[[ -n "$AH" ]] && for c in kr jp us cn; do ev run-h-us "$B3" "$AH" "$c"; done
echo "[temp] end $(date -u +%H:%M:%SZ)"
date -u +%Y-%m-%dT%H:%M:%SZ > "$OUT/TEMP_SAMPLING_COMPLETE"
