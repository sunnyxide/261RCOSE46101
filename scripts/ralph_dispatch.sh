#!/usr/bin/env bash
# ralph_dispatch.sh — fan out batch persona-judgment workload across N parallel
# cores using the proven Ralph Loop pattern.
#
# Used by analyst.py when running tier-C panel CAS scoring at scale:
# 4,800 personas × 4 judges = 19,200 judgments. Serial = ~53h. N=8 cores = ~7h.
#
# Wraps the existing parallel_orchestrator.sh from
# orbtCS-sim-corrections/ralph_lab/. The wrapping responsibilities are:
#
# 1. Materialize per-core input shards from a single persona JSONL.
# 2. Generate per-core PROMPT_research.md with the OpenClaw research_v2
#    output standard inlined (no tool access in completion mode — see
#    feedback-ralph-loop-tuning memory).
# 3. Apply Ralph-Loop tuning constants: max-tokens >= 24000, mkdir-before-
#    spawn, line-anchored verifiability_signal parsing.
# 4. Stream per-core dispatch.log into the lab's results/ tree.
#
# Usage:
#   bash scripts/ralph_dispatch.sh \
#       --personas data/processed/personas_w6.jsonl \
#       --cores 8 \
#       --judges anthropic-opus-4-7,openai-gpt-5,google-gemini-2.5,qwen-3.6-27b \
#       --max-iter 1 \
#       --out results/cas/tier_c_w6/
#
# Exit conditions:
#   - All cores exit cleanly -> exit 0
#   - --halt-on-error and any core fails -> SIGTERM others, exit 1
#   - Wall-time cap exceeded -> SIGTERM all, exit 2

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Default to the proven orchestrator from orbtCS-sim-corrections; allow
# override for local testing.
RALPH_ORCH="${RALPH_ORCH:-/Users/orbt/Desktop/orbt/orbtCS-sim-corrections/ralph_lab/scripts/parallel_orchestrator.sh}"

PERSONAS=""
CORES_N=8
JUDGES="anthropic-opus-4-7,openai-gpt-5,google-gemini-2.5,qwen-3.6-27b"
MAX_ITER=1
MAX_TOKENS=24000
MODEL="mimo-v2.5-pro"
OUT_DIR=""
MAX_WALL_SEC=28800   # 8 hours
HALT_ON_ERROR=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --personas)      PERSONAS="$2"; shift 2 ;;
    --cores)         CORES_N="$2"; shift 2 ;;
    --judges)        JUDGES="$2"; shift 2 ;;
    --max-iter)      MAX_ITER="$2"; shift 2 ;;
    --max-tokens)    MAX_TOKENS="$2"; shift 2 ;;
    --model)         MODEL="$2"; shift 2 ;;
    --out)           OUT_DIR="$2"; shift 2 ;;
    --max-wall-sec)  MAX_WALL_SEC="$2"; shift 2 ;;
    --halt-on-error) HALT_ON_ERROR=1; shift ;;
    -h|--help)
      sed -n '2,/^$/p' "$0" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    *) echo "ERROR: unknown arg $1" >&2; exit 2 ;;
  esac
done

[[ -n "$PERSONAS" ]] || { echo "ERROR: --personas required" >&2; exit 2; }
[[ -n "$OUT_DIR" ]]  || { echo "ERROR: --out required" >&2; exit 2; }
[[ -f "$PERSONAS" ]] || { echo "ERROR: personas file not found: $PERSONAS" >&2; exit 2; }
[[ -x "$RALPH_ORCH" ]] || { echo "ERROR: RALPH_ORCH not executable: $RALPH_ORCH" >&2; exit 2; }
[[ "$MAX_TOKENS" -ge 24000 ]] || { echo "ERROR: --max-tokens must be >= 24000 per feedback-ralph-loop-tuning memory" >&2; exit 2; }

TS="$(date -u +%Y%m%dT%H%M%SZ)"
TASK_ROOT="$OUT_DIR/$TS"
mkdir -p "$TASK_ROOT"
DRIVER_LOG="$TASK_ROOT/dispatcher.log"

echo "[dispatcher $TS] personas=$PERSONAS cores=$CORES_N judges=$JUDGES" | tee -a "$DRIVER_LOG"

