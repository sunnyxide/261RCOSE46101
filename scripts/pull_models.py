"""Pre-pull models and datasets the lab will need.

Run once after `make setup`. Idempotent — re-running skips already-cached items.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from huggingface_hub import snapshot_download
from loguru import logger

TARGETS = [
    # (repo_id, kind, local_dir, optional)
    ("nvidia/Nemotron-Personas-Korea", "dataset", "data/raw/nemotron_full", False),
    ("SALT-NLP/CultureBank", "dataset", "data/raw/culturebank_full", False),
    ("BAAI/bge-m3", "model", "models/bge-m3", False),
    ("mlx-community/Qwen3.6-27B-Instruct-4bit", "model", "models/qwen3.6-27b-mlx-q4", False),
    ("Qwen/Qwen3.6-27B-Instruct", "model", "models/qwen3.6-27b-hf", True),  # only if AWS
    ("google/gemma-4-26b-moe-it", "model", "models/gemma-4-26b-moe", True),
]


def main() -> None:
    on_aws = os.environ.get("ORBT_HOST") == "aws"
    for repo_id, kind, local_dir, optional in TARGETS:
        if optional and not on_aws:
            logger.info(f"Skipping {repo_id} (optional, host != aws)")
            continue
        Path(local_dir).mkdir(parents=True, exist_ok=True)
        try:
            logger.info(f"Pulling {repo_id} → {local_dir}")
            snapshot_download(
                repo_id=repo_id,
                local_dir=local_dir,
                local_dir_use_symlinks=False,
                token=os.environ.get("HUGGINGFACE_TOKEN"),
            )
        except Exception as e:
            logger.warning(f"Failed to pull {repo_id}: {e}")
            if not optional:
                sys.exit(1)


if __name__ == "__main__":
    main()
