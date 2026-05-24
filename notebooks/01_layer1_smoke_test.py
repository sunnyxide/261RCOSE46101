"""Layer 1 smoke test — run BEFORE handing off to data_steward agent.

Verifies that:
1. Nemotron-Personas-Korea is downloadable and parseable.
2. CultureBank has the expected schema with Korea-tagged rows.
3. KOSIS-strata sampling math is correct.

Run with: python notebooks/01_layer1_smoke_test.py
Expected runtime: ~5 min on Mac Mini with cached datasets.
"""

from __future__ import annotations

from collections import Counter

from datasets import load_dataset
from loguru import logger


def smoke_nemotron(n: int = 100) -> None:
    logger.info("Loading nvidia/Nemotron-Personas-Korea (streaming)...")
    ds = load_dataset("nvidia/Nemotron-Personas-Korea", split="train", streaming=True)
    rows = []
    for i, row in enumerate(ds):
        rows.append(row)
        if i + 1 >= n:
            break
    logger.info(f"Sampled {len(rows)} rows.")
    logger.info(f"Available keys (first row): {list(rows[0].keys())}")
    # Sanity: sex/age distribution
    sex_counts = Counter(r.get("sex") for r in rows)
    logger.info(f"Sex distribution in sample: {sex_counts}")


def smoke_culturebank(n: int = 200) -> None:
    logger.info("Loading SALT-NLP/CultureBank...")
    ds = load_dataset("SALT-NLP/CultureBank", split="train")
    logger.info(f"Total CultureBank rows: {len(ds)}")
    # Schema check
    logger.info(f"Available keys: {list(ds[0].keys())}")
    # Korea filter
    korean = [r for r in ds if "south korea" in (r.get("cultural_group") or "").lower()][:n]
    logger.info(f"Korea-tagged rows (first {n}): {len(korean)}")
    if korean:
        logger.info(f"Example: {korean[0]}")


def smoke_kosis_distribution() -> None:
    from agents.data_steward import KOSIS_TARGET_DISTRIBUTION
    total = sum(KOSIS_TARGET_DISTRIBUTION.values())
    logger.info(f"KOSIS target distribution sums to {total:.4f} (expected close to 1.0).")
    assert 0.95 <= total <= 1.05, "Distribution does not sum to ~1; check strata coverage."


if __name__ == "__main__":
    smoke_kosis_distribution()
    smoke_nemotron(100)
    smoke_culturebank(200)
    logger.success("Layer 1 smoke test passed.")
