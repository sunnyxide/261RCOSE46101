# 2026-05-26 — Phase 1 extended eval results: revised findings

## What changed

Phase 1 evaluation (few-shot K=3, n=400 KoBBQ with ambig/disambig split, n=100 KMMLU) completed at 2026-05-26 09:07 UTC on AWS-A. Results contradict portions of `decisions/2026-05-26-controlled-study-findings.md` and `decisions/2026-05-26-koalpaca-negative-result.md`.

## Headline numbers

| Model | KoBBQ corr | KoBBQ bias | Ambig corr | Disambig corr | KMMLU | HAE-RAE |
|---|---|---|---|---|---|---|
| Vanilla-3B-Qwen | 0.660 | 0.438 | 0.475 | 0.849 | 0.300 | 0.000 |
| Run-A-3B + KoAlpaca rank16 attn | 0.680 | 0.407 | 0.535 | 0.828 | 0.270 | 0.000 |
| Run-B-3B + KoAlpaca rank32 alllinear | 0.640 | 0.378 | 0.564 | 0.717 | 0.330 | 0.000 |
| Vanilla-7B-Qwen | 0.780 | 0.355 | 0.738 | 0.823 | 0.320 | 0.000 |
| **Run-D-7B + KoAlpaca** | 0.738 | **0.312** | **0.782** | 0.692 | 0.290 | 0.000 |

Bias score range: 0.0 = no stereotype reinforcement, 1.0 = all wrong answers match stereotype.

## Finding 1 (revised): KoAlpaca QLoRA REDUCES stereotype reinforcement on KoBBQ

Direction reversed from earlier doc:
- Vanilla-3B bias 0.438 → Run-B 0.378 (-6.0pt)
- Vanilla-7B bias 0.355 → Run-D 0.312 (-4.3pt)

This holds across both 3B and 7B bases. KoAlpaca instruction-following data, despite being culturally-generic translated content, produces measurable bias reduction. Earlier "catastrophic forgetting" claim was an artifact of zero-shot KoBBQ scoring (the loader bug returning 0s).

## Finding 2 (new): Ambig/Disambig trade-off is the real story

The aggregate KoBBQ score (correctness) masks two opposite movements:

| | Vanilla-7B | Run-D-7B+KoAlpaca | Δ |
|---|---|---|---|
| Ambig context (correct answer is "unknown") — correct rate | 0.738 | **0.782** | **+4.4pt** |
| Ambig context — bias rate | 0.249 (computed) | 0.158 | **-9.1pt** |
| Disambig context (factually-clear) — correct rate | 0.823 | **0.692** | **-13.1pt** |
| Disambig context — bias rate | 0.462 | 0.470 | flat |

**Interpretation**: KoAlpaca QLoRA pushes the model to be MORE willing to say "I don't know" when context is genuinely ambiguous (good calibration), at the cost of slightly hedging on factually-clear questions (over-conservative). This is a meaningful, publishable behavioral trade-off — not just "training hurts everything."

The same direction holds for 3B (Vanilla-3B ambig 0.475 → Run-B 0.564, +8.9pt) but is less pronounced.

## Finding 3 (revised): KMMLU 7B-vs-3B anomaly was zero-shot calibration, not quantization

Earlier observation: zero-shot KMMLU Vanilla-7B 22.5% < Vanilla-3B 42.5%. With few-shot K=3:
- Vanilla-3B → 30.0%
- Vanilla-7B → 32.0%

The 20-point gap vanished. The quantization-source mismatch (`unsloth/Qwen2.5-7B-Instruct-bnb-4bit` vs Alibaba FP16) is real and worth documenting (see `decisions/2026-05-26-quantization-confound.md`), but it is not the explanation for the original anomaly. The original anomaly was the model's inability to extract the answer letter under zero-shot conditions.

**Action**: keep quantization-confound doc as Limitations content (transparency), but don't claim it caused the anomaly.

## Finding 4 (outstanding): HAE-RAE and CLIcK loaders still broken

- HAE-RAE: 100 examples loaded across 4 subjects, 12-24 unparsed per model, accuracy 0.0 across all models.
- CLIcK: 0 examples loaded.

Likely an answer-letter parsing or loader-schema issue. Until fixed, these benchmarks contribute nothing to the comparison. Hermes brief 09 should produce a fix.

## Implications for W4 cultural-QLoRA design

1. **KoAlpaca-QLoRA is now the reference baseline, not the failed attempt**. Cultural-QLoRA must beat KoAlpaca on KoBBQ bias AND maintain disambig correctness (i.e., avoid the over-conservative hedge).
2. The ambig calibration metric (correct rate on ambiguous contexts) becomes a primary figure in the paper. Cultural-QLoRA should match or exceed Run-D's 0.782 ambig.
3. WVS distribution alignment becomes the main differentiator: KoAlpaca-QLoRA likely doesn't shift WVS responses much (generic data), Cultural-QLoRA should produce measurable shift toward Korean WVS-7 cohort distributions. This is the unique contribution.

## Required updates to prior docs

- `decisions/2026-05-26-koalpaca-negative-result.md` — supersede; the "negative result" framing was based on the zero-shot scoring bug
- `decisions/2026-05-26-controlled-study-findings.md` — replace findings 1-3 with this doc
- `reports/paper/sections/04_results.tex` (when written) — use these numbers
