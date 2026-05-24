# Baseline failures observed — Qwen2.5-3B-Instruct vanilla

Date: 2026-05-24
Status: H1 evidence — first concrete data
Source: `results/benchmarks/qwen2.5-3b-vanilla-loadtest.json`

Five Korean prompts run through Qwen2.5-3B-Instruct (4-bit NF4 quantized) on
the NxtGen L4 instance. Each prompt explicitly asks for "한국 원어민
자연스러운 표현" or warns against "영어식 번역체 / 공허한 표현".

The model fails at exactly the failure modes hypothesized in
`MOTIVATION_v2.md`. This is our first **own-experiment** evidence of the
research gap (vs cited literature like CulturalBench, KAIO).

## Concrete failure modes observed

### 1. English-translated phrasing under instruction not to use it

Prompt 1: "한국 30대 직장인 여성 페르소나를 한 문장으로 설명해줘. **영어식
번역체 말고 한국 원어민 자연스러운 표현으로.**"

Response:
> "30대의 한국 직장인 여성이시라면, 아마도 '일과 가정 사이에서 균형을 잡아야
> 하는 어려움을 겪는 중이고, 동시에 새로운 직무 기회와 **더 깊은 사랑**을
> 찾아가는 길에 서 있는 것 같아'라는 표현이 적절할 것 같습니다."

Failures:
- "**더 깊은 사랑**을 찾아가는 길에 서 있는" — direct calque of English
  "looking for deeper love", phrase that doesn't occur in Korean idiom for
  describing a working woman.
- "일과 가정 사이에서 균형을 잡아야 하는" — Western work-life-balance frame
  imposed on Korean context (Korean discourse uses different framings:
  career-vs-relationship pressure, age-norm pressure, 워킹맘 vs 비혼).
- The model literally repeats "(영어식 번역체)" pattern AFTER the
  instruction to avoid it.

### 2. Hallucinated Western-college-life cultural pattern

Prompt 2: "서울 거주 20대 대학생이 새 신용카드 결제일을 정할 때 무엇을
고민할까? **진짜 한국 대학생처럼 답해.**"

Response excerpt:
> "1. 월세 납부일... [reasonable]
>  2. **영화나 밴드 콘서트 관람일**: 학생들이 즐겨 찾는 활동 중 하나인
>     영화관람이나 밴드 콘서트 관람일을 고려합니다. 이때는 그 행사가 열리는
>     날짜를 신용카드 결제일로 설정하는 것이 일반적입니다."

Failures:
- Korean college students do NOT pick credit card cycle to match "concert
  dates". This is a hallucinated US-college-culture frame.
- Missing what an actual Korean 20대 would think about: 학자금대출 상환일,
  알바 급여일 (most students paid weekly or monthly cash), 부모 송금일.
- "밴드 콘서트" (band concert) — phrasing that doesn't match Korean college
  social vocabulary. K-pop fan would say "콘서트" without "밴드", and
  academic students would say "동아리 활동".

### 3. Reasonable answer when topic is more universal

Prompt 3: "한국 D2C 화장품 브랜드가 신제품 출시 시 고려해야 할 문화적 요소
3가지는?"

Response: actually reasonable — covers seasonality, gift-culture, 색조
preferences. This is because the cultural specificity of cosmetic marketing
is well-documented in English-language business literature the model was
trained on. **The failure surfaces specifically on prompts where the
*reasoning frame* needs to be Korean, not just the keywords.**

### 4. Performance numbers (for AWS_PERFORMANCE_PLAN.md calibration)

| Metric | Value |
|--------|-------|
| Model | Qwen/Qwen2.5-3B-Instruct (FP16 → bnb NF4 4-bit) |
| VRAM | 1.92 GiB (out of 22.03 GiB L4 budget) |
| Throughput | 14.4 tok/s avg, 14.8 tok/s steady state |
| End-to-end (5 prompts × ~180 tokens) | 117.9 seconds |
| GPU utilization | low (single-stream, no batching) — room for 16x batched throughput |

## Why this changes the plan

**Backbone choice locked: Qwen2.5-3B-Instruct as primary.** Tried 14B (disk
OOM), tried unsloth (dependency resolution failed). 3B is the largest that
both fits and trains cleanly under our constraints. The H4 hypothesis is
*relative* gap closure — 3B is sufficient.

**Inference benchmark sample size goes UP.** At 14.8 tok/s × 4h auto-stop
= 213,000 generated tokens. At ~180 tokens per persona, that's ~1,200
personas per 4h session. For 4,800-persona corpus (6 conditions × 200 ×
4 backbones), we need ~16 hours of inference = 24 credits. Fits within the
40-credit research budget.

**Update AWS_PERFORMANCE_PLAN.md** to reflect 3B as primary, drop unsloth
optimization assumption, recompute the W3 schedule with 3B QLoRA timing.

## What this evidence justifies in the paper

- §1 Introduction: cite this **own observation** alongside CulturalBench /
  KAIO as motivation. "Even with explicit anti-translation instructions,
  Qwen2.5-3B-Instruct produced English-translated Korean phrasing
  ('더 깊은 사랑') in 2/5 of our seed-prompts; this is consistent with
  CulturalBench's report that LLMs fail in the same direction (ρ > 0.97
  cross-model correlation) [chiu2024culturalbench]."
- §3 Methods: this is the *control* condition (Vanilla, no Nemotron, no
  CultureBank, no LightRAG). Subsequent conditions add cultural grounding;
  the delta is the H1 effect.
- §4 Results: include 1-2 of these baseline failures verbatim as
  illustrative examples in a "Qualitative observations" subsection.

## Reproducibility

Re-run: `ssh ku-aws` → activate venv → run the script in
`/tmp/qwen3b-baseline.log` (preserved). Inputs in
`results/benchmarks/qwen2.5-3b-vanilla-loadtest.json`. No random sampling
(`do_sample=False`), so re-runs are deterministic given the same model
checkpoint + tokenizer version.

## Re-deviation triggers

QA Meta agent re-opens the backbone choice if:

- Qwen2.5-3B QLoRA cannot reach 50% gap closure on the H4 metric
- Qwen2.5-7B becomes viable (disk freed, e.g., delete /opt/pytorch or
  request larger instance)
- A native Korean model (EXAONE-3.0-7.8B, HyperCLOVA X) becomes accessible
  at comparable inference cost
