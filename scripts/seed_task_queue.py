"""Seed the task queue with the W1 work plan.

Run once after the first scheduler boot. Idempotent (skips if tasks
already exist with matching kinds).
"""

from __future__ import annotations

import asyncio
import os

from orchestrator.queue import TaskQueue


W1_PLAN = [
    # Layer 1 data foundations
    dict(kind="layer1_data_collection", agent="data_steward", tier=1, priority="high",
         payload={"subkind": "nemotron_sample", "n": 1000},
         justification="W1 Layer 1: demographic skeleton."),
    dict(kind="layer1_data_collection", agent="data_steward", tier=1, priority="high",
         payload={"subkind": "culturebank_korean_subset"},
         justification="W1 Layer 1: cultural descriptors."),
    dict(kind="layer1_data_collection", agent="data_steward", tier=1, priority="high",
         payload={"subkind": "wvs_wave7_korea"},
         justification="W1 Layer 1: WVS reference distribution."),
    # Library audit at end of W1
    dict(kind="lineage_audit", agent="librarian", tier=1, priority="normal",
         payload={"subkind": "lineage_audit"},
         justification="W1 close-out: confirm all data has manifests."),
    # First daily digest cron-style
    dict(kind="daily_digest", agent="librarian", tier=1, priority="low",
         payload={"subkind": "daily_digest"},
         justification="Recurring 08:00 KST digest."),
]


# W2: validity-spec tasks that must be done BEFORE any downstream analyst code
# computes CCR / AAS / GCS. Skipping these is risk R4 in
# decisions/2026-05-24-known-risks.md.
W2_PLAN = [
    dict(kind="validity_spec", agent="data_steward", tier=2, priority="high",
         payload={
             "subkind": "meas_to_ground_truth_mapping",
             "metrics": ["CCR", "AAS", "GCS"],
             "ground_truth_sources": ["kosis", "naver_datalab", "kofice"],
             "output_file": "data/spec/meas_mapping.yaml",
             "required_fields": ["series_id", "time_window", "cohort_decomposition",
                                 "mapping_function", "known_limitations"],
             "needs_human_review": True,
         },
         justification="W2 R4 mitigation: define how MEAS theory metrics map to "
                       "KOSIS / Naver / KOFICE series before analyst.py computes them. "
                       "Blocks W3+ analyst work."),
    dict(kind="evaluator_tier_check", agent="qa_meta", tier=2, priority="high",
         payload={
             "subkind": "irb_status_check",
             "decision_deadline": "2026-06-21",  # end of W4
             "tiers": ["A", "B", "C", "D"],
             "default_if_no_response": "C",
         },
         justification="W2 evaluator-status snapshot. By W4 Friday QA Meta proposes "
                       "tier A/B/C/D based on IRB and recruitment progress. See "
                       "EVALUATOR_FALLBACK.md."),
    dict(kind="judge_panel_dry_run", agent="analyst", tier=1, priority="normal",
         payload={
             "subkind": "panel_smoke_test",
             "n_personas": 5,
             "output_file": "results/qa/judge_panel_dry_run.json",
         },
         justification="W2 sanity check: exercise the 4-model judge panel on 5 "
                       "personas to confirm all 4 judges respond, ICC is finite, "
                       "and total cost stays within $0.20."),
]


def all_plans() -> list[dict]:
    """Return W1 + W2 plans. Scheduler enqueues all; queue's idempotency on
    (kind, payload['subkind']) prevents double-seeding."""
    return list(W1_PLAN) + list(W2_PLAN)


async def main() -> None:
    queue = TaskQueue(os.environ["ORCHESTRATOR_DB"])
    for t in all_plans():
        task_id = await queue.enqueue(**t)
        print(f"Enqueued {t['kind']}/{t['payload'].get('subkind', '-')} → {task_id}")


if __name__ == "__main__":
    asyncio.run(main())
