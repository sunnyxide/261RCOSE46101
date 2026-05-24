"""QA Meta agent — hourly KPI monitoring and queue re-prioritization.

Reads KPI_FRAMEWORK.md, current results/, decision log, and budget state.
Produces a structured QA report at results/qa/<timestamp>.yaml and,
when severity warrants, posts to Slack and reorders the task queue.

Authority (per SELF_EVAL_LOOP.md):
- Tier 1: reorder queue priorities.
- Tier 2: propose configuration changes via decision log entry.
- NOT permitted: modify RQs, hypotheses, methodology (Tier 3 only).

The agent does not "decide" research questions — it only tracks whether
the project's stated objectives are at risk and proposes operational
remediations.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml
from anthropic import AsyncAnthropic
from loguru import logger

from agents.runner import load_prompt
from orchestrator.budget import BudgetGuard
from orchestrator.queue import Task, TaskQueue


SYSTEM_PROMPT_NAME = "qa_meta"

SEVERITY_RANK = {"green": 0, "yellow": 1, "orange": 2, "red": 3, "black": 4}


async def handle(task: Task, compute_target: str, budget: BudgetGuard) -> dict[str, Any]:
    """Run an hourly QA Meta tick.

    Steps:
    1. Aggregate current state (KPI projections, costs, queue, recent decisions).
    2. Compute risk levels per metric.
    3. Decide actions: reprioritize, propose, alert.
    4. Write report to results/qa/<timestamp>.yaml.
    5. If severity ≥ orange, send Slack message.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    out_dir = Path("results/qa")
    out_dir.mkdir(parents=True, exist_ok=True)

    state = await _aggregate_state(budget)
    risk_assessment = _assess_risk(state)
    actions_taken = await _take_actions(risk_assessment, state)

    report = {
        "tick": timestamp,
        "state": state,
        "risk": risk_assessment,
        "actions": actions_taken,
    }
    report_path = out_dir / f"{timestamp}.yaml"
    report_path.write_text(yaml.safe_dump(report, allow_unicode=True, sort_keys=False))

    overall = _overall_severity(risk_assessment)
    if SEVERITY_RANK[overall] >= SEVERITY_RANK["orange"]:
        await _alert_humans(report, overall)

    cost_usd = state.get("self_check_cost_usd", 0.0)

    return {
        "summary": (
            f"QA Meta tick {timestamp}: overall={overall}, "
            f"{len(actions_taken)} actions taken."
        ),
        "artifacts": [str(report_path)],
        "cost_usd": cost_usd,
        "overall_severity": overall,
        "human_approval_required": overall in {"red", "black"},
        "reversibility": (
            "Queue reorderings are reversible by manual priority changes; "
            "no destructive actions taken at Tier 1."
        ),
    }


# ---------------------------------------------------------------------------
# State aggregation
# ---------------------------------------------------------------------------

async def _aggregate_state(budget: BudgetGuard) -> dict[str, Any]:
    queue = TaskQueue(os.environ["ORCHESTRATOR_DB"])
    queue_summary = await queue.summary()
    budget_report = await budget.report()

    # Read latest static + dynamic metric results
    static_metrics = _read_latest("results/static/static_metrics.json")
    dynamic_metrics = _read_latest("results/dynamic/dynamic_metrics.json")

    # Evaluator-tier state (Sunwoo updates irb_status.yaml weekly)
    evaluator_tier_state = _read_evaluator_tier_state()

    # Decision log activity
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    recent_decisions = [
        p.name
        for p in Path("decisions").glob("*.md")
        if p.exists() and datetime.fromtimestamp(p.stat().st_mtime, timezone.utc) >= week_ago
    ]

    # Critic pass rate from recent results
    critic_outcomes = []
    for p in Path("results/qa").glob("*.yaml") if Path("results/qa").exists() else []:
        try:
            data = yaml.safe_load(p.read_text())
            if data and "critic_pass" in (data.get("state") or {}):
                critic_outcomes.append(data["state"]["critic_pass"])
        except Exception:
            pass

    return {
        "now": datetime.now(timezone.utc).isoformat(),
        "queue": queue_summary,
        "budget": {
            "today_usd": budget_report.today_usd,
            "week_usd": budget_report.week_usd,
            "total_usd": budget_report.total_usd,
            "daily_limit": budget_report.daily_limit,
            "weekly_limit": budget_report.weekly_limit,
            "total_limit": budget_report.total_limit,
        },
        "static_metrics": static_metrics,
        "dynamic_metrics": dynamic_metrics,
        "evaluator_tier_state": evaluator_tier_state,
        "recent_decisions_count_7d": len(recent_decisions),
        "self_check_cost_usd": 0.0,
    }


