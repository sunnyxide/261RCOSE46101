"""
Orchestrator scheduler — the heartbeat of the autonomous lab.

Runs as a systemd/launchd service on the Mac Mini. Pulls tasks from the
SQLite-backed queue, dispatches them to the appropriate agent worker,
enforces budget caps, and writes outcomes to the decision log.

Design principles:
- Idempotent: a task can be re-dispatched safely after a crash.
- Blast-radius bounded: a single failed task does not halt other agents.
- Auditable: every dispatch and every outcome is logged with timestamps.
- Cheap to read state: the SQLite DB is the single source of truth for
  the orchestrator; agents persist their artifacts to the Git repo and DVC.
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table

from orchestrator.budget import BudgetGuard
from orchestrator.queue import Task, TaskQueue, TaskStatus
from orchestrator.router import ResourceRouter

app = typer.Typer(help="ORBT research-lab orchestrator")
console = Console()

# Agents registered with their entry-point modules. Each agent is a Claude
# Agent SDK subagent; the scheduler invokes it via a thin runner.
AGENTS = {
    "data_steward": "agents.data_steward",
    "experiment_runner": "agents.experiment_runner",
    "analyst": "agents.analyst",
    "writer": "agents.writer",
    "critic": "agents.critic",
    "librarian": "agents.librarian",
}

# Agents allowed at each tier. Heavy mode unlocks all.
TIER_PERMISSIONS = {
    "light": {"data_steward", "experiment_runner", "analyst", "librarian"},
    "medium": {"data_steward", "experiment_runner", "analyst", "librarian", "critic"},
    "heavy": set(AGENTS.keys()),
}


class Scheduler:
    def __init__(self) -> None:
        self.queue = TaskQueue(os.environ["ORCHESTRATOR_DB"])
        self.budget = BudgetGuard()
        self.router = ResourceRouter()
        self.autonomy_tier = os.environ.get("AUTONOMY_TIER", "light")
        self.allowed_agents = TIER_PERMISSIONS[self.autonomy_tier]
        self.shutdown_requested = False
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum: int, frame) -> None:  # noqa: ANN001
        logger.warning(f"Received signal {signum}, finishing current task then halting.")
        self.shutdown_requested = True

    async def run_forever(self) -> None:
        logger.info(f"Scheduler starting in tier={self.autonomy_tier}")
        await self.budget.assert_within_limits()  # gate at boot too
        while not self.shutdown_requested:
            try:
                await self._tick()
            except Exception as e:  # noqa: BLE001 — top-level guard
                logger.exception(f"Scheduler tick failed: {e}")
                await self._alert_humans(severity="critical", message=str(e))
            await asyncio.sleep(5)
        logger.info("Scheduler halted cleanly.")

    async def _tick(self) -> None:
        # Hard kill if daily budget breached
        if not await self.budget.is_within_daily_limit():
            await self.queue.pause_all()
            await self._alert_humans(severity="critical", message="Daily budget exceeded.")
            self.shutdown_requested = True
            return

        # Pull next runnable task (highest priority, ready dependencies)
        task = await self.queue.next_runnable()
        if task is None:
            return

        if task.agent not in self.allowed_agents:
            logger.warning(
                f"Task {task.id} requires agent={task.agent}, "
                f"not permitted at tier={self.autonomy_tier}. Escalating."
            )
            await self.queue.escalate(task)
            return

        # Route to appropriate compute (Mac vs AWS)
        target = self.router.pick(task)
        logger.info(f"Dispatching task {task.id} ({task.kind}) → {task.agent}@{target}")
        await self.queue.mark_running(task.id)
        try:
            outcome = await self._dispatch(task, target)
            await self.queue.mark_complete(task.id, outcome)
            await self._log_decision(task, outcome)
        except Exception as e:  # noqa: BLE001
            logger.exception(f"Task {task.id} failed: {e}")
            await self.queue.mark_failed(task.id, error=str(e))
            await self._alert_humans(severity="warning", message=f"Task {task.id} failed: {e}")

    async def _dispatch(self, task: Task, target: str) -> dict:
        """Invoke the Claude Agent SDK subagent for this task."""
        from agents.runner import run_agent

        return await run_agent(
            agent_name=task.agent,
            task=task,
            compute_target=target,
            budget=self.budget,
        )

    async def _log_decision(self, task: Task, outcome: dict) -> None:
        """Append a structured decision entry to decisions/ directory."""
        decisions_dir = Path("decisions")
        decisions_dir.mkdir(exist_ok=True)
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = decisions_dir / f"{date}-{task.kind}-{task.id[:8]}.md"
        path.write_text(
            f"""---
date: {datetime.now(timezone.utc).isoformat()}
agent: {task.agent}
task_id: {task.id}
task_kind: {task.kind}
tier: {task.tier}
auto_executed: {task.tier <= 2}
human_approved: {outcome.get('human_approved', 'n/a')}
cost_usd: {outcome.get('cost_usd', 0)}
---

## What
{outcome.get('summary', '(no summary)')}

## Why
{task.justification or '(scheduled)'}

## Inputs
{outcome.get('inputs', 'see task.input_paths')}

## Outputs
{outcome.get('outputs', 'see task.output_paths')}

## Reversibility
{outcome.get('reversibility', 'see runbook')}
"""
        )

    async def _alert_humans(self, severity: str, message: str) -> None:
        # Slack bot lives in another process; we just write to alerts table
        await self.queue.enqueue_alert(severity=severity, message=message)


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

@app.command()
def run() -> None:
    """Start the scheduler loop (typically invoked by systemd/launchd)."""
    asyncio.run(Scheduler().run_forever())


@app.command()
def enqueue(
    task: str = typer.Option(..., help="Task kind, e.g. layer1_data_collection"),
    agent: str = typer.Option(..., help="Agent name"),
    tier: int = typer.Option(1, help="Tier 1/2/3"),
    priority: str = typer.Option("normal", help="low|normal|high|critical"),
    justification: str | None = typer.Option(None),
) -> None:
    queue = TaskQueue(os.environ["ORCHESTRATOR_DB"])
    task_id = asyncio.run(
        queue.enqueue(
            kind=task,
            agent=agent,
            tier=tier,
            priority=priority,
            justification=justification or f"manual enqueue at {datetime.now(timezone.utc)}",
        )
    )
    console.print(f"[green]Enqueued[/green] task {task_id}")


@app.command()
def status() -> None:
    queue = TaskQueue(os.environ["ORCHESTRATOR_DB"])
    rows = asyncio.run(queue.summary())
    table = Table(title="Lab status")
    for col in ["state", "count", "oldest", "newest"]:
        table.add_column(col)
    for r in rows:
        table.add_row(r["state"], str(r["count"]), str(r["oldest"]), str(r["newest"]))
    console.print(table)
    budget = BudgetGuard()
    console.print(asyncio.run(budget.report_text()))


@app.command()
def kill_all() -> None:
    """Emergency stop — halt all running tasks, release AWS resources."""
    queue = TaskQueue(os.environ["ORCHESTRATOR_DB"])
    n = asyncio.run(queue.pause_all())
    console.print(f"[red]Emergency stop[/red]: paused {n} running tasks.")
    from orchestrator.router import ResourceRouter

    n_inst = ResourceRouter().stop_all_aws_instances()
    console.print(f"[red]Stopped[/red] {n_inst} AWS instances.")


if __name__ == "__main__":
    app()
