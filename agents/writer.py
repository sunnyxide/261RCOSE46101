"""Writer agent — drafts paper sections from analyst outputs and decision log.

Hard constraints:
- Writes ONLY to draft/agent-{run_id} branches, never main.
- Must read decision_log + style_guide + section outline before drafting.
- Must cite a results file for every numerical claim.
- Loops with Critic up to WRITER_MAX_ROUNDS; escalates to human after that.

Sections owned (in order of riskiness):
1. Related work (low risk — narrative) — W5
2. Background (low risk) — W5
3. Methods (HIGH RISK — must match what code actually does) — W6 with heavy human review
4. Results (HIGH RISK — numbers must match artifacts) — W7
5. Discussion (MEDIUM — interpretation) — W7
6. Abstract + Intro (write last, after body stabilizes) — W8

Sunwoo writes the methods section himself per the safety protocol.
"""

from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path
from typing import Any

from claude_agent_sdk import query, ClaudeAgentOptions  # type: ignore
from loguru import logger

from agents.runner import load_prompt
from orchestrator.budget import BudgetGuard
from orchestrator.queue import Task

SYSTEM_PROMPT_NAME = "writer"

# Sections the Writer is allowed to draft autonomously.
# Methods is excluded — Sunwoo writes it manually.
ALLOWED_SECTIONS = {"related_work", "background", "results", "discussion", "abstract", "introduction"}


async def handle(task: Task, compute_target: str, budget: BudgetGuard) -> dict[str, Any]:
    section = task.payload["section"]
    if section not in ALLOWED_SECTIONS:
        return {
            "summary": f"Section {section} is not Writer-eligible; escalating.",
            "human_approval_required": True,
            "issues": [{"severity": "error", "msg": f"Section {section} requires human author"}],
        }

    run_id = task.payload.get("run_id", str(uuid.uuid4())[:8])
    branch = f"draft/agent-{run_id}"
    _create_branch(branch)

    system_prompt = load_prompt(SYSTEM_PROMPT_NAME)
    style_guide = Path("reports/style_guide.md").read_text() if Path("reports/style_guide.md").exists() else ""
    decision_log = _aggregate_decision_log()
    outline = Path(f"reports/outlines/{section}.md").read_text()

    user_prompt = f"""
You are drafting the **{section}** section of the COSE461 / ORBT paper.

Style guide (must follow strictly):
---
{style_guide}
---

Decision log (every methodological/experimental decision so far):
---
{decision_log}
---

Section outline (your structural brief):
---
{outline}
---

Constraints:
- Cite every numerical claim with the source file (e.g., [results/static/cas_by_condition.csv]).
- Use BibTeX keys from reports/bibliography.bib only.
- Do not introduce new findings or claims that aren't supported by artifacts in results/.
- Keep prose tight; no hedging beyond what the data supports.

Produce the section as Markdown.
""".strip()

    cost_before = (await budget.report()).total_usd
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-6",
        system_prompt=system_prompt,
        max_turns=1,
        permission_mode="ask",  # never let Writer touch tools, just text out
    )
    output_text = ""
    async for msg in query(prompt=user_prompt, options=options):
        if hasattr(msg, "content"):
            for block in msg.content:
                if hasattr(block, "text"):
                    output_text += block.text

    cost_after = (await budget.report()).total_usd
    section_cost = cost_after - cost_before

    draft_path = Path(f"reports/sections/{section}.md")
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(output_text)
    _commit(branch, [str(draft_path)], message=f"draft: {section} by writer-{run_id}")

    # Auto-enqueue a critic review for this draft
    from orchestrator.queue import TaskQueue
    queue = TaskQueue(os.environ["ORCHESTRATOR_DB"])
    await queue.enqueue(
        kind="critic_review",
        agent="critic",
        tier=2,
        priority="high",
        payload={"draft_path": str(draft_path), "section": section, "run_id": run_id, "round": 0},
        depends_on=[task.id],
        justification="Auto-enqueued by writer to validate draft.",
    )

    return {
        "summary": f"Drafted {section} ({len(output_text.split())} words) on branch {branch}.",
        "artifacts": [str(draft_path)],
        "branch": branch,
        "cost_usd": section_cost,
        "reversibility": f"git branch -D {branch}",
    }


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def _create_branch(branch: str) -> None:
    subprocess.run(["git", "checkout", "-B", branch], check=True)


def _commit(branch: str, files: list[str], message: str) -> None:
    subprocess.run(["git", "add", *files], check=True)
    subprocess.run(["git", "commit", "-m", message], check=True)


def _aggregate_decision_log() -> str:
    """Concatenate all entries from decisions/ in chronological order."""
    entries = sorted(Path("decisions").glob("*.md"))
    return "\n\n---\n\n".join(e.read_text() for e in entries[-50:])  # last 50 to bound context