# Shard the personas file into $CORES_N near-equal pieces. We use line-count
# split (not size split) so each shard has the same number of judgment tasks.
TOTAL_LINES=$(wc -l < "$PERSONAS")
PER_SHARD=$(( (TOTAL_LINES + CORES_N - 1) / CORES_N ))
echo "[dispatcher] sharding $TOTAL_LINES personas into $CORES_N cores ($PER_SHARD per shard)" | tee -a "$DRIVER_LOG"

CORE_IDS=()
for i in $(seq 1 "$CORES_N"); do
  core_id="cas-shard-$(printf '%02d' "$i")"
  CORE_IDS+=("$core_id")

  # mkdir BEFORE anything that redirects into the dir — fix from 2026-05-21
  # ralph_lab dispatch (4 cores rc=1'ed because mkdir was after spawn).
  CORE_DIR="$TASK_ROOT/cores/$core_id"
  mkdir -p "$CORE_DIR"

  start_line=$(( (i - 1) * PER_SHARD + 1 ))
  sed -n "${start_line},$((start_line + PER_SHARD - 1))p" "$PERSONAS" > "$CORE_DIR/personas.jsonl"

  # Compose the per-core PROMPT_research.md. CRITICAL: "No tool access" line
  # MUST appear at top — fix from 2026-05-21 where mimo-v2.5-pro emitted
  # <tool_call> XML that the completion endpoint can't parse.
  cat > "$CORE_DIR/PROMPT_research.md" <<EOF
# CAS panel judgment — core $core_id

**Output protocol:** You have NO tool access in this completion. Respond
with the full markdown deliverable as plain text — no tool-call XML.

## Task

For each persona in personas.jsonl below, score it on the CURE 5 dimensions
(realism, plausibility, idiom, reasoning, behavior) as a Korean cultural
evaluator. See agents/shared/llm_judge_panel.py for the formal rubric.

## Judges

$JUDGES

## Personas (one JSON object per line)

\`\`\`
$(cat "$CORE_DIR/personas.jsonl")
\`\`\`

## Output

For each persona, emit one block:

\`\`\`yaml
persona_id: <id>
scores:
  realism: <1-5>
  plausibility: <1-5>
  idiom: <1-5>
  reasoning: <1-5>
  behavior: <1-5>
rationale_kr: <up to 200 Korean chars>
\`\`\`

Then at the very end of the file, the required \`[meta]\` footer:

\`\`\`yaml
[meta]
verifiability_signal: high
n_personas_scored: <int>
notes: <any caveats>
\`\`\`
EOF

  echo "[dispatcher] prepared core=$core_id ($(wc -l < "$CORE_DIR/personas.jsonl") personas)" | tee -a "$DRIVER_LOG"
done

# Hand off to the proven orchestrator. RALPH_LAB_ROOT environment variable
# tells ralph_loop.sh where the per-core dirs are.
CORES_CSV=$(IFS=,; echo "${CORE_IDS[*]}")

echo "[dispatcher] handing off to $RALPH_ORCH" | tee -a "$DRIVER_LOG"

RALPH_LAB_ROOT="$TASK_ROOT" \
  "$RALPH_ORCH" \
    --cores "$CORES_CSV" \
    --max-iter "$MAX_ITER" \
    --max-tokens "$MAX_TOKENS" \
    --model "$MODEL" \
    --max-wall-sec "$MAX_WALL_SEC" \
    $( [[ "$HALT_ON_ERROR" -eq 1 ]] && echo "--halt-on-error" ) \
    >> "$DRIVER_LOG" 2>&1
RC=$?

echo "[dispatcher] orchestrator exit=$RC" | tee -a "$DRIVER_LOG"

# Aggregate verifiability_signal across cores into a single summary file
# (line-anchored per feedback-ralph-loop-tuning memory).
SUMMARY="$TASK_ROOT/summary.tsv"
{
  printf "core_id\tverifiability_signal\tpersonas_scored\n"
  for core_id in "${CORE_IDS[@]}"; do
    out_file="$TASK_ROOT/cores/$core_id/output.md"
    if [[ -f "$out_file" ]]; then
      signal=$(grep -E '^verifiability_signal:' "$out_file" | head -1 | awk '{print $2}')
      count=$(grep -c -E '^persona_id:' "$out_file" || true)
      printf "%s\t%s\t%s\n" "$core_id" "${signal:-unknown}" "${count:-0}"
    else
      printf "%s\tNO_OUTPUT\t0\n" "$core_id"
    fi
  done
} > "$SUMMARY"

echo "[dispatcher] summary written to $SUMMARY" | tee -a "$DRIVER_LOG"

exit $RC
