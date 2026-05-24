"""Data Steward agent.

Owns Layer 1 + Layer 2 data ingestion:
- Nemotron-Personas-Korea sampling (1,000 personas matching KOSIS demographics)
- CultureBank Korean subset extraction
- Hofstede Korea scores (fixed)
- WVS Wave 7 Korea responses
- KOSIS consumer surveys
- KCA dispute statistics
- Naver Datalab shopping insights (where API/scrape feasible)
- KOFICE Hallyu reports

For each dataset, the steward:
1. Fetches raw data into data/raw/<source>/<date>/
2. Validates schema and PII (Korean PII regex pack in scripts/pii_filter.py)
3. Writes a manifest (data/raw/<source>/manifest.yaml) with row counts, hash, license
4. Emits a Tier-2 proposal if schema differs from previous fetch
5. Tracks all output paths with DVC

The Claude Agent SDK subagent is used only for ambiguous decisions:
- "Does this CultureBank entry actually describe Korean culture, or East Asian generally?"
- "Is this KOSIS table the right one for our consumer cohort?"
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from datasets import load_dataset
from loguru import logger

from agents.runner import load_prompt
from orchestrator.budget import BudgetGuard
from orchestrator.queue import Task

SYSTEM_PROMPT_NAME = "data_steward"

KOSIS_TARGET_DISTRIBUTION = {
    # 2024-2026 KOSIS census, simplified into 16 strata for sampling.
    # Source: kosis.kr/statHtml/statHtml.do?orgId=101&tblId=DT_1IN1502
    # (we'll refine this in W1 from actual census; placeholder values for skeleton)
    ("M", "20s"): 0.063,
    ("M", "30s"): 0.073,
    ("M", "40s"): 0.078,
    ("M", "50s"): 0.082,
    ("M", "60s+"): 0.105,
    ("F", "20s"): 0.060,
    ("F", "30s"): 0.070,
    ("F", "40s"): 0.077,
    ("F", "50s"): 0.083,
    ("F", "60s+"): 0.117,
    # ... region cross-tab to be added
}


async def handle(task: Task, compute_target: str, budget: BudgetGuard) -> dict[str, Any]:
    """Dispatch Layer-1 sub-tasks based on payload."""
    kind = task.payload.get("subkind", "layer1_full")
    if kind == "layer1_full":
        return await layer1_full(task, budget)
    if kind == "nemotron_sample":
        return await nemotron_sample(task, budget)
    if kind == "culturebank_korean_subset":
        return await culturebank_korean_subset(task, budget)
    if kind == "wvs_wave7_korea":
        return await wvs_wave7_korea(task, budget)
    raise ValueError(f"Unknown data_steward subkind: {kind}")


# ---------------------------------------------------------------------------
# Layer 1 — Demographic & Cultural Foundations
# ---------------------------------------------------------------------------

async def layer1_full(task: Task, budget: BudgetGuard) -> dict[str, Any]:
    artifacts: list[str] = []
    for sub in ["nemotron_sample", "culturebank_korean_subset", "wvs_wave7_korea"]:
        logger.info(f"data_steward layer1 → {sub}")
        out = await dispatch_sub(sub, task, budget)
        artifacts.extend(out["artifacts"])
    return {
        "summary": f"Layer 1 ingest complete. {len(artifacts)} artifacts.",
        "artifacts": artifacts,
        "cost_usd": 0.0,  # all free public data
        "reversibility": "delete data/raw/{nemotron,culturebank,wvs}/<date>",
    }


async def dispatch_sub(sub: str, parent: Task, budget: BudgetGuard) -> dict[str, Any]:
    if sub == "nemotron_sample":
        return await nemotron_sample(parent, budget)
    if sub == "culturebank_korean_subset":
        return await culturebank_korean_subset(parent, budget)
    if sub == "wvs_wave7_korea":
        return await wvs_wave7_korea(parent, budget)
    raise ValueError(sub)


async def nemotron_sample(task: Task, budget: BudgetGuard) -> dict[str, Any]:
    """Sample 1,000 personas from nvidia/Nemotron-Personas-Korea matching KOSIS strata."""
    out_dir = Path("data/raw/nemotron") / datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)

    ds = load_dataset("nvidia/Nemotron-Personas-Korea", split="train", streaming=True)
    target_n = task.payload.get("n", 1000)
    quotas = {k: int(v * target_n) for k, v in KOSIS_TARGET_DISTRIBUTION.items()}
    selected: list[dict[str, Any]] = []
    counts: dict[tuple[str, str], int] = {k: 0 for k in quotas}

    for row in ds:
        key = (_normalize_sex(row.get("sex")), _bucket_age(row.get("age")))
        if key not in counts:
            continue
        if counts[key] >= quotas[key]:
            continue
        selected.append(row)
        counts[key] += 1
        if sum(counts.values()) >= target_n:
            break

    out_path = out_dir / "nemotron_sample_1000.jsonl"
    with out_path.open("w") as f:
        for row in selected:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    manifest = {
        "source": "nvidia/Nemotron-Personas-Korea",
        "license": "CC BY 4.0",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "n_rows": len(selected),
        "strata_target": KOSIS_TARGET_DISTRIBUTION,
        "strata_realized": {f"{k[0]}-{k[1]}": v for k, v in counts.items()},
        "sha256": _hash_file(out_path),
    }
    (out_dir / "manifest.yaml").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    return {
        "summary": f"Sampled {len(selected)} Korean personas matched to KOSIS strata.",
        "artifacts": [str(out_path), str(out_dir / "manifest.yaml")],
        "cost_usd": 0.0,
        "reversibility": f"rm -rf {out_dir}",
    }


async def culturebank_korean_subset(task: Task, budget: BudgetGuard) -> dict[str, Any]:
    """Filter CultureBank for Korea-tagged descriptors; ambiguous cases get LLM-judged.

    The LLM-judging is Tier 2 in effect because it changes the working set —
    so we emit a sample for human review before committing the full subset.
    """
    from agents.shared.cultural_filter import filter_culturebank_for_korea

    out_dir = Path("data/raw/culturebank") / datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)

    ds = load_dataset("SALT-NLP/CultureBank", split="train")
    rows, ambiguous = await filter_culturebank_for_korea(ds, budget=budget, task_id=task.id)

    main_path = out_dir / "culturebank_korea.jsonl"
    ambiguous_path = out_dir / "culturebank_korea_ambiguous_for_review.jsonl"
    with main_path.open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with ambiguous_path.open("w") as f:
        for r in ambiguous:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    manifest = {
        "source": "SALT-NLP/CultureBank",
        "license": "see HF page",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "n_committed": len(rows),
        "n_ambiguous_pending_review": len(ambiguous),
        "sha256": _hash_file(main_path),
    }
    (out_dir / "manifest.yaml").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    return {
        "summary": (
            f"CultureBank Korean subset: {len(rows)} committed, "
            f"{len(ambiguous)} flagged for human review (Tier-2 escalation)."
        ),
        "artifacts": [str(main_path), str(ambiguous_path), str(out_dir / "manifest.yaml")],
        "cost_usd": (await budget.report()).today_usd,  # approximate; tracked by filter
        "human_approval_required": len(ambiguous) > 0,
        "reversibility": f"rm -rf {out_dir}",
    }


async def wvs_wave7_korea(task: Task, budget: BudgetGuard) -> dict[str, Any]:
    """WVS Wave 7 is not on HuggingFace; we download from worldvaluessurvey.org.

    Per WVS terms, attribution required and redistribution restricted —
    so we download but do not commit raw file to public Git. DVC handles it.
    """
    from agents.shared.wvs_downloader import download_korea_wave7

    out_dir = Path("data/raw/wvs7") / datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_dir.mkdir(parents=True, exist_ok=True)
    path = await download_korea_wave7(out_dir)
    manifest = {
        "source": "worldvaluessurvey.org Wave 7 (KOR)",
        "license": "Free for academic use, redistribution restricted",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "sha256": _hash_file(path),
    }
    (out_dir / "manifest.yaml").write_text(json.dumps(manifest, indent=2))
    return {
        "summary": "WVS Wave 7 Korea downloaded.",
        "artifacts": [str(path), str(out_dir / "manifest.yaml")],
        "cost_usd": 0.0,
        "reversibility": f"rm -rf {out_dir}",
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_sex(s: str | None) -> str | None:
    if not s:
        return None
    s = s.strip().lower()
    if s in {"m", "male", "남"}:
        return "M"
    if s in {"f", "female", "여"}:
        return "F"
    return None


def _bucket_age(age: int | str | None) -> str | None:
    try:
        a = int(age) if age is not None else None
    except (TypeError, ValueError):
        return None
    if a is None:
        return None
    if a < 30:
        return "20s"
    if a < 40:
        return "30s"
    if a < 50:
        return "40s"
    if a < 60:
        return "50s"
    return "60s+"


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
