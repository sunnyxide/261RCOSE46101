#!/usr/bin/env bash
# paper_autofill_watchdog.sh — Mac-side watchdog that polls AWS for new
# cross_cultural_*.json files, syncs them down, regenerates aggregator
# tables, and refills paper.tex placeholders. Commits + pushes when paper
# content actually changes.
#
# Run: nohup bash scripts/paper_autofill_watchdog.sh > logs/paper_autofill.log 2>&1 &
set -uo pipefail
LAB="$(cd "$(dirname "$0")/.." && pwd)"
KEY=~/.ssh/ku-lbj-key.pem
AWS_A=54.91.146.199
AWS_B=54.198.8.209
LOG="$LAB/logs/paper_autofill.log"
DURATION=$((12 * 3600))
INTERVAL=600   # 10 min
START=$(date -u +%s)

mkdir -p "$LAB/logs"
_log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }
_log "paper_autofill_watchdog START"

LAST_FINGERPRINT=""

while true; do
  NOW=$(date -u +%s)
  ELAPSED=$((NOW - START))
  if [[ $ELAPSED -gt $DURATION ]]; then _log "12h cap — stopping"; break; fi

  # Pull cross_cultural + HAE-RAE results from both instances (silent on failure)
  for host in "$AWS_A" "$AWS_B"; do
    rsync -avz --ignore-existing -e "ssh -i $KEY -o BatchMode=yes -o ConnectTimeout=15" \
      "ubuntu@${host}:/home/ubuntu/orbt-research-lab/results/benchmarks/cross_cultural_*.json" \
      "$LAB/results/benchmarks/" >> "$LOG" 2>&1 || true
    rsync -avz --ignore-existing -e "ssh -i $KEY -o BatchMode=yes -o ConnectTimeout=15" \
      "ubuntu@${host}:/home/ubuntu/orbt-research-lab/results/benchmarks/phase1_*FIXED*.json" \
      "$LAB/results/benchmarks/" >> "$LOG" 2>&1 || true
  done

  # Fingerprint current data so we only update on change
  FP=$(find "$LAB/results/benchmarks" -name "cross_cultural_*.json" -newer /tmp/non-existent 2>/dev/null | \
       sort | xargs cat 2>/dev/null | md5 2>/dev/null || echo "")
  COUNT=$(ls "$LAB/results/benchmarks"/cross_cultural_*.json 2>/dev/null | wc -l | tr -d ' ')

  if [[ "$FP" != "$LAST_FINGERPRINT" ]]; then
    _log "data changed ($COUNT cross_cultural files) — refilling paper"
    cd "$LAB"
    python3 scripts/aggregate_results.py 2>&1 | tee -a "$LOG"
    python3 scripts/update_paper_from_results.py 2>&1 | tee -a "$LOG"

    # Only commit if paper.tex actually changed
    if ! git diff --quiet reports/overleaf/paper.tex reports/final_results_table.md reports/final_summary.json; then
      git add reports/overleaf/paper.tex reports/final_results_table.md reports/final_summary.json \
              results/benchmarks/cross_cultural_*.json results/benchmarks/phase1_*FIXED*.json 2>/dev/null
      git commit -m "auto: paper tables refreshed from new AWS results ($COUNT cross_cultural cells)" \
                 >> "$LOG" 2>&1
      git push origin HEAD >> "$LOG" 2>&1
      _log "committed + pushed paper update"
    fi
    LAST_FINGERPRINT="$FP"
  fi

  # Stop if both INSTANCE_*_HAERAE_COMPLETE sentinels exist (final stage done)
  if ssh -i "$KEY" -o ConnectTimeout=10 -o BatchMode=yes ubuntu@"$AWS_A" \
       "[[ -f ~/orbt-research-lab/results/INSTANCE_A_HAERAE_COMPLETE ]]" 2>/dev/null \
       && ssh -i "$KEY" -o ConnectTimeout=10 -o BatchMode=yes ubuntu@"$AWS_B" \
            "[[ -f ~/orbt-research-lab/results/INSTANCE_B_HAERAE_COMPLETE ]]" 2>/dev/null; then
    _log "BOTH HAE-RAE rerun sentinels present — final refill, then stop"
    sleep 60   # last sync window
    cd "$LAB"
    python3 scripts/aggregate_results.py 2>&1 | tee -a "$LOG"
    python3 scripts/update_paper_from_results.py 2>&1 | tee -a "$LOG"
    if ! git diff --quiet reports/overleaf/paper.tex; then
      git add -A
      git commit -m "auto: final paper refresh — both HAE-RAE rerun sentinels present" >> "$LOG" 2>&1
      git push origin HEAD >> "$LOG" 2>&1
    fi
    date -u +%Y-%m-%dT%H:%M:%SZ > "$LAB/results/PAPER_FINAL_AUTOFILL_DONE"
    break
  fi

  _log "tick t+$((ELAPSED/60))min cc_files=$COUNT — sleeping ${INTERVAL}s"
  sleep $INTERVAL
done

_log "paper_autofill_watchdog END"
