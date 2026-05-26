# 2026-05-26 — Quantization-source confound in Vanilla-7B baseline

## Status
**Open / mitigated in W4.** Surfaced by Sunwoo question (2026-05-26): "Are our vanilla models off-the-shelf or with custom pretraining/fine-tuning?"

## What was found

The "Vanilla" models reported in `decisions/2026-05-26-controlled-study-findings.md` are NOT loaded through a uniform code path:

| Label | HuggingFace source | On-disk storage | Quantizer at inference |
|---|---|---|---|
| Vanilla-3B-Qwen | `Qwen/Qwen2.5-3B-Instruct` | **FP16** (Alibaba original) | Our `BitsAndBytesConfig(load_in_4bit, nf4, double_quant, bf16 compute)` |
| Vanilla-7B-Qwen | `unsloth/Qwen2.5-7B-Instruct-bnb-4bit` | **Already bnb-4bit** (unsloth pre-quantized) | None (pre-baked) |

Both are advertised as "4-bit Qwen2.5 instruct" but the quantization **calibration source differs**:
- 3B is quantized by our code at inference time
- 7B is quantized once by unsloth and shipped that way (separate calibration corpus, separate per-channel scale stats)

## Likely consequence: the KMMLU anomaly

`results/benchmarks/eval_5way.json` reports:
- Vanilla-3B-Qwen → KMMLU Korean-History 42.5%
- Vanilla-7B-Qwen → KMMLU Korean-History **22.5%**

A 20-point drop on factual recall when going from 3B → 7B of the same instruction-tuned family is implausible from scale alone. The most likely explanation is the quantization-source mismatch hurting 7B factual recall.

## Why we ended up here

Disk pressure: g6.xlarge 48 GiB EBS sat at 86-97% full. The unsloth pre-quantized variant (~5 GiB on disk) fit; the Alibaba FP16 (~14 GiB) did not. We chose disk feasibility over experimental cleanliness without flagging it.

## Mitigation paths

| Path | Cost | Cleanliness |
|---|---|---|
| **A. Re-run Vanilla-7B-FP16** (Alibaba `Qwen/Qwen2.5-7B-Instruct` + our BnB config) | EBS resize 100GB ($5/mo) or 2nd instance | ✅ apples-to-apples with 3B |
| B. Re-run Vanilla-3B as unsloth pre-quantized | If `unsloth/Qwen2.5-3B-Instruct-bnb-4bit` exists | ✅ different direction, same cleanliness |
| C. Document as Limitation only (no re-run) | $0 | ⚠️ paper reviewers will flag |

**Decision**: Path A in W4 — Sunwoo approved 2-instance parallel + EBS resize. The cultural-QLoRA bases will all use FP16 sources + our identical BnB config, so cross-cultural shift measurements are clean.

## What gets re-reported

Section 4 in the paper currently says "Vanilla-7B Qwen 22.5% KMMLU" with no caveat. Updates:
1. Mark the 7B vs 3B KMMLU comparison as **confounded** until A is run
2. Add this confound to Limitations section even if A succeeds (transparency about how the result was originally obtained)
3. Re-run Vanilla-7B-FP16 → if new number is ≥ 3B, confound confirmed; if still anomalously low, scale-related artifact (different academic story)

## References
- `decisions/2026-05-26-controlled-study-findings.md` §Anomaly
- `scripts/multi_base_bench.py` — loader uses `prequantized` branch when base name contains `-bnb-4bit` or `4bit`
- `scripts/after_corpus.py:55-67` — same prequantized handling
