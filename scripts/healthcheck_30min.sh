#!/usr/bin/env bash
# healthcheck_30min.sh — read-only status probe for the autonomous research lab.
#
# Runs every 1800 seconds via com.orbt.research-lab.healthcheck launchd job.
# Reports a 4-line compact summary to Slack channel C0ASJUD7JJX (hermes-home).
#
# Touches NOTHING. No kill, no start, no commit. Pure observation:
#   1. NxtGen AWS instance reachability + GPU + free VRAM (single SSH call, 10s budget)
#   2. Lab queue state (read-only sqlite SELECT)
#   3. Budget today/total (read-only sqlite SELECT)
#   4. Most-recent QA Meta tick severity
#   5. Disk free on lab data dir
#
# Designed to be safe to run alongside existing com.orbt.ralph-lab-24x7,
# com.orbt.daily-growth, ai.hermes.gateway — namespace isolated, no shared
# locks, no shared output files, no shared kill signals.
#
# Exit codes:
#   0 — healthy or yellow
#   1 — orange (degraded but running)
#   2 — red/black (intervention needed; alerts on every tick until cleared)

set -uo pipefail

LAB_ROOT="${LAB_ROOT:-/Users/orbt/Desktop/orbt/projects/orbt-research-lab}"
SSH_HOST="${SSH_HOST:-ku-aws}"
SLACK_CHANNEL="${SLACK_CHANNEL_RESEARCH:-C0ASJUD7JJX}"
SLACK_TOKEN_FILE="${SLACK_TOKEN_FILE:-$HOME/.hermes/.env}"
STATE_DIR="$LAB_ROOT/data/state"
mkdir -p "$STATE_DIR"

TS_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
TS_KST="$(TZ='Asia/Seoul' date +%Y-%m-%dT%H:%M:%S%z)"
TICK_LOG="$STATE_DIR/healthcheck.log"

# ---------- helpers (no external deps beyond ssh, sqlite3 if present) -------

_log() { printf '[%s] %s\n' "$TS_UTC" "$*" >> "$TICK_LOG"; }

_slack() {
  # Best-effort Slack post. Failure here is non-fatal — never block a tick.
  local text="$1"
  local token
  if [[ -f "$SLACK_TOKEN_FILE" ]]; then
    token=$(grep -E '^SLACK_BOT_TOKEN=' "$SLACK_TOKEN_FILE" 2>/dev/null \
            | head -1 | cut -d= -f2- | tr -d '"' | tr -d "'")
  fi
  if [[ -z "${token:-}" ]]; then
    _log "slack skipped: no SLACK_BOT_TOKEN in $SLACK_TOKEN_FILE"
    return 0
  fi
  curl -fsS -X POST https://slack.com/api/chat.postMessage \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json; charset=utf-8" \
    -d "$(python3 -c "import json,sys; print(json.dumps({'channel':'$SLACK_CHANNEL','text':sys.argv[1],'mrkdwn':True}))" "$text")" \
    >/dev/null 2>&1 \
    || _log "slack post failed"
}

# ---------- 1. AWS instance reachability ----------

aws_status=""
aws_gpu=""
ssh_result=$(ssh -o ConnectTimeout=8 -o BatchMode=yes "$SSH_HOST" \
  'nvidia-smi --query-gpu=name,memory.used,memory.free --format=csv,noheader 2>/dev/null; \
   df -h ~/orbt-research-lab 2>/dev/null | tail -1 | awk "{print \"disk_free=\" \$4}"; \
   pgrep -af "python.*train.py" | head -1 || echo "no_training_pid"' \
  2>/dev/null) || ssh_result=""

if [[ -z "$ssh_result" ]]; then
  aws_status="DOWN"
  aws_gpu="(unreachable — auto-stopped or instance down)"
else
  aws_status="UP"
  aws_gpu=$(echo "$ssh_result" | head -1)
  aws_disk=$(echo "$ssh_result" | grep '^disk_free=' | cut -d= -f2)
  aws_train=$(echo "$ssh_result" | grep -vE '^(NVIDIA|disk_free=)' | head -1)
fi

# ---------- 2-4. Lab state (sqlite + recent qa_meta tick) ----------

lab_db="$STATE_DIR/../orchestrator.db"
queue_pending=0
queue_failed=0
budget_today=0
budget_total=0
if [[ -f "$lab_db" ]] && command -v sqlite3 >/dev/null; then
  queue_pending=$(sqlite3 "$lab_db" \
    "SELECT COUNT(*) FROM task WHERE state='pending'" 2>/dev/null || echo 0)
  queue_failed=$(sqlite3 "$lab_db" \
    "SELECT COUNT(*) FROM task WHERE state='failed'" 2>/dev/null || echo 0)
  budget_today=$(sqlite3 "$lab_db" \
    "SELECT printf('%.2f', COALESCE(SUM(usd),0)) FROM costs \
     WHERE date(when) = date('now')" 2>/dev/null || echo 0)
  budget_total=$(sqlite3 "$lab_db" \
    "SELECT printf('%.2f', COALESCE(SUM(usd),0)) FROM costs" 2>/dev/null || echo 0)
fi

qa_recent="(no QA Meta tick yet)"
if [[ -d "$LAB_ROOT/results/qa" ]]; then
  qa_latest=$(ls -1t "$LAB_ROOT/results/qa"/*.yaml 2>/dev/null | head -1)
  if [[ -n "$qa_latest" ]]; then
    qa_severity=$(grep -E '^\s*severity:' "$qa_latest" | tail -1 | awk '{print $2}')
    qa_recent="$(basename "$qa_latest") severity=$qa_severity"
  fi
fi

# ---------- 5. Determine overall band + emit ----------

band="green"
[[ "$aws_status" == "DOWN" && "$queue_pending" -gt 0 ]] && band="yellow"
[[ "$queue_failed" -gt 0 ]] && band="orange"
[[ "$queue_failed" -gt 3 ]] && band="red"

ICON="✅"
[[ "$band" == "yellow" ]] && ICON="⚠️"
[[ "$band" == "orange" ]] && ICON="🟠"
[[ "$band" == "red" ]] && ICON="🔴"

# Compose 4-line compact summary
summary=$(cat <<EOF
$ICON *research-lab healthcheck* — $TS_KST — \`$band\`
• AWS: $aws_status — $aws_gpu${aws_disk:+ disk=$aws_disk}${aws_train:+ train_pid=$aws_train}
• Queue: pending=$queue_pending failed=$queue_failed   Budget: today=\$$budget_today total=\$$budget_total/\$400
• QA: $qa_recent
EOF
)

_log "band=$band aws=$aws_status queue=$queue_pending/$queue_failed budget=$budget_today/$budget_total"

# Always post on red/orange; on green/yellow only every 4th tick (2h)
TICK_COUNTER_FILE="$STATE_DIR/healthcheck.tick"
tick_n=0
[[ -f "$TICK_COUNTER_FILE" ]] && tick_n=$(cat "$TICK_COUNTER_FILE")
tick_n=$((tick_n + 1))
echo "$tick_n" > "$TICK_COUNTER_FILE"

if [[ "$band" == "red" ]] || [[ "$band" == "orange" ]] || (( tick_n % 4 == 0 )); then
  _slack "$summary"
fi

case "$band" in
  green|yellow) exit 0 ;;
  orange)       exit 1 ;;
  red|black)    exit 2 ;;
esac
