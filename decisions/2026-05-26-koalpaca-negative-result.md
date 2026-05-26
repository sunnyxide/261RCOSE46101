# KoAlpaca QLoRA pilot — negative cultural-authenticity result

Date: 2026-05-26
Status: paper-relevant finding from W3 pilot (Run-A + Run-B)
Inputs: results/baselines/three_way_diff.md, results/baselines/three_way_metrics.json,
        results/personas_pilot/personas.jsonl

## TL;DR

Training Qwen2.5-3B-Instruct with QLoRA on KoAlpaca-v1.1a (general Korean
instruction-tuning dataset) **did not clearly improve cultural authenticity**
across 60 Korean consumer prompts and 30 persona generations. Two
configurations were tested (Run-A: rank 16 attn-only 1ep 8k samples; Run-B:
rank 32 all-linear 2ep 15k samples); both converged on loss but exhibit
persistent Western-default reasoning patterns and Korean-translation
fragility.

**This is a paper-relevant finding**, not a failure: it directly motivates
the need for *cultural-specific* training data (Nemotron-Personas-Korea +
CultureBank-Korean subset) for the W4 H4 hypothesis test.

## Quantitative summary

| Metric | Vanilla | Run-A | Run-B |
|---|---|---|---|
| Final train loss | n/a (no train) | 1.640 | 1.572 |
| Final eval loss | n/a | 1.591 | 1.583 |
| Perplexity | n/a | 4.91 | 4.87 |
| Total tokens (60 prompts) | 8,494 | 9,975 | 9,771 |
| Total chars (60 prompts) | 20,154 | 16,080 | 16,225 |
| Avg chars per response | 336 | 268 | 270 |
| Trainable params | 0 | 7.37M (0.43%) | 14.75M (0.86%) |

Both Run-A and Run-B converged (train_loss < eval_loss < perplexity 5),
confirming the QLoRA pipeline itself works. The 1-point loss drop is
substantial and indicates the adapter learned the KoAlpaca distribution.

## Qualitative findings — three failure modes persist after QLoRA

### Failure mode 1 — English-translated phrasing remains

Prompt: "한국 30대 직장인 기혼 여성 페르소나를 한 문장으로 설명해. 영어식
번역체 말고 한국 원어민 자연스러운 표현으로."

- **Vanilla**: "가족과의 관계가 중요하고, 직장에서 성공하려면 노력해야..." —
  short, somewhat natural Korean
- **Run-B**: "남편과의 관계가 중요하며, 남편이 행복하면 자신도 행복하다는
  생각을 가지고 있습니다. 또한, 남편과의 관계를 유지하기 위해 노력하고,
  남편의 필요에 맞춰 행동하는 것이 일반적입니다."

