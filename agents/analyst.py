"""Analyst agent — computes static + dynamic metrics, generates plots.

Metrics:
- Static: CAS, HAD, PDI, JSD (vs WVS Wave 7 Korea)
- Dynamic: CCR, AAS, GCS, BAS (from OASIS sim transcripts)

The Analyst is mostly deterministic Python. The Claude Agent SDK subagent is
called only when interpretation is needed (e.g., "what does this CAS=0.42 mean
qualitatively?"). Numerical computation never goes through an LLM.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from loguru import logger
from scipy.spatial.distance import jensenshannon

from orchestrator.budget import BudgetGuard
from orchestrator.queue import Task


async def handle(task: Task, compute_target: str, budget: BudgetGuard) -> dict[str, Any]:
    kind = task.payload.get("subkind", "all_metrics")
    if kind == "static_metrics":
        return await compute_static_metrics(task)
    if kind == "dynamic_metrics":
        return await compute_dynamic_metrics(task)
    if kind == "all_metrics":
        static = await compute_static_metrics(task)
        dynamic = await compute_dynamic_metrics(task)
        return {
            "summary": f"All metrics: static={len(static['artifacts'])} dynamic={len(dynamic['artifacts'])}",
            "artifacts": static["artifacts"] + dynamic["artifacts"],
            "cost_usd": 0.0,
            "reversibility": "Metrics are derived; recompute from sources to restore.",
        }
    raise ValueError(kind)


# ---------------------------------------------------------------------------
# Static metrics
# ---------------------------------------------------------------------------

async def compute_static_metrics(task: Task) -> dict[str, Any]:
    """For each (condition, backbone) cell, compute CAS, HAD, PDI, JSD."""
    out_dir = Path("results/static")
    out_dir.mkdir(parents=True, exist_ok=True)
    cells = task.payload.get("cells", [])
    rows = []
    for cell in cells:
        personas = _load_personas(cell)
        rows.append({
            "condition": cell["condition"],
            "backbone": cell["backbone"],
            "CAS": _cas(personas),
            "HAD": _had(personas),
            "PDI": _pdi(personas),
            "JSD": _jsd_vs_wvs(personas),
        })
    out_path = out_dir / "static_metrics.json"
    out_path.write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    return {
        "summary": f"Computed static metrics for {len(rows)} cells.",
        "artifacts": [str(out_path)],
        "cost_usd": 0.0,
        "reversibility": f"rm {out_path}",
    }


def _load_personas(cell: dict[str, str]) -> list[dict[str, Any]]:
    path = Path(f"results/personas/{cell['condition']}/{cell['backbone']}/personas.jsonl")
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()]


def _cas(personas: list[dict[str, Any]]) -> float:
    """Cultural Authenticity Score — LLM-judge avg (handled by separate evaluator pipeline).
    Returns NaN if evaluator scores aren't yet present."""
    scores = [p.get("evaluator_cas") for p in personas if p.get("evaluator_cas") is not None]
    return float(np.mean(scores)) if scores else float("nan")


def _had(personas: list[dict[str, Any]]) -> float:
    """Hofstede Alignment Delta — distance from Korea's known 6D vector."""
    korea_vec = np.array([60, 18, 39, 85, 100, 29])  # PDI, IDV, MAS, UAI, LTO, IVR (Hofstede)
    persona_vecs = np.array([p.get("hofstede_6d", [50] * 6) for p in personas])
    if persona_vecs.size == 0:
        return float("nan")
    return float(np.mean(np.linalg.norm(persona_vecs - korea_vec, axis=1)))


def _pdi(personas: list[dict[str, Any]]) -> float:
    """Persona Diversity Index — embedding-space variance proxy."""
    embs = np.array([p.get("embedding", []) for p in personas if p.get("embedding")])
    if embs.size == 0:
        return float("nan")
    return float(np.var(embs))


def _jsd_vs_wvs(personas: list[dict[str, Any]]) -> float:
    """Jensen-Shannon divergence vs WVS Wave 7 Korea response distribution."""
    wvs_path = Path("data/processed/wvs_korea_distribution.json")
    if not wvs_path.exists():
        return float("nan")
    wvs = np.array(json.loads(wvs_path.read_text())["distribution"])
    persona_dist = _persona_value_distribution(personas)
    return float(jensenshannon(wvs, persona_dist))


def _persona_value_distribution(personas: list[dict[str, Any]]) -> np.ndarray:
    """Quantize persona value-responses to same buckets as WVS."""
    return np.array([0.1] * 10)  # placeholder — implement in W5


# ---------------------------------------------------------------------------
# Dynamic metrics (OASIS)
# ---------------------------------------------------------------------------

async def compute_dynamic_metrics(task: Task) -> dict[str, Any]:
    out_dir = Path("results/dynamic")
    out_dir.mkdir(parents=True, exist_ok=True)
    sim_dirs = [p for p in Path("results/sims").iterdir() if p.is_dir()]
    rows = []
    for d in sim_dirs:
        transcript = d / "transcript.jsonl"
        if not transcript.exists():
            continue
        events = [json.loads(line) for line in transcript.read_text().splitlines()]
        rows.append({
            "sim_id": d.name,
            "CCR": _conformity_cascade_rate(events),
            "AAS": _authority_adoption_slope(events),
            "GCS": _group_consensus_speed(events),
            "BAS": _bas_aggregate(events),
        })
    out_path = out_dir / "dynamic_metrics.json"
    out_path.write_text(json.dumps(rows, indent=2))
    return {
        "summary": f"Computed dynamic metrics for {len(rows)} sims.",
        "artifacts": [str(out_path)],
        "cost_usd": 0.0,
        "reversibility": f"rm {out_path}",
    }


def _conformity_cascade_rate(events: list[dict[str, Any]]) -> float:
    """% of agents who changed opinion after seeing majority view."""
    return 0.0  # impl in W6


def _authority_adoption_slope(events: list[dict[str, Any]]) -> float:
    """Slope of adoption curve after influencer endorsement."""
    return 0.0


def _group_consensus_speed(events: list[dict[str, Any]]) -> float:
    """Time-to-consensus in chat-room style sims."""
    return 0.0


def _bas_aggregate(events: list[dict[str, Any]]) -> float:
    """Weighted combination of CCR/AAS/GCS calibrated to Korean ground-truth deltas."""
    return 0.0