def _read_evaluator_tier_state() -> dict[str, Any]:
    """Read IRB + panel-dry-run state. Missing files are treated as zeros so
    the tier-proposal logic still runs (and proposes Tier D / C as appropriate).
    """
    irb_path = Path("data/state/irb_status.yaml")
    panel_path = Path("results/qa/judge_panel_dry_run.json")
    irb: dict[str, Any] = {}
    panel: dict[str, Any] = {}
    if irb_path.exists():
        try:
            irb = yaml.safe_load(irb_path.read_text()) or {}
        except Exception as e:
            logger.warning(f"irb_status.yaml unreadable: {e}")
    if panel_path.exists():
        try:
            panel = json.loads(panel_path.read_text())
        except Exception as e:
            logger.warning(f"judge_panel_dry_run.json unreadable: {e}")
    return {
        "irb": {
            "submitted_at": irb.get("submitted_at"),
            "approved_at": irb.get("approved_at"),
            "confirmed_evaluators": int(irb.get("confirmed_evaluators", 0) or 0),
            "target_personas_per_evaluator":
                int(irb.get("target_personas_per_evaluator", 0) or 0),
        },
        "panel": {
            "icc": float(panel.get("icc", 0.0) or 0.0),
            "all_judges_responded": bool(panel.get("all_judges_responded", False)),
            "mean_cost_per_persona_usd":
                float(panel.get("mean_cost_per_persona_usd", 0.0) or 0.0),
        },
    }


def propose_evaluator_tier(state: dict[str, Any]) -> str:
    """Pure function — apply EVALUATOR_FALLBACK.md decision tree.

    Returns one of 'A', 'B', 'C', 'D'. Pure so it's unit-testable; called
    by _assess_risk for the evaluator-tier risk band.
    """
    es = state.get("evaluator_tier_state") or {}
    irb = es.get("irb") or {}
    panel = es.get("panel") or {}
    n_evaluators = irb.get("confirmed_evaluators", 0)
    n_personas = irb.get("target_personas_per_evaluator", 0)
    if n_evaluators >= 15 and n_personas >= 200:
        return "A"
    if n_evaluators >= 5 and n_personas >= 50:
        return "B"
    if panel.get("icc", 0.0) >= 0.5 and panel.get("all_judges_responded"):
        return "C"
    return "D"


def _read_latest(path: str) -> Any:
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Risk assessment
# ---------------------------------------------------------------------------