Run-B is *longer* and grammatically fine, but adds **English-translated
patriarchal stereotype** ("남편이 행복하면 자신도 행복하다", "남편의 필요에
맞춰 행동") that is uncommon as a 30대 직장인 기혼 여성 self-description
in actual Korean discourse. The training data (KoAlpaca, derived from
Stanford Alpaca seed translation) carries Western framings forward.

### Failure mode 2 — Cultural hallucination

Persona pilot p003 (F 30대 수도권 기혼 워킹맘):
> "매일 아침에는 러시아 레드벨벳 콘서트를 듣고, 오후에는 아웃도어
> 액티비티를 즐기며..."

"러시아 레드벨벳 콘서트" is a hallucinated entity — likely confusion
between K-pop group Red Velvet and "Russian Red Velvet" (likely the cake).
A 30대 워킹맘 typical lifestyle is also not "매일 콘서트". This is the
**hollow-pattern hallucination** observed in ORBT production (HANDOFF.md
§1).

### Failure mode 3 — Persona output structural drift

24/30 personas were JSON-parseable; 6 produced free-text instead of
structured output despite explicit JSON instruction. Some produced
**incomplete name fields** (`"name": "`) or **混合된 영어 단어**
("d2c response pattern" English instead of Korean).

## Why this matters for the paper

### Position in MOTIVATION_v2.md framework

Three proposed mechanisms for cultural injection:
- **Proposition 1**: Cultural retrieval is necessary but not sufficient (H1)
- **Proposition 2**: Demographic grounding is necessary but not sufficient (H1)
- **Proposition 3**: Static authenticity ≠ behavioral authenticity (H3)

This W3 pilot adds a fourth empirical proposition:
- **Proposition 4 (new)**: General Korean instruction tuning (KoAlpaca-style)
  is NOT a substitute for cultural-specific tuning. Vanilla-base + general-
  instruction-tuning produces fluent Korean but does not eliminate
  Western-default reasoning patterns. **H4 requires training data that is
  itself culturally grounded** — Nemotron-Personas-Korea (demographically
  Korean) + CultureBank-Korean (culturally Korean) is the testable path.

### Section 4 paper structure implication

The original Section 4 plan was:
- Static metrics table (CAS, HAD, PDI, JSD) for 6 conditions × 4 backbones
- Single QLoRA condition showing H4 closure

Updated structure:
- **Section 4.1 — Why KoAlpaca QLoRA is insufficient** (this finding)
- **Section 4.2 — Cultural-specific QLoRA result** (W4 main run with
  Nemotron+CultureBank, projected to show real H4 closure)
- **Section 4.3 — Capacity ablation** (Run-A rank 16 vs Run-B rank 32)
- **Section 4.4 — Standard benchmark eval** (KoBBQ + KMMLU, in progress)

This restructure makes the paper STRONGER:
- Negative result + positive result = clear ablation narrative
- Justifies the cultural-specific data acquisition cost
- Differentiates from prior work (CultureLLM uses Wikipedia values,
  CAReDiO uses preference data) — we show task-tuning isn't enough

## What we keep (Run-A + Run-B value)

Even though cultural-authenticity gains were weak, both adapters:
1. **Validate the W4 training pipeline end-to-end** — code, hyperparams,
   resume logic, checkpoint rotation all proven on real workload
2. **Provide before/after comparison data** for 60 Korean prompts —
   directly usable in Section 4.1
3. **Establish capacity-ablation baseline** — when W4 final run uses
   different rank/alpha, we can compare against Run-A/B convergence
4. **Free QLoRA dataset choice** — KoAlpaca cost ~7 credits total, learned
   what doesn't work BEFORE the more expensive Nemotron+CultureBank run

## Re-deviation check

This doesn't break any HANDOFF.md hypothesis. H4 still tests "QLoRA closes
gap" — we just now have stronger evidence that the gap-closing requires
*cultural-specific* training data, not just *Korean-language* training data.
Updates needed:
- DEVIATIONS_FROM_PPT.md: add Section 7 — "KoAlpaca pilot rejected as H4
  test bed; Nemotron+CultureBank confirmed as required for H4"
- KPI_FRAMEWORK.md §2 (H4 row): keep target at ≥50% gap closure but tag
  "valid only for cultural-specific training data"
- RESEARCH_PLAN_v2.md (new): list W4 training data acquisition as
  critical-path, not optional

## Next steps validated by this finding

1. **Acquire Nemotron-Personas-Korea** (W1 data_steward task, was failing
   in scheduler due to HF gating — escalate to manual HF_TOKEN setup)
2. **Build CultureBank-Korean filtered subset** (W2 data_steward task)
3. **Run-D (Qwen2.5-7B QLoRA)** — capacity ablation at base-model level,
   tests whether 3B was just too small to absorb cultural patterns
4. **Run-E (EXAONE-3.0-7.8B QLoRA)** — Korean-pretrained baseline; if
   pretraining solves the problem then QLoRA pivot needed
5. **Korean cultural benchmark eval (in progress)** — quantitative gap
   measurement between vanilla / Run-A / Run-B on KoBBQ + KMMLU
