#!/usr/bin/env bash
# hermes_research_cycle.sh — picks the next unstarted lab brief and runs it
# via the Xiaomi Plan endpoint (token-plan-sgp.xiaomimimo.com), saving output
# to results/hermes_outputs/.
#
# Designed for launchd cron com.orbt.research-lab.hermes-cycle, every 2 hours.
# Keeps the research project producing deliverables while Sunwoo is away and
# the AWS instance is auto-stopped.
#
# Uses existing dispatch_plan_research.sh wrapper for auth + payload.
#
# Brief queue convention:
#   briefs/lab/NN_short_name.md  (NN = 01, 02, ...)
#   Script picks LOWEST-numbered brief whose output file is missing.
#
# Output convention:
#   results/hermes_outputs/NN_short_name.md
#   results/hermes_outputs/NN_short_name.md.raw.json
#   results/hermes_outputs/NN_short_name.tick.log
#
# Concurrency: flock prevents overlapping cycles.

set -uo pipefail

LAB="${LAB:-/Users/orbt/Desktop/orbt/projects/orbt-research-lab}"
DISPATCH="${DISPATCH:-/Users/orbt/Desktop/orbt/overnight-agents/scripts/openclaw/dispatch_plan_research.sh}"
MODEL="${MODEL:-mimo-v2.5-pro}"
SLACK_CHANNEL="${SLACK_CHANNEL_RESEARCH:-C0ASJUD7JJX}"
SLACK_TOKEN_FILE="${SLACK_TOKEN_FILE:-$HOME/.hermes/.env}"
LOCK_DIR="/tmp/orbt-research-lab.hermes-cycle.lock.d"

TS_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
TS_KST="$(TZ='Asia/Seoul' date +%Y-%m-%dT%H:%M:%S%z)"

# ---------- helpers ----------

