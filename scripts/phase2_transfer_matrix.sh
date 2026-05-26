#!/usr/bin/env bash
# phase2_transfer_matrix.sh — runs cross-cultural transfer eval matrix for the
# adapters that live on THIS instance. Each adapter is evaluated against the
# 3 OTHER cultures' benchmarks (off-diagonal) so we can see if cultural
# conditioning transfers, breaks neutral, or breaks negatively.
#
# Invocation:
#   ADAPTERS="run-f-kr run-h-us" bash scripts/phase2_transfer_matrix.sh  # AWS-B
#   ADAPTERS="run-g-jp run-i-cn" bash scripts/phase2_transfer_matrix.sh  # AWS-A
#
# Pairs each adapter with the other 3 cultures (skips in-distribution since
# cultural_pipeline.sh already does that as Phase E).

set -uo pipefail
ADAPTERS="${ADAPTERS:-}"
[[ -z "$ADAPTERS" ]] && { echo "ADAPTERS env required"; exit 1; }
LAB="$HOME/orbt-research-lab"
LOG=/tmp/phase2_transfer.log
cd "$LAB"
source .venv/bin/activate

_log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ) phase2] $*" | tee -a "$LOG"; }
_log "START — adapters=$ADAPTERS"

declare -A ADAPTER_CULTURE=( [run-f]=kr [run-g]=jp [run-h]=us [run-i]=cn )
ALL_CULTURES=(kr jp us cn)

for prefix in $ADAPTERS; do
  # Extract the letter ("run-f-kr" -> "run-f")
  base_run="${prefix%-*}"
  origin_culture="${ADAPTER_CULTURE[$base_run]:-unknown}"
  if [[ "$origin_culture" == "unknown" ]]; then
    _log "skip $prefix — not in known adapter map"
    continue
  fi
  adapter_path=$(ls -d "$LAB/runs/${prefix}"-* 2>/dev/null | tail -1)
  if [[ -z "$adapter_path" || ! -d "$adapter_path/adapter_final" ]]; then
    _log "skip $prefix — adapter not found at $LAB/runs/${prefix}-*/adapter_final"
    continue
  fi
  ADAPTER="$adapter_path/adapter_final"
  BASE=$(python -c "import json; print(json.load(open('$ADAPTER/adapter_config.json'))['base_model_name_or_path'])")
  _log "adapter=$prefix origin=$origin_culture base=$BASE path=$ADAPTER"

  for target in "${ALL_CULTURES[@]}"; do
    if [[ "$target" == "$origin_culture" ]]; then
      _log "  skip in-distribution: $prefix x $target (already done in pipeline Phase E)"
      continue
    fi
    out_file="$LAB/results/benchmarks/transfer_${prefix}_on_${target}.json"
    if [[ -f "$out_file" ]]; then
      _log "  skip: $out_file already exists"
      continue
    fi
    _log "  TRANSFER eval: $prefix adapter on $target benchmark"
    python scripts/cross_cultural_eval.py \
      --base "$BASE" --adapter "$ADAPTER" \
      --culture "$target" \
      --n-globalopinion 150 --n-blend 80 --n-samples-globalopinion 6 \
      --out "$out_file" 2>&1 | tee -a "$LOG"
  done
done

_log "TRANSFER MATRIX COMPLETE on this instance"
