"""Principal Investigator (PI) agent — daily research-integrity audit.

Runs at 07:00 KST each morning, before the librarian's 08:00 digest.
Reviews the last 24h of decisions, results, and Writer drafts; assesses
whether the project is still on the rails toward the stated research
questions.

Operating questions (per SELF_EVAL_LOOP.md):
1. Hypothesis drift: any implicit RQ change?
2. Metric drift: results reporting metrics outside KPI_FRAMEWORK.md?
3. Coherence: do section drafts tell one story?
4. Emergent findings: anything that suggests a new RQ (flag, don't act).
5. Status: queue and cost health summary.

Authority:
- Tier 3 ONLY. PI flags issues, never acts on them autonomously.
- Output is read by Sunwoo each morning; he decides remediations.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from anthropic import AsyncAnthropic
from loguru import logger

from agents.runner import load_prompt
from orchestrator.budget import BudgetGuard
from orchestrator.queue import Task


SYSTEM_PROMPT_NAME = "principal_investigator"


async def handle(task: Task, compute_target: str, budget: BudgetGuard) -> dict[str, Any]:
    """Run a daily PI audit."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir = Path("reports/digests")
    out_dir.mkdir(parents=True, exist_ok=True)

    # Gather artifacts of the last 24h
    context_blob = _gather_24h_context()

    # Invoke Claude Sonnet to produce the 5-bullet digest
    client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    system_prompt = load_prompt(SYSTEM_PROMPT_NAME)
    user_prompt = _format_user_prompt(context_blob)

    resp = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    digest_text = resp.content[0].text if resp.content else ""
    cost_usd = (
        (resp.usage.input_tokens * 3 + resp.usage.output_tokens * 15) / 1_000_000
        if resp.usage else 0.0
    )
    budget.record(source="anthropic", usd=cost_usd, task_id=task.id, agent="principal_investigator")

    out_path = out_dir / f"{today}-pi-audit.md"
    out_path.write_text(f"# PI audit — {today}\n\n{digest_text}\n")

    # Determine if escalation is required (CRITICAL/HYPOTHESIS DRIFT triggers it)
    escalate = ("HYPOTHESIS DRIFT" in digest_text and "None" not in digest_text)

    return {
        "summary": f"PI audit for {today} written ({len(digest_text.split())} words).",
        "artifacts": [str(out_path)],
        "cost_usd": cost_usd,
        "human_approval_required": escalate,
        "reversibility": "PI audit is advisory; no destructive actions taken.",
    }


def _gather_24h_context() -> dict[str, Any]:
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)

    decisions_text = []
    for p in sorted(Path("decisions").glob("*.md")):
        if datetime.fromtimestamp(p.stat().st_mtime, timezone.utc) >= yesterday:
            decisions_text.append(p.read_text())

    drafts_text = {}
    for p in sorted(Path("reports/sections").rglob("*.md")) if Path("reports/sections").exists() else []:
        try:
            if datetime.fromtimestamp(p.stat().st_mtime, timezone.utc) >= yesterday:
                drafts_text[p.name] = p.read_text()
        except Exception:
            pass

    results_summary = []
    for p in (Path("results").rglob("*.json") if Path("results").exists() else []):
        try:
            if datetime.fromtimestamp(p.stat().st_mtime, timezone.utc) >= yesterday:
                results_summary.append(str(p))
        except Exception:
            pass

    return {
        "decisions": "\n\n---\n\n".join(decisions_text) if decisions_text else "(no decisions in last 24h)",
        "drafts": drafts_text,
        "result_paths_touched": results_summary,
    }


def _format_user_prompt(context: dict[str, Any]) -> str:
    drafts_summary = "\n\n".join(
        f"### {name}\n{text[:2000]}{'…' if len(text) > 2000 else ''}"
        for name, text in context["drafts"].items()
    ) or "(no draft updates in last 24h)"

    return f"""
You are auditing the past 24h of research lab activity.

## Decisions logged (last 24h)
{context['decisions']}

## Section drafts updated (last 24h, truncated to 2000 chars each)
{drafts_summary}

## Results files touched (last 24h)
{chr(10).join(context['result_paths_touched']) or "(none)"}

## Reference documents (always available, see repo)
- HANDOFF.md — RQs and hypotheses (immutable)
- KPI_FRAMEWORK.md — metric targets
- MOTIVATION_v2.md — long-form motivation
- DEVIATIONS_FROM_PPT.md — design evolution

Produce your audit as a 5-bullet digest. Brevity matters — this is
Sunwoo's first read of the morning.

Format:
1. HYPOTHESIS DRIFT — [None | Description of drift]
2. METRIC DRIFT — [None | Description of metric reported outside KPI framework]
3. COHERENCE — [Status of section drafts as a single story]
4. EMERGENT — [Optional: a finding worth surfacing as a future RQ]
5. STATUS — [One-line health summary]
""".strip()
