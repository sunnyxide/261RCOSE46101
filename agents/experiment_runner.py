"""Experiment Runner — launches OASIS simulations and QLoRA training jobs.

For Mac-Mini-routed tasks: orchestrates OASIS sims that call external LLM APIs.
For AWS-routed tasks: SSHes into the assigned EC2 instance, runs the job under
tmux, monitors completion, then stops the instance.

Persistence model:
- Every sim run gets an immutable directory: results/sims/<run_id>/
- Includes: config.yaml, personas.jsonl, scenario.json, transcript.jsonl, metrics.json
- Failures leave artifacts behind for debugging; never delete on failure.
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

from orchestrator.budget import BudgetGuard
from orchestrator.queue import Task


async def handle(task: Task, compute_target: str, budget: BudgetGuard) -> dict[str, Any]:
    kind = task.payload.get("subkind")
    if kind == "oasis_simulation":
        return await run_oasis(task, budget)
    if kind == "qlora_train":
        return await run_qlora(task, compute_target, budget)
    if kind == "batch_inference":
        return await run_batch_inference(task, compute_target, budget)
    raise ValueError(f"experiment_runner subkind: {kind}")


async def run_oasis(task: Task, budget: BudgetGuard) -> dict[str, Any]:
    run_id = str(uuid.uuid4())[:8]
    out_dir = Path(f"results/sims/{run_id}")
    out_dir.mkdir(parents=True, exist_ok=True)
    config = task.payload["config"]
    (out_dir / "config.yaml").write_text(json.dumps(config, indent=2))

    cmd = [
        "python", "-m", "scripts.run_oasis_sim",
        "--config", str(out_dir / "config.yaml"),
        "--output", str(out_dir),
    ]
    logger.info(f"OASIS sim {run_id}: {' '.join(cmd)}")
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        (out_dir / "stderr.log").write_bytes(stderr)
        raise RuntimeError(f"OASIS sim {run_id} failed; stderr saved.")

    metrics_path = out_dir / "metrics.json"
    summary_metrics = json.loads(metrics_path.read_text()) if metrics_path.exists() else {}

    # Estimate cost from token usage logged by the sim
    usage_path = out_dir / "usage.json"
    cost_usd = 0.0
    if usage_path.exists():
        usage = json.loads(usage_path.read_text())
        cost_usd = usage.get("estimated_cost_usd", 0.0)
        budget.record(source="openai", usd=cost_usd, task_id=task.id, agent="experiment_runner")

    return {
        "summary": f"OASIS sim {run_id} complete. {summary_metrics}",
        "artifacts": [str(p) for p in out_dir.rglob("*") if p.is_file()],
        "metrics": summary_metrics,
        "cost_usd": cost_usd,
        "reversibility": f"rm -rf {out_dir}",
    }


async def run_qlora(task: Task, compute_target: str, budget: BudgetGuard) -> dict[str, Any]:
    """SSH into AWS instance, launch unsloth QLoRA, monitor, stop instance."""
    if not compute_target.startswith("aws"):
        raise RuntimeError("QLoRA requires AWS GPU target.")
    from orchestrator.router import ResourceRouter

    router = ResourceRouter()
    router.start_aws_instance(compute_target)
    try:
        run_id = str(uuid.uuid4())[:8]
        out_dir = Path(f"results/qlora/{run_id}")
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "config.yaml").write_text(json.dumps(task.payload["config"], indent=2))
        # Real impl: pscp config + training script, run via tmux, poll logs
        # For skeleton, mark as todo
        return {
            "summary": f"QLoRA stub for {run_id}; AWS integration in scripts/launch_qlora.sh",
            "artifacts": [str(out_dir / "config.yaml")],
            "cost_usd": 0.0,
            "reversibility": f"rm -rf {out_dir}; instance auto-stopped",
        }
    finally:
        router.stop_aws_instance(compute_target)


async def run_batch_inference(task: Task, compute_target: str, budget: BudgetGuard) -> dict[str, Any]:
    """Batch persona generation for a given (condition, backbone) cell."""
    cell = task.payload["cell"]  # e.g., {'condition': 'nemotron+kg', 'backbone': 'qwen3.6-27b-q4'}
    n = task.payload.get("n", 200)
    out_dir = Path(f"results/personas/{cell['condition']}/{cell['backbone']}")
    out_dir.mkdir(parents=True, exist_ok=True)
    # Real impl: call scripts/generate_personas.py with cell args
    return {
        "summary": f"Batch persona generation: cell={cell} n={n} (stub)",
        "artifacts": [str(out_dir)],
        "cost_usd": 0.0,
        "reversibility": f"rm -rf {out_dir}",
    }