def _assess_risk(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Apply rules from KPI_FRAMEWORK.md."""
    risks: dict[str, dict[str, Any]] = {}

    # Budget — directly from .env limits
    b = state["budget"]
    daily_pct = b["today_usd"] / max(b["daily_limit"], 1)
    risks["budget_daily"] = {
        "value": b["today_usd"],
        "target": b["daily_limit"],
        "severity": _band(daily_pct, [0.5, 0.7, 0.85, 0.95]),
        "note": f"Used ${b['today_usd']:.2f} of ${b['daily_limit']:.0f} today",
    }
    total_pct = b["total_usd"] / max(b["total_limit"], 1)
    risks["budget_total"] = {
        "value": b["total_usd"],
        "target": b["total_limit"],
        "severity": _band(total_pct, [0.4, 0.6, 0.8, 0.95]),
        "note": f"Used ${b['total_usd']:.2f} of ${b['total_limit']:.0f} total",
    }

    # Queue health — if many tasks failed or backlog growing
    queue = {row["state"]: row["count"] for row in state["queue"]}
    failed = queue.get("failed", 0)
    pending = queue.get("pending", 0)
    risks["queue_failure_count"] = {
        "value": failed,
        "target": 0,
        "severity": "green" if failed == 0 else ("yellow" if failed < 3 else "orange"),
        "note": f"{failed} failed tasks; {pending} pending",
    }

    # Evaluator-tier proposal — W4 Friday is the decision deadline. Before
    # that, lower tiers are normal; after, Tier D is red because it implies
    # the CAS headline claim has to be dropped.
    proposed_tier = propose_evaluator_tier(state)
    w4_deadline = datetime(2026, 6, 19, tzinfo=timezone.utc)  # Friday end-of-W4
    now = datetime.now(timezone.utc)
    if proposed_tier == "A":
        tier_severity = "green"
    elif proposed_tier == "B":
        tier_severity = "green" if now < w4_deadline else "yellow"
    elif proposed_tier == "C":
        tier_severity = "yellow" if now < w4_deadline else "orange"
    else:  # D
        tier_severity = "orange" if now < w4_deadline else "red"
    risks["evaluator_tier"] = {
        "value": proposed_tier,
        "target": "A or B by W4",
        "severity": tier_severity,
        "note": f"Proposed tier: {proposed_tier} (see EVALUATOR_FALLBACK.md)",
    }

    # Static metrics — only if data present
    sm = state.get("static_metrics") or []
    if isinstance(sm, list) and sm:
        full_stack = next(
            (row for row in sm if row.get("condition", "").startswith("nemotron+kg")), None
        )
        vanilla = next(
            (row for row in sm if row.get("condition", "").lower() == "vanilla"), None
        )
        if full_stack and vanilla and full_stack.get("CAS") and vanilla.get("CAS"):
            delta_cas = full_stack["CAS"] - vanilla["CAS"]
            risks["cas_delta"] = {
                "value": delta_cas,
                "target": 0.8,
                "severity": (
                    "green" if delta_cas >= 0.8
                    else "yellow" if delta_cas >= 0.4
                    else "orange" if delta_cas >= 0.0
                    else "red"
                ),
                "note": f"CAS delta full_stack vs vanilla = {delta_cas:+.2f}",
            }

    return risks


def _band(value: float, thresholds: list[float]) -> str:
    """Return severity given a usage ratio."""
    labels = ["green", "yellow", "orange", "red", "black"]
    for i, t in enumerate(thresholds):
        if value < t:
            return labels[i]
    return labels[-1]


def _overall_severity(risks: dict[str, dict[str, Any]]) -> str:
    severities = [r.get("severity", "green") for r in risks.values()]
    return max(severities, key=lambda s: SEVERITY_RANK.get(s, 0)) if severities else "green"


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

async def _take_actions(
    risks: dict[str, dict[str, Any]],
    state: dict[str, Any],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []

    # If budget is at orange, reduce parallelism by deprioritizing low-priority tasks
    if risks.get("budget_daily", {}).get("severity") in {"orange", "red"}:
        actions.append({
            "type": "queue_deprioritize_low",
            "note": "Daily budget at orange+; lowering low-priority task urgency.",
            "tier": 1,
        })

    # If queue has failures, propose root-cause analysis task (Tier 2)
    if risks.get("queue_failure_count", {}).get("severity") in {"orange", "red"}:
        actions.append({
            "type": "propose_rca",
            "note": "Propose root-cause analysis for failed tasks.",
            "tier": 2,
            "needs_human_ack": True,
        })

    # If CAS delta is not on track, propose adding a second QLoRA run with longer training
    if risks.get("cas_delta", {}).get("severity") in {"orange", "red"}:
        actions.append({
            "type": "propose_extended_qlora",
            "note": "CAS delta below target; propose extending QLoRA training.",
            "tier": 2,
            "needs_human_ack": True,
        })

    # Evaluator-tier proposal: if tier is degrading and we are within 2 weeks
    # of the W4 decision deadline, surface a Tier 2 proposal requiring human ack.
    tier_risk = risks.get("evaluator_tier", {})
    if tier_risk.get("severity") in {"orange", "red"}:
        actions.append({
            "type": "propose_evaluator_tier",
            "note": (
                f"Evaluator tier {tier_risk.get('value')} proposed. "
                f"Sunwoo: confirm in #orbt-research-lab within 24h or default applies. "
                f"See EVALUATOR_FALLBACK.md for what this commits the paper to."
            ),
            "tier": 2,
            "needs_human_ack": True,
            "deadline_hours": 24,
        })

    return actions


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

async def _alert_humans(report: dict[str, Any], severity: str) -> None:
    token = os.environ.get("SLACK_BOT_TOKEN")
    channel = (
        os.environ.get("SLACK_CHANNEL_ALERTS")
        if severity in {"red", "black"}
        else os.environ.get("SLACK_CHANNEL_RESEARCH")
    )
    if not token or not channel:
        logger.warning(f"Cannot alert humans: Slack not configured. Severity={severity}")
        return

    try:
        from slack_sdk import WebClient

        client = WebClient(token=token)
        risk_lines = [
            f"- *{name}*: {info.get('severity')} — {info.get('note', '')}"
            for name, info in report["risk"].items()
            if info.get("severity") in {"orange", "red", "black"}
        ]
        text = (
            f":warning: QA Meta — overall *{severity.upper()}*\n"
            + "\n".join(risk_lines)
            + f"\nFull report: `{report['tick']}.yaml`"
        )
        client.chat_postMessage(channel=channel, text=text, mrkdwn=True)
    except Exception as e:
        logger.exception(f"Slack alert failed: {e}")
