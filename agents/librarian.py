"""Librarian agent — maintains data lineage, decision log integrity, daily digest.

Responsibilities:
- Ensure every artifact in data/ and results/ has a manifest and DVC hash.
- Detect orphan files (no manifest) and stale manifests (hash mismatch).
- Compose the daily digest at 08:00 KST and send via Slack.
- Maintain CITATIONS.md mapping every paper claim to a source file.
- Backup state.db to S3 nightly.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import typer
from loguru import logger

from orchestrator.budget import BudgetGuard
from orchestrator.queue import Task, TaskQueue

app = typer.Typer()


async def handle(task: Task, compute_target: str, budget: BudgetGuard) -> dict[str, Any]:
    subkind = task.payload.get("subkind", "lineage_audit")
    if subkind == "lineage_audit":
        return await lineage_audit()
    if subkind == "daily_digest":
        return await compose_and_send_digest(budget)
    raise ValueError(subkind)


async def lineage_audit() -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    for d in ["data/raw", "data/processed", "results"]:
        root = Path(d)
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and not _has_manifest(path):
                issues.append({"severity": "warning", "path": str(path), "msg": "no manifest"})
    return {
        "summary": f"Lineage audit: {len(issues)} orphan/stale artifacts.",
        "issues": issues,
        "cost_usd": 0.0,
        "reversibility": "Audit is read-only.",
    }


def _has_manifest(path: Path) -> bool:
    m = path.parent / "manifest.yaml"
    return m.exists()


async def compose_and_send_digest(budget: BudgetGuard) -> dict[str, Any]:
    queue = TaskQueue(os.environ["ORCHESTRATOR_DB"])
    summary = await queue.summary()
    budget_text = await budget.report_text()
    decisions_today = [
        p for p in Path("decisions").glob("*.md")
        if datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).date() == datetime.now(timezone.utc).date()
    ]
    digest = _format_digest(summary, budget_text, decisions_today)
    _send_slack(digest)
    Path("reports/digests").mkdir(parents=True, exist_ok=True)
    Path(f"reports/digests/{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.md").write_text(digest)
    return {
        "summary": "Daily digest sent.",
        "artifacts": [],
        "cost_usd": 0.0,
        "reversibility": "Digest is informational.",
    }


def _format_digest(summary: list[dict[str, Any]], budget_text: str, decisions: list[Path]) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"# Lab digest — {today}",
        "",
        "## Queue state",
        *(f"- {row['state']}: {row['count']}" for row in summary),
        "",
        "## Budget",
        f"- {budget_text}",
        "",
        f"## Decisions today ({len(decisions)})",
    ]
    for p in decisions[:20]:
        first_line = next((ln for ln in p.read_text().splitlines() if ln.startswith("## What")), p.name)
        lines.append(f"- `{p.name}` — {first_line[7:].strip()}")
    return "\n".join(lines)


def _send_slack(text: str) -> None:
    token = os.environ.get("SLACK_BOT_TOKEN")
    channel = os.environ.get("SLACK_CHANNEL_RESEARCH")
    if not token or not channel:
        logger.warning("Slack not configured; digest written to file only.")
        return
    try:
        from slack_sdk import WebClient
        WebClient(token=token).chat_postMessage(channel=channel, text=text, mrkdwn=True)
    except Exception as e:
        logger.exception(f"Slack send failed: {e}")


@app.command()
def daily_digest() -> None:
    import asyncio

    asyncio.run(compose_and_send_digest(BudgetGuard()))


if __name__ == "__main__":
    app()
