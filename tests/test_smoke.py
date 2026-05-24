"""Smoke tests — fast import + pure-function checks. No network, no LLM.

These run on every CI pass. They guarantee:
- Every agent module is importable (no syntax errors, no missing deps).
- Pure functions in qa_meta produce expected outputs for fixed inputs.
- The evaluator-tier proposer matches the spec in EVALUATOR_FALLBACK.md.

If any test here fails, the lab is not safe to boot.
"""

from __future__ import annotations

import importlib

import pytest


AGENT_MODULES = [
    "agents.runner",
    "agents.data_steward",
    "agents.experiment_runner",
    "agents.analyst",
    "agents.writer",
    "agents.critic",
    "agents.librarian",
    "agents.qa_meta",
    "agents.principal_investigator",
    "agents.shared.cultural_filter",
    "agents.shared.wvs_downloader",
    "agents.shared.llm_judge_panel",
    "orchestrator.queue",
    "orchestrator.budget",
    "orchestrator.router",
    "orchestrator.scheduler",
]


@pytest.mark.parametrize("modname", AGENT_MODULES)
def test_module_imports(modname: str) -> None:
    importlib.import_module(modname)


def test_evaluator_tier_decision_tree() -> None:
    from agents.qa_meta import propose_evaluator_tier

    # Tier A — full human cohort
    state = {"evaluator_tier_state": {
        "irb": {"confirmed_evaluators": 15, "target_personas_per_evaluator": 200},
        "panel": {"icc": 0.0, "all_judges_responded": False},
    }}
    assert propose_evaluator_tier(state) == "A"

    # Tier B — small human anchor
    state["evaluator_tier_state"]["irb"]["confirmed_evaluators"] = 5
    state["evaluator_tier_state"]["irb"]["target_personas_per_evaluator"] = 50
    assert propose_evaluator_tier(state) == "B"

    # Tier C — no humans, panel healthy
    state["evaluator_tier_state"]["irb"]["confirmed_evaluators"] = 0
    state["evaluator_tier_state"]["irb"]["target_personas_per_evaluator"] = 0
    state["evaluator_tier_state"]["panel"]["icc"] = 0.6
    state["evaluator_tier_state"]["panel"]["all_judges_responded"] = True
    assert propose_evaluator_tier(state) == "C"

    # Tier D — no humans, panel disagrees
    state["evaluator_tier_state"]["panel"]["icc"] = 0.3
    assert propose_evaluator_tier(state) == "D"

    # Tier D — judge missing even with high ICC (no consensus to be had)
    state["evaluator_tier_state"]["panel"]["icc"] = 0.8
    state["evaluator_tier_state"]["panel"]["all_judges_responded"] = False
    assert propose_evaluator_tier(state) == "D"


def test_panel_icc_handles_empty_input() -> None:
    from agents.shared.llm_judge_panel import compute_panel_icc

    assert compute_panel_icc([]) == 0.0


def test_panel_icc_handles_balanced_input() -> None:
    """Synthetic case: 3 personas, 4 judges, perfect agreement → ICC ≈ 1.0.

    Uses the dataclasses directly so we don't need a real LLM.
    """
    from agents.shared.llm_judge_panel import (
        CURE_DIMENSIONS,
        JudgeRating,
        PanelRating,
        compute_panel_icc,
    )

    def make_rating(persona_id: str, scores: list[float]) -> PanelRating:
        judges = [
            JudgeRating(
                judge_id=f"judge-{i}",
                scores={dim: int(s) for dim in CURE_DIMENSIONS},
                rationale="",
                raw_usd=0.0,
            )
            for i, s in enumerate(scores)
        ]
        return PanelRating(
            persona_id=persona_id,
            judges=judges,
            mean_score=sum(scores) / len(scores),
            per_dimension={d: sum(scores) / len(scores) for d in CURE_DIMENSIONS},
            inter_judge_uncertainty=0.0,
            per_dimension_uncertainty={d: 0.0 for d in CURE_DIMENSIONS},
            total_usd=0.0,
        )

    ratings = [
        make_rating("p1", [5, 5, 5, 5]),
        make_rating("p2", [3, 3, 3, 3]),
        make_rating("p3", [1, 1, 1, 1]),
    ]
    icc = compute_panel_icc(ratings)
    # Perfect inter-judge agreement → ICC should be high (≥ 0.9).
    assert icc >= 0.9, f"Expected high ICC for perfect agreement, got {icc}"


def test_w2_plan_includes_meas_mapping_task() -> None:
    """R4 mitigation must be in the seed queue."""
    from scripts.seed_task_queue import W2_PLAN

    subkinds = [t["payload"].get("subkind") for t in W2_PLAN]
    assert "meas_to_ground_truth_mapping" in subkinds, (
        "R4 mitigation (MEAS↔ground-truth mapping) missing from W2 seed queue. "
        "See decisions/2026-05-24-known-risks.md."
    )
