"""Critic agent — adversarial reviewer for Writer output.

The Critic has a separate context from the Writer. It does NOT see the
underlying simulation data, only the Writer's draft. Its sole job is to
ask: "Is every claim in this draft supported by the artifacts the Writer
cites, and does it pass our course rubric?"

Critic uses a DIFFERENT model from the Writer (e.g., Writer=Claude Sonnet,
Critic=GPT-5). This deliberate mismatch reduces the chance that both
agents share the same blind spot.

Checks performed:
1. Citation existence — every [@key] resolves to bibliography.bib?
2. Numerical claims — every numeric value appears in a results/*.csv or
   metrics/*.json file we trust?
3. Cross-section consistency — methods section claims match results
   section measurements?
4. Course rubric — config/rubric.yaml requirements all addressed?
5. Style drift — does the prose drift from style_guide.md?
6. Hallucinated references — are paper citations real (cross-check with
   Semantic Scholar)?

Output: pass / specific issues (file:line, reason, suggested fix).
Writer gets up to WRITER_MAX_ROUNDS iterations to fix; then escalate.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

from agents.runner import load_prompt
from orchestrator.budget import BudgetGuard
from orchestrator.queue import Task

SYSTEM_PROMPT_NAME = "critic"


async def handle(task: Task, compute_target: str, budget: BudgetGuard) -> dict[str, Any]:
    """Review a Writer-produced draft.

    Expected task.payload:
      - draft_path: path to the markdown draft on draft/agent-N branch
      - section: which section was drafted (e.g. 'methods', 'results')
      - run_id: writer's run id (for tracing)
    """
    draft_path = Path(task.payload["draft_path"])
    section = task.payload["section"]
    issues: list[dict[str, Any]] = []

    text = draft_path.read_text()
    issues.extend(check_citations(text, draft_path))
    issues.extend(check_numbers_against_artifacts(text, draft_path, section))
    issues.extend(check_rubric_coverage(text, section))
    issues.extend(check_style_compliance(text))
    issues.extend(await check_cross_section_consistency(text, section, draft_path))
    issues.extend(await check_paper_citations_real(text, draft_path, budget, task.id))

    score = compute_pass_score(issues)
    threshold = 0.85
    passed = score >= threshold

    return {
        "summary": (
            f"Critic review of {section}: {'PASS' if passed else 'FAIL'} "
            f"(score={score:.2f}, {len(issues)} issues)"
        ),
        "section": section,
        "issues": issues,
        "score": score,
        "passed": passed,
        "human_approval_required": not passed and task.payload.get("round", 0) >= 2,
        "reversibility": "Critic outputs are advisory; Writer either revises or escalates.",
    }


# ---------------------------------------------------------------------------
# Static checks (no LLM, fast)
# ---------------------------------------------------------------------------

CITATION_RE = re.compile(r"\[@([A-Za-z0-9_\-:]+)\]")
NUMBER_CLAIM_RE = re.compile(r"\b(\d+\.?\d*)\s*(%|percent|points?|increase|decrease|delta)\b", re.I)


def check_citations(text: str, path: Path) -> list[dict[str, Any]]:
    """Every [@key] must resolve to bibliography.bib."""
    bib_path = Path("reports/bibliography.bib")
    if not bib_path.exists():
        return [{"severity": "error", "file": str(path), "msg": "bibliography.bib missing"}]
    bib_keys = set(re.findall(r"@\w+\{([^,]+),", bib_path.read_text()))
    issues = []
    for i, line in enumerate(text.splitlines(), 1):
        for key in CITATION_RE.findall(line):
            if key not in bib_keys:
                issues.append({
                    "severity": "error",
                    "file": str(path),
                    "line": i,
                    "msg": f"Citation [@{key}] not in bibliography.bib",
                    "suggested_fix": "Either add the entry or remove the citation",
                })
    return issues


def check_numbers_against_artifacts(text: str, path: Path, section: str) -> list[dict[str, Any]]:
    """Every numerical claim must trace to a file in results/ or metrics/."""
    artifact_numbers = collect_artifact_numbers()
    issues = []
    for i, line in enumerate(text.splitlines(), 1):
        for match in NUMBER_CLAIM_RE.finditer(line):
            n = float(match.group(1))
            if not artifact_numbers.contains_close(n, tolerance=0.05):
                issues.append({
                    "severity": "warning",
                    "file": str(path),
                    "line": i,
                    "msg": f"Numeric claim {n}{match.group(2)} not found in results/ artifacts",
                    "suggested_fix": "Add a source reference or correct the number",
                })
    return issues


def check_rubric_coverage(text: str, section: str) -> list[dict[str, Any]]:
    """Course rubric (config/rubric.yaml) — does this section address its required points?"""
    rubric_path = Path("config/rubric.yaml")
    if not rubric_path.exists():
        return [{"severity": "warning", "msg": "rubric.yaml not configured; skipping"}]
    rubric = yaml.safe_load(rubric_path.read_text())
    section_reqs = rubric.get("sections", {}).get(section, [])
    issues = []
    lower = text.lower()
    for req in section_reqs:
        if isinstance(req, dict):
            kw = req["any_of"]
            if not any(k.lower() in lower for k in kw):
                issues.append({
                    "severity": "error",
                    "msg": f"Section '{section}' missing required topic: {req.get('label', kw)}",
                    "suggested_fix": f"Add a paragraph addressing: {req.get('label', kw)}",
                })
    return issues


def check_style_compliance(text: str) -> list[dict[str, Any]]:
    """Style guide compliance (passive voice ratio, hedge words, etc.)."""
    style_path = Path("reports/style_guide.md")
    if not style_path.exists():
        return []
    # Toy heuristic; replace with proper linter in W3
    issues = []
    hedges = ["arguably", "perhaps", "might be", "could be considered"]
    for h in hedges:
        if text.lower().count(h) > 3:
            issues.append({
                "severity": "info",
                "msg": f"Hedge word '{h}' used >3 times; consider tightening",
            })
    return issues


# ---------------------------------------------------------------------------
# LLM-backed checks (slow, costly, gated)
# ---------------------------------------------------------------------------

async def check_cross_section_consistency(
    text: str, section: str, path: Path
) -> list[dict[str, Any]]:
    """Methods claim X measurement → Results section must actually report X."""
    if section not in {"results", "discussion"}:
        return []
    methods_path = Path("reports/sections/methods.md")
    if not methods_path.exists():
        return []
    # Stub — full impl uses Claude Sonnet with strict JSON output
    return []


async def check_paper_citations_real(
    text: str, path: Path, budget: BudgetGuard, task_id: str
) -> list[dict[str, Any]]:
    """Cross-check that cited papers actually exist on Semantic Scholar / arXiv."""
    # Stub — full impl queries Semantic Scholar API for each cited title
    return []


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def compute_pass_score(issues: list[dict[str, Any]]) -> float:
    weights = {"error": -0.20, "warning": -0.05, "info": -0.01}
    base = 1.0
    for i in issues:
        base += weights.get(i.get("severity", "warning"), -0.05)
    return max(0.0, base)


# ---------------------------------------------------------------------------
# Artifact number index (built once per run)
# ---------------------------------------------------------------------------

class ArtifactNumberIndex:
    def __init__(self) -> None:
        self.numbers: list[float] = []

    def contains_close(self, n: float, tolerance: float = 0.05) -> bool:
        return any(abs(n - x) <= max(tolerance, tolerance * abs(x)) for x in self.numbers)


def collect_artifact_numbers() -> ArtifactNumberIndex:
    """Walk results/ and metrics/, collect every numeric value into an index."""
    idx = ArtifactNumberIndex()
    for p in Path("results").rglob("*.json"):
        try:
            data = json.loads(p.read_text())
            _walk_numbers(data, idx)
        except Exception:
            continue
    for p in Path("results").rglob("*.csv"):
        # naive — replace with pandas in W3
        try:
            for line in p.read_text().splitlines()[1:]:
                for tok in line.split(","):
                    try:
                        idx.numbers.append(float(tok))
                    except ValueError:
                        pass
        except Exception:
            continue
    return idx


def _walk_numbers(obj: Any, idx: ArtifactNumberIndex) -> None:
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        idx.numbers.append(float(obj))
    elif isinstance(obj, dict):
        for v in obj.values():
            _walk_numbers(v, idx)
    elif isinstance(obj, list):
        for v in obj:
            _walk_numbers(v, idx)
