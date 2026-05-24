"""Generic agent runner — invokes a Claude Agent SDK subagent with task context.

Each agent module exports `SYSTEM_PROMPT` (or loads it from prompts/) and
optionally a `tools` list. The runner here is the bridge between the scheduler's
SQLite-tracked tasks and the Claude Agent SDK execution.

Why a thin runner instead of direct subagent calls:
- Centralizes cost tracking. Every Claude/OpenAI call goes through one place.
- Centralizes timeout / retry logic. Agents don't reimplement.
- Centralizes the decision-log emission so we never forget.
- Makes it easy to swap the SDK or even the LLM provider per agent.
"""

from __future__ import annotations

import importlib
import time
from pathlib import Path
from typing import Any

from loguru import logger

from orchestrator.budget import BudgetGuard
from orchestrator.queue import Task


async def run_agent(
    agent_name: str,
    task: Task,
    compute_target: str,
    budget: BudgetGuard,
) -> dict[str, Any]:
    """Dispatch a task to its assigned agent and return an outcome dict.

    The outcome should include:
      - summary: human-readable one-paragraph description
      - inputs / outputs: paths or identifiers
      - cost_usd: total spend for this task
      - artifacts: list of file paths the agent produced
      - reversibility: how to undo if needed
      - human_approval_required: bool (set True if Tier 2 result needs sign-off)
    """
    module = importlib.import_module(f"agents.{agent_name}")
    handler = getattr(module, "handle", None)
    if handler is None:
        raise RuntimeError(f"agent {agent_name} has no handle() function")

    start = time.time()
    try:
        outcome = await handler(task=task, compute_target=compute_target, budget=budget)
    except Exception as e:
        logger.exception(f"Agent {agent_name} raised: {e}")
        raise
    outcome.setdefault("elapsed_seconds", time.time() - start)
    outcome.setdefault("agent", agent_name)
    return outcome


def load_prompt(name: str) -> str:
    """Load a system prompt from prompts/ — versioned in Git so we can attribute drift."""
    path = Path("prompts") / f"{name}.md"
    return path.read_text()
