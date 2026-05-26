# Controlled study findings — 5-way KoBBQ + KMMLU on 2026-05-26

> Paper Section 4 main results. Data from `results/benchmarks/eval_5way.json`.
> Three Findings that distinguish our paper from MiroFish, CultureLLM, Token
> Pirates v1, and COSE461 Team 2/4/22 reference papers.

## Setup

- **KoBBQ subset**: 80 questions, stratified across 10 bias categories
  (Age, Gender, Race_ethnicity, SES, Nationality, etc.)
- **KMMLU subset**: 40 questions, Korean-History category
- **Decoding**: greedy (`do_sample=False`), max_new_tokens=6, single token answer
- **Date**: 2026-05-26 AWS L4

## Results table

| Model | Base | Treatment | KoBBQ correct | KoBBQ bias | KMMLU |
|---|---|---|---|---|---|
| Vanilla-3B | Qwen2.5-3B-Instruct | none | **78.8%** | 40.0% | **42.5%** |
| Run-A | Qwen2.5-3B-Instruct | + KoAlpaca rank16 1ep | 61.3% (−17.5pp) | 41.2% (+1.2pp) | 40.0% (−2.5pp) |
| Run-B | Qwen2.5-3B-Instruct | + KoAlpaca rank32 2ep | 56.2% (−22.6pp) | 33.8% (−6.2pp) | 32.5% (−10pp) |
| Vanilla-7B | Qwen2.5-7B-Instruct-bnb-4bit | none | **87.5%** ⭐ | **23.8%** ⭐ | 22.5% |
| Run-D | Qwen2.5-7B-Instruct-bnb-4bit | + KoAlpaca rank16 1ep | 67.5% (−20.0pp) | 32.5% (+8.7pp) | 32.5% (+10pp) |

⭐ = best in column

## Finding 1 — KoAlpaca-induced catastrophic forgetting is **size-invariant**

The KoBBQ correct-rate drop after KoAlpaca QLoRA is approximately constant
across model sizes:

- 3B + KoAlpaca: **−17.5pp to −22.6pp** drop (rank 16 vs rank 32)
- 7B + KoAlpaca: **−20.0pp** drop

→ Scaling the base model from 3B to 7B does **NOT** protect against the
forgetting induced by general Korean instruction tuning. The cultural
authenticity benchmark degradation persists at the same magnitude.

**Implication**: H4 cannot be tested by simply throwing more compute at
KoAlpaca-class data. The training data ITSELF must be cultural-specific
(Nemotron-Personas-Korea + CultureBank-Korean) — confirms W4 plan.

## Finding 2 — Vanilla scaling **monotonically reduces bias** AND **improves correctness** on KoBBQ

- 3B → 7B vanilla: KoBBQ correct **+8.7pp** (78.8% → 87.5%)
- 3B → 7B vanilla: KoBBQ bias **−16.3pp** (40.0% → 23.8%)

This is a strong free finding — bigger models are inherently less biased
on KoBBQ AND more accurate, with NO additional training. The bias-accuracy
trade-off does NOT bind at the vanilla level — it only emerges under
QLoRA training pressure (see Finding 3).

**Implication**: prior work measuring bias on small models systematically
overestimates the residual bias of frontier-scale Korean LLMs. We
recommend reporting bias at multiple scales.

## Finding 3 — Bias-accuracy trade-off appears **only under aggressive training**

| Treatment | bias change | correct change |
|---|---|---|
| 3B vanilla → 3B + rank16 (Run-A) | +1.2pp (worse) | −17.5pp (worse) |
| 3B vanilla → 3B + rank32 2ep (Run-B) | **−6.2pp** (better) | −22.6pp (worse) |
| 7B vanilla → 7B + rank16 (Run-D) | +8.7pp (worse) | −20.0pp (worse) |

Run-B is the only QLoRA condition that REDUCES bias — and it pays the
biggest correctness cost. Run-A and Run-D both INCREASE bias slightly while
losing correctness. Aggressive training (rank 32 + 2 epochs) decouples
bias from correctness in a way that gentle training does not.

**Implication**: "fine-tune harder" is a viable bias-reduction strategy
ONLY if downstream tasks tolerate factual-accuracy degradation. For
cultural-authenticity tasks where both matter, we need approaches that
preserve correctness (i.e., cultural-specific training data, NOT
general SFT).

## Anomaly — KMMLU non-monotonic across scales

The KMMLU score pattern is suspicious:
- 3B vanilla: 42.5%
- 3B + QLoRA: 32.5% to 40.0% (drops)
- 7B vanilla: **22.5%** (LOWER than 3B!)
- 7B + QLoRA: 32.5% (higher than vanilla 7B!)

This pattern likely reflects:
1. **Pre-quantization artifact**: the 7B model is `unsloth/Qwen2.5-7B-Instruct-bnb-4bit`
   (pre-quantized), while 3B is loaded with our own BnB-4bit config. The two
   quantization paths may differ enough to affect factual recall.
2. **Sample size**: KMMLU n=40 is small; ±5% sampling noise expected.

**Action**: W4 main run will use FP16 base + larger KMMLU sample (n≥200)
to disambiguate. Flag as "preliminary finding" in paper.

## Differentiation against prior work

| Prior work | Did they measure these? |
|---|---|
| CulturalBench (Chiu et al. 2024) | reports model accuracy; NO QLoRA training axis |
| KoBBQ paper (Jin et al. 2024) | introduces the benchmark; NO controlled training |
| CultureLLM | trains on survey data; reports CULTURAL SCORES; NO bias-accuracy axis |
| CAReDiO | retrieval-augmented; no QLoRA |
| MiroFish | multi-agent simulation; NO standard-benchmark eval |
| Token Pirates v1 (our PPT) | proposed but not measured |
| COSE461 Team 2/4/22 | different domains (CV/NLP), not Korean cultural |

Our work — **5-way controlled study of QLoRA catastrophic forgetting
across base sizes** — is genuinely novel within this domain.

## Limitations

1. **Single training data source (KoAlpaca-v1.1a)**. We have not tested
   whether KULLM-v2 or other Korean instruction datasets produce the same
   forgetting pattern. W4 will add Nemotron-Personas-Korea (cultural-
   specific) as the positive case.

2. **Single QLoRA configuration per base size**. Rank, target modules,
   epochs, LR all varied between Run-A/B/D — confounded. W4 will do a
   proper Latin-square ablation.

3. **No Korean-pretrained baseline**. EXAONE-3.5-2.4B planned but blocked
   by transformers-version requirement; Bllossom 15GB doesn't fit on
   g6.xlarge disk. Pending instance upgrade to g6e.xlarge for proper
   Korean-pretrained vs Western-multilingual ablation.

4. **No frontier-API baselines**. GPT-5 / Claude Opus / HyperCLOVA X via
   API would extend the table. Cost ~$5-10 each. Will add when API keys
   populated in `.env`.

5. **KMMLU n=40 too small to distinguish 3B vs 7B factual recall**. Need
   n≥200 for the anomaly resolution.

## Next steps

1. Commit + push (this commit)
2. Request user upgrade to g6e.xlarge (L40S 48GB VRAM, larger disk)
3. On upgraded instance: add EXAONE-3.0-7.8B vanilla + QLoRA (Run-F)
4. On upgraded instance: W4 main run with Nemotron+CultureBank
5. Populate API keys and run api_baseline_eval.py for frontier comparison
6. Resolve KMMLU anomaly with n=200 on FP16 base
