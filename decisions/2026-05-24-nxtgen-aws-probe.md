# NxtGen AWS instance probe — first SSH session

Date: 2026-05-24
Author: Claude (executing on Sunwoo's behalf)
Status: probe complete, two constraints discovered that change the plan
Instance: ku-aws @ 54.147.157.243 (NxtCloud allocated)

## What we have (confirmed via SSH probe)

| Item | Value |
|------|-------|
| OS | Ubuntu 24.04.4 LTS noble |
| GPU | NVIDIA L4, 23,034 MiB total, 22,564 MiB free, compute_cap 8.9 |
| Driver / CUDA | driver 580.126.16, CUDA 12.0 toolkit (nvcc available) |
| Python | 3.12.3 system, `/usr/bin/python3` |
| Conda | not installed |
| Root disk | 48 GB total, 28 GB free (42% used by base AMI) |
| RAM | **15 GiB only** |
| Swap | **0 B (none configured)** |
| ML stack | nothing pre-installed (no torch, no transformers, etc.) |
| Default user | `ubuntu` |
| Security group | sg-0d197adab7cb8f65c, SSH 22 + Jupyter 8888 open to 0.0.0.0/0 |
| Credits | 97.92, ~64h headroom at 1.53/hr |
| Auto-stop | 4h timer from instance start (renewable) |

## Constraints that change the plan

### C1 — 15 GB system RAM is tight for 27B-parameter QLoRA

A 27B model in 4-bit quantization needs ~13-14 GB just to hold weights in
CPU/host memory before they get streamed to GPU. Add the dataloader,
gradient buffers, optimizer state (8-bit AdamW), tokenizer cache, and
runtime Python overhead, and we're at or above 15 GB. Single OOM = hard
crash, no recovery.

Three responses ranked by safety:

1. **Pivot to smaller backbones for QLoRA.** Qwen3-7B-Instruct or
   Gemma-2-9B-it fit comfortably in 15 GB host + 23 GB GPU with significant
   headroom. The paper's H4 hypothesis (QLoRA closes ≥50% of the
   vanilla → full-stack-retrieval gap) is testable on these — the *effect*
   we want to measure is QLoRA on Korean cultural data, not absolute SOTA.
   Decision: **make Qwen3-7B the primary QLoRA target**, keep Qwen3.6-27B
   as an **inference-only** baseline via the panel + cloud API. This is
   actually scientifically cleaner — the "scaling solves culture" critique
   (H2) is rebutted more directly by showing QLoRA on a small model
   matching prompt-engineering on a big one.
2. Try Qwen3.6-27B with CPU offloading via `bitsandbytes` + `accelerate
   device_map="auto"` and pray. ~5× slower (12h → 60h), risky.
3. Drop QLoRA from the paper, keep retrieval-only conditions. Loses H4.

→ **Going with option 1.** AUTONOMOUS_INTEGRATION.md and DEVIATIONS_FROM_PPT.md
need updates to reflect this.

### C2 — Zero swap is a footgun

Even with the smaller-model pivot, a single CUDA OOM or a runaway dataset
loader can take the whole instance down. Adding 16 GB of swapfile costs
us 16 GB of the 28 GB disk but buys real safety. Net free after: ~12 GB
(still enough for model + dataset cache).

→ Adding swap as the first action this session.

### C3 — Fresh AMI means ~10 min of pip installs before any training

The base AMI is the AWS Deep Learning AMI's minimal cousin: drivers and
CUDA toolkit, but no torch / transformers / peft / bitsandbytes /
accelerate. We pay this once and snapshot the result locally so a future
session can re-bootstrap quickly if the instance is recycled.

→ Installing ML stack in a venv at `~/orbt-research-lab/.venv` on the
instance.

## What this means for `agents/shared/aws_qlora.py`

The code as written had three issues against this real environment:

1. Uses `boto3` for instance lifecycle. NxtGen exposes only a web portal
   for start/stop — no boto3 access. Refactor: instance lifecycle becomes
   **manual via portal**, `aws_qlora.py` becomes SSH-only.
2. Hardcoded `G5_2XLARGE` constant. Replace with `G6_XLARGE` (L4 24GB
   GPU, 1.53 credits/hr).
3. Hard kill at $300 USD. Replace with 75 credits (≈75% of the 97.92
   pool). Cost tracking is in NxtGen credits, not USD.

This refactor is small (~80 LOC change) and tracked as task #18.

## What does NOT change

- KPI framework (KPI_FRAMEWORK.md) — H4 wording slightly tightens to
  "QLoRA on Qwen3-7B closes ≥50% of the Vanilla → full-stack-retrieval
  gap on the same Qwen3-7B backbone", but the metric (CAS delta) and
  threshold are unchanged.
- Evaluator fallback ladder (EVALUATOR_FALLBACK.md) — unchanged.
- Risk log (decisions/2026-05-24-known-risks.md) — R1-R4 unchanged.
- W2 seed queue — unchanged.

## Action sequence executed this session

1. ✅ Probe environment (above)
2. ⏳ Add 16 GB swap (next)
3. ⏳ Install ML training stack in venv on instance
4. ⏳ Verify torch sees the L4 GPU end-to-end
5. ⏳ Update `agents/shared/aws_qlora.py` constants + boto3 → SSH refactor
6. ⏳ Snapshot the env manifest (pip freeze) into the repo for reproducibility
