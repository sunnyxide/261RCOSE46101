#!/usr/bin/env bash
# extension_phases.sh — runs after research_pipeline_6h.sh completes.
# Uses the extra 2h NxtGen extension (total 8h budget).
#
# Phase 7: Re-run after-corpus on Run-A specifically (fix for the glob bug)
# Phase 8: Run-C — KULLM-v2 data ablation (rank 16, 1ep, 10k samples)
# Phase 9: after-corpus on Run-C
# Phase 10: KoBBQ mini-eval — 50 Q × 4 models (vanilla / Run-A / Run-B / Run-C)
# Phase 11: 4-way comparative analysis

set -uo pipefail
LAB=~/orbt-research-lab
STATUS=$LAB/results/PIPELINE_STATUS.json

_status() {
  python3 -c "
import json, time, os
p = '$STATUS'
d = json.load(open(p)) if os.path.exists(p) else {'phases': []}
d['phases'].append({'phase': '$1', 'status': '$2', 'notes': '''$3''',
                    'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})
d['last_updated'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
json.dump(d, open(p, 'w'), indent=2, ensure_ascii=False)
"
}

cd $LAB
source .venv/bin/activate
_status extension started "2h overflow: re-after-a + Run-C + KoBBQ + 4-way"

# ----------------------------------------------------------------------------
# Phase 7 — Re-run after-corpus targeting Run-A specifically
# ----------------------------------------------------------------------------
echo "===== Phase 7: re-after-a (Run-A diff that was missed) ====="
_status after-a-retry started ""
RUN_A=$(ls -d $LAB/runs/run-a-* 2>/dev/null | head -1)/adapter_final
if [[ -d "$RUN_A" ]]; then
  python scripts/after_corpus.py --adapter=$RUN_A 2>&1 | tee /tmp/after-a-retry.log
  mv -f $LAB/results/baselines/qwen2.5-3b-qlora-corpus.json \
        $LAB/results/baselines/qwen2.5-3b-qlora-run-a-corpus.json 2>/dev/null
  mv -f $LAB/results/baselines/before_after_diff.md \
        $LAB/results/baselines/before_after_diff_run-a.md 2>/dev/null
  _status after-a-retry complete "Run-A diff now exists"
else
  _status after-a-retry skipped "Run-A adapter not found"
fi

# ----------------------------------------------------------------------------
# Phase 8 — Run-C: KULLM-v2 data ablation
# ----------------------------------------------------------------------------
echo "===== Phase 8: Run-C (KULLM-v2, rank 16, 1ep, 10k) ====="
_status run-c started "KULLM-v2 data ablation"
RUN_C_ID="run-c-kullm-rank16-$(date -u +%Y%m%dT%H%M%SZ)"
python scripts/qlora_train.py \
  --run-id "$RUN_C_ID" \
  --dataset nlpai-lab/kullm-v2 \
  --max-samples 10000 \
  --num-epochs 1 \
  --lora-rank 16 \
  --save-steps 100 \
  --eval-steps 200 2>&1 | tee /tmp/run-c.log
RC=$?
if [[ $RC -ne 0 ]]; then
  _status run-c failed "exit=$RC"
  echo "Run-C failed; remaining results preserved"
else
  _status run-c complete "adapter at runs/$RUN_C_ID/adapter_final"
fi

# ----------------------------------------------------------------------------
# Phase 9 — after-corpus on Run-C
# ----------------------------------------------------------------------------
if [[ $RC -eq 0 ]]; then
  echo "===== Phase 9: after-corpus on Run-C ====="
  _status after-c started ""
  RUN_C_ADAPTER=$LAB/runs/$RUN_C_ID/adapter_final
  python scripts/after_corpus.py --adapter=$RUN_C_ADAPTER 2>&1 | tee /tmp/after-c.log
  mv -f $LAB/results/baselines/qwen2.5-3b-qlora-corpus.json \
        $LAB/results/baselines/qwen2.5-3b-qlora-run-c-corpus.json 2>/dev/null
  mv -f $LAB/results/baselines/before_after_diff.md \
        $LAB/results/baselines/before_after_diff_run-c.md 2>/dev/null
  _status after-c complete ""
fi

# ----------------------------------------------------------------------------
# Phase 10 — KoBBQ mini-eval
# ----------------------------------------------------------------------------
echo "===== Phase 10: KoBBQ mini-eval (4 models × 50 Q) ====="
_status kobbq started ""
python scripts/kobbq_eval.py 2>&1 | tee /tmp/kobbq.log
_status kobbq complete ""

# ----------------------------------------------------------------------------
# Phase 11 — 4-way comparison
# ----------------------------------------------------------------------------
echo "===== Phase 11: 4-way analysis (vanilla / A / B / C) ====="
_status compare-4way started ""
python scripts/compare_4way.py 2>&1 | tee /tmp/compare-4way.log
_status compare-4way complete ""

_status extension complete "all 5 extension phases done"
echo "===== EXTENSION_COMPLETE ====="
