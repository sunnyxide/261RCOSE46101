#!/usr/bin/env bash
# mimo_dispatch_parallel.sh — fires all briefs/mimo/*.md to mimo-v2.5-pro Plan
# endpoint concurrently (capped at MAX_PARALLEL). Outputs to reports/drafts_mimo/.
#
# All outputs are DRAFT (per user guidance 2026-05-28: mimo can hallucinate,
# Claude or gpt-5.5 must double-check before promotion to final paper).
#
# Usage: bash scripts/mimo_dispatch_parallel.sh
#   env: MAX_PARALLEL=5 MAX_TOKENS=16000 MODEL=mimo-v2.5-pro

set -uo pipefail
LAB="$(cd "$(dirname "$0")/.." && pwd)"
MAX_PARALLEL="${MAX_PARALLEL:-5}"
MAX_TOKENS="${MAX_TOKENS:-16000}"
MODEL="${MODEL:-mimo-v2.5-pro}"
LOG="$LAB/logs/mimo_dispatch.log"
OUT_DIR="$LAB/reports/drafts_mimo"
mkdir -p "$OUT_DIR" "$LAB/logs"

# Load key
KEY="${XIAOMI_PLAN_API_KEY:-}"
if [[ ! "$KEY" =~ ^tp- ]] && [[ -f "$HOME/.hermes/.env" ]]; then
  KEY=$(grep -E '^XIAOMI_PLAN_API_KEY=' "$HOME/.hermes/.env" | sed 's/.*=//' | tr -d '"' | tr -d "'" | head -1)
fi
BASE="${XIAOMI_PLAN_BASE_URL:-https://token-plan-sgp.xiaomimimo.com/v1}"

if [[ ! "$KEY" =~ ^tp- ]]; then
  echo "FATAL: XIAOMI_PLAN_API_KEY (tp-) not found"; exit 2
fi

_log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }
_log "mimo_dispatch_parallel START — MAX_PARALLEL=$MAX_PARALLEL MAX_TOKENS=$MAX_TOKENS"

dispatch_one() {
  local brief="$1"
  local name=$(basename "$brief" .md)
  local out="$OUT_DIR/${name}_draft_mimo.md"
  local raw="$OUT_DIR/${name}_draft_mimo.raw.json"
  if [[ -f "$out" && -s "$out" ]]; then
    echo "[skip] $name already exists ($out)"; return 0
  fi
  echo "[start] $name -> $out"
  local t0=$(date +%s)
  local body
  body=$(python3 -c "
import json, sys
brief = open('$brief').read()
print(json.dumps({
  'model': '$MODEL',
  'messages': [
    {'role':'system','content':'You are a research assistant generating draft paper content. Output ONLY the requested deliverable, no preamble or meta-commentary. Korean and English mixed welcome where appropriate. Cite as placeholders like \\\\cite{author2024short}.'},
    {'role':'user','content': brief}
  ],
  'max_tokens': $MAX_TOKENS,
  'temperature': 0.3,
}))
")
  local response
  response=$(curl -fsS -X POST "$BASE/chat/completions" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $KEY" \
    --max-time 600 \
    -d "$body" 2>&1)
  local curl_ec=$?
  local elapsed=$(($(date +%s) - t0))
  if [[ $curl_ec -ne 0 ]]; then
    echo "[FAIL] $name curl exit=$curl_ec elapsed=${elapsed}s"
    echo "$response" > "$out.error"
    return $curl_ec
  fi
  echo "$response" > "$raw"
  # Extract content
  local content
  content=$(python3 -c "
import json, sys
d = json.loads(open('$raw').read())
print(d['choices'][0]['message']['content'])
" 2>&1)
  if [[ -z "$content" || "$content" =~ Traceback ]]; then
    echo "[FAIL] $name content extraction failed"
    return 3
  fi
  printf '%s\n' "$content" > "$out"
  local toks=$(python3 -c "
import json
d = json.loads(open('$raw').read())
u = d.get('usage', {})
print(f\"in={u.get('prompt_tokens')} out={u.get('completion_tokens')} reasoning={(u.get('completion_tokens_details') or {}).get('reasoning_tokens')}\")
" 2>&1)
  echo "[done] $name elapsed=${elapsed}s tokens($toks)"
}

# Find all briefs
briefs=( "$LAB"/briefs/mimo/*.md )
if [[ ! -f "${briefs[0]}" ]]; then
  _log "no briefs found in $LAB/briefs/mimo/"; exit 1
fi
_log "found ${#briefs[@]} briefs"

# Fire concurrent
running=0
for b in "${briefs[@]}"; do
  while [[ $running -ge $MAX_PARALLEL ]]; do
    wait -n
    ((running--))
  done
  dispatch_one "$b" &
  ((running++))
done
wait
_log "all dispatches finished"

# Summary
echo ""
echo "=== DRAFTS ==="
ls -la "$OUT_DIR"/*_draft_mimo.md 2>/dev/null | head -20

date -u +%Y-%m-%dT%H:%M:%SZ > "$LAB/results/MIMO_DISPATCH_COMPLETE"
