"""CultureBank filter with LLM-judged ambiguity escalation.

Logic:
1. Deterministic pass: if `cultural_group` exactly matches "South Korea", commit.
2. Ambiguous pass: rows tagged "East Asian", "Korean diaspora", "Northeast Asia"
   are staged for human review with the LLM's reasoning attached.

The LLM is called only for the ambiguous cases (batched), so cost stays bounded.
"""

from __future__ import annotations

import json
import os
from typing import Any

from anthropic import AsyncAnthropic
from loguru import logger

from orchestrator.budget import BudgetGuard


AMBIGUOUS_GROUPS = {"east asian", "northeast asia", "korean diaspora", "asia"}


async def filter_culturebank_for_korea(
    ds: Any,
    budget: BudgetGuard,
    task_id: str,
) -> tuple[list[dict], list[dict]]:
    committed: list[dict] = []
    ambiguous: list[dict] = []
    for row in ds:
        group = (row.get("cultural_group") or "").strip().lower()
        if group == "south korea":
            committed.append(row)
        elif group in AMBIGUOUS_GROUPS:
            ambiguous.append(row)
    if not ambiguous:
        return committed, []

    # Batch-judge ambiguous cases for review staging
    judged = await _llm_judge_batch(ambiguous, budget, task_id)
    return committed, judged


async def _llm_judge_batch(
    rows: list[dict],
    budget: BudgetGuard,
    task_id: str,
    batch_size: int = 25,
) -> list[dict]:
    client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    out: list[dict] = []
    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        prompt = _format_batch_prompt(batch)
        resp = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            system=(
                "You judge whether each CultureBank row describes a behavior or "
                "value specific to South Korean culture (as opposed to East Asian "
                "more broadly). For each row, return JSON: "
                "{idx, korean_specific: bool, reasoning: str}. Be strict."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
        # cost tracking: rough estimate
        usd_est = (resp.usage.input_tokens * 3 + resp.usage.output_tokens * 15) / 1_000_000
        budget.record(source="anthropic", usd=usd_est, task_id=task_id, agent="data_steward")
        try:
            text = resp.content[0].text if resp.content else "[]"
            judgments = json.loads(text)
        except Exception as e:
            logger.warning(f"Failed to parse judgment batch: {e}")
            judgments = []
        for j in judgments:
            idx = j.get("idx")
            if idx is not None and 0 <= idx < len(batch):
                row = dict(batch[idx])
                row["_judgment"] = j
                out.append(row)
    return out


def _format_batch_prompt(batch: list[dict]) -> str:
    return "\n\n".join(
        f"[{i}] cultural_group={r.get('cultural_group')!r} | "
        f"behavior={r.get('behavior', '')[:200]}"
        for i, r in enumerate(batch)
    )