_post_slack() {
  local text="$1"
  local token
  if [[ -f "$SLACK_TOKEN_FILE" ]]; then
    token=$(grep -E '^SLACK_BOT_TOKEN=' "$SLACK_TOKEN_FILE" 2>/dev/null \
            | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
  fi
  [[ -z "${token:-}" ]] && return 0
  curl -fsS -X POST https://slack.com/api/chat.postMessage \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json; charset=utf-8" \
    -d "$(python3 -c "import json,sys; print(json.dumps({'channel':sys.argv[1],'text':sys.argv[2],'mrkdwn':True}))" "$SLACK_CHANNEL" "$text")" \
    >/dev/null 2>&1 || true
}

# ---------- lock + preflight ----------
# mkdir-based lock — POSIX atomic, no flock dependency (macOS doesn't ship flock).

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  if [[ -f "$LOCK_DIR/pid" ]]; then
    other_pid=$(cat "$LOCK_DIR/pid" 2>/dev/null)
    if [[ -n "$other_pid" ]] && kill -0 "$other_pid" 2>/dev/null; then
      echo "[hermes-cycle $TS_UTC] another tick in progress (pid=$other_pid), skipping"
      exit 0
    fi
    echo "[hermes-cycle $TS_UTC] stale lock from dead pid $other_pid, reclaiming"
    rm -rf "$LOCK_DIR"
    mkdir "$LOCK_DIR" || { echo "[hermes-cycle] cannot create lock dir, abort"; exit 0; }
  else
    echo "[hermes-cycle $TS_UTC] lock dir exists without pid file, reclaiming"
    rm -rf "$LOCK_DIR"
    mkdir "$LOCK_DIR" || exit 0
  fi
fi
echo $$ > "$LOCK_DIR/pid"
trap 'rm -rf "$LOCK_DIR"' EXIT

if [[ ! -x "$DISPATCH" ]]; then
  echo "[hermes-cycle $TS_UTC] ERROR: dispatch script not found: $DISPATCH" >&2
  _post_slack ":x: hermes-cycle preflight fail — dispatch script missing at \`$DISPATCH\`"
  exit 2
fi

BRIEFS_DIR="$LAB/briefs/lab"
if [[ ! -d "$BRIEFS_DIR" ]]; then
  echo "[hermes-cycle $TS_UTC] ERROR: $BRIEFS_DIR missing" >&2
  exit 2
fi

OUT_DIR="$LAB/results/hermes_outputs"
mkdir -p "$OUT_DIR"

# Source ~/.hermes/.env to pull XIAOMI_PLAN_API_KEY (tp-) + SLACK_BOT_TOKEN
if [[ -f "$HOME/.hermes/.env" ]]; then
  set +e
  set -a; source "$HOME/.hermes/.env" 2>/dev/null; set +a
  set -e
fi

# ---------- pick next brief ----------

NEXT_BRIEF=""
NEXT_NAME=""
for brief_path in $(ls "$BRIEFS_DIR"/[0-9][0-9]_*.md 2>/dev/null | sort); do
  base="$(basename "$brief_path" .md)"
  out_file="$OUT_DIR/$base.md"
  if [[ ! -f "$out_file" || ! -s "$out_file" ]]; then
    NEXT_BRIEF="$brief_path"
    NEXT_NAME="$base"
    break
  fi
done

if [[ -z "$NEXT_BRIEF" ]]; then
  echo "[hermes-cycle $TS_UTC] all briefs complete, nothing to do"
  if [[ ! -f "$OUT_DIR/.queue_drained" ]]; then
    touch "$OUT_DIR/.queue_drained"
    _post_slack ":white_check_mark: research-lab hermes queue drained at $TS_KST. All briefs processed. Disable the cron with: launchctl bootout gui/\$UID/com.orbt.research-lab.hermes-cycle"
  fi
  exit 0
fi

echo "[hermes-cycle $TS_UTC] running $NEXT_NAME via $MODEL"
TICK_LOG="$OUT_DIR/$NEXT_NAME.tick.log"
OUT_FILE="$OUT_DIR/$NEXT_NAME.md"

# ---------- dispatch ----------
# TCC workaround: launchd-spawned Python cannot open files under ~/Desktop/
# (macOS Privacy & Security restricts non-GUI processes). Copy the brief
# and system prompt to /tmp first, point dispatch there. /tmp has no TCC.
TMP_RUN_DIR=$(mktemp -d /tmp/orbt-hermes-XXXXXX)
trap 'rm -rf "$LOCK_DIR" "$TMP_RUN_DIR"' EXIT
SYS_PROMPT_SRC=/Users/orbt/Desktop/orbt/overnight-agents/prompts/openclaw/research_v2.md
TMP_BRIEF="$TMP_RUN_DIR/brief.md"
TMP_SYSTEM="$TMP_RUN_DIR/system.md"
TMP_OUT="$TMP_RUN_DIR/out.md"
cp "$NEXT_BRIEF" "$TMP_BRIEF" 2>/dev/null
cp "$SYS_PROMPT_SRC" "$TMP_SYSTEM" 2>/dev/null

{
  echo "=== hermes-cycle tick $TS_UTC ==="
  echo "brief: $NEXT_BRIEF (copied to $TMP_BRIEF)"
  echo "model: $MODEL"
  echo "out:   $OUT_FILE (via $TMP_OUT)"
  echo "system: $SYS_PROMPT_SRC (copied to $TMP_SYSTEM)"
  echo
  if [[ ! -s "$TMP_BRIEF" || ! -s "$TMP_SYSTEM" ]]; then
    echo "ERROR: failed to copy files to /tmp (TCC blocks bash too?)"
    RC=2
  else
    "$DISPATCH" --model "$MODEL" --brief "$TMP_BRIEF" --out "$TMP_OUT" \
      --system "$TMP_SYSTEM"
    RC=$?
    # Copy output back to its real home so other tools see it
    if [[ -s "$TMP_OUT" ]]; then
      cp "$TMP_OUT" "$OUT_FILE" 2>/dev/null
      [[ -f "$TMP_OUT.raw.json" ]] && cp "$TMP_OUT.raw.json" "$OUT_FILE.raw.json" 2>/dev/null
    fi
  fi
  echo
  echo "=== dispatch exit: $RC ==="
} > "$TICK_LOG" 2>&1
RC=$?

# ---------- auto-commit on success ----------

if [[ $RC -eq 0 && -s "$OUT_FILE" ]]; then
  cd "$LAB"
  git add "results/hermes_outputs/$NEXT_NAME.md" \
          "results/hermes_outputs/$NEXT_NAME.md.raw.json" \
          "results/hermes_outputs/$NEXT_NAME.tick.log" 2>>"$TICK_LOG"
  if ! git diff --staged --quiet; then
    git -c user.name="Sunwoo Ju" -c user.email="sunwo1224@korea.ac.kr" \
      commit -m "hermes-cycle: $NEXT_NAME completed at $TS_KST" >>"$TICK_LOG" 2>&1 || true
    git push origin main >>"$TICK_LOG" 2>&1 || true
  fi
fi

# ---------- slack notify ----------

if [[ $RC -eq 0 && -s "$OUT_FILE" ]]; then
  CHARS=$(wc -c < "$OUT_FILE" | tr -d ' ')
  SIGNAL=$(grep -E '^verifiability_signal:' "$OUT_FILE" | head -1 | awk '{print $2}')
  _post_slack ":rocket: hermes-cycle done — *$NEXT_NAME*
• Model: \`$MODEL\` | KST: $TS_KST | Out: ${CHARS}c | Signal: \`${SIGNAL:-unknown}\`
• File: \`results/hermes_outputs/$NEXT_NAME.md\` (auto-committed)"
else
  TAIL=$(tail -15 "$TICK_LOG" 2>/dev/null | tr -d '\r')
  _post_slack ":x: hermes-cycle FAILED — *$NEXT_NAME* (exit=$RC)
KST: $TS_KST
Tail:
\`\`\`
${TAIL}
\`\`\`"
fi

exit 0
