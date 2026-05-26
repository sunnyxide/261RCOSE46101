# Benchmark improvement strategy — pushing KoBBQ + KMMLU scores

> Source: 5-way controlled study results 2026-05-26.
> Goal: identify concrete interventions to improve our headline numbers
> BEFORE final paper deadline. Distinguish what's worth pursuing vs noise.

## 1. Current baselines (what we measured)

| Metric | Best model | Best score | Gap vs target |
|---|---|---|---|
| KoBBQ correct | Vanilla-7B | 87.5% | PPT target: implicit; aim ≥ 90% |
| KoBBQ bias | Vanilla-7B | 23.8% | aim ≤ 15% |
| KMMLU | Vanilla-3B | 42.5% | aim ≥ 55% |
| CAS | (no eval yet) | n/a | PPT target ≥ 4.0/5.0 |
| HAD | (not computed) | n/a | PPT target RMSE ≤ 15 |
| JSD | (not computed) | n/a | PPT target ≤ 0.10 |
| PDI | (not computed) | n/a | aim > Vanilla |

## 2. Diagnostic — why Vanilla 7B beats QLoRA versions on KoBBQ

The 5-way study showed QLoRA on KoAlpaca HURTS scores. Hypothesis:
KoAlpaca's instruction distribution is dominated by general task prompts
("write a haiku", "explain quantum", etc.) that pull the model AWAY from
"answer Korean bias questions cleanly with numeric choice".

→ **the catastrophic forgetting we measured is partly OUTPUT-FORMAT
forgetting**, not just knowledge forgetting. KoAlpaca samples don't
contain "정답 번호만 출력" instructions.

## 3. Intervention catalog — ordered by expected ROI

### A. Cheap interventions (no training, only inference tweaks)

| # | Intervention | Effort | Expected ΔKoBBQ correct | Risk |
|---|---|---|---|---|
| A1 | Few-shot prompting (3 demonstrations) | 30 min | +5-15pp | low |
| A2 | Chain-of-thought "한국어로 차근차근 생각하고" prefix | 30 min | +3-10pp | low |
| A3 | Answer-format constraints (logit bias on numbers 1-3 tokens) | 1h | +2-5pp on parse rate | low |
| A4 | Multi-sample voting (5 samples, majority) | 30 min, cost ×5 | +2-5pp | low (cost) |
| A5 | Temperature=0 + greedy (already done) | 0 | — | — |

### B. Mid-effort interventions (small training)

| # | Intervention | Effort | Expected ΔKoBBQ correct | Risk |
|---|---|---|---|---|
| B1 | QLoRA on **KoBBQ training split** (instruction format match) | 2h GPU | +10-20pp | medium — overfit risk |
| B2 | QLoRA on **MIXED data** (KoAlpaca + format-aligned synthetic) | 3h GPU | +5-15pp | medium |
| B3 | DPO on Vanilla 7B with KoBBQ correct/biased pairs | 2h GPU | +5-10pp on bias rate specifically | medium |
| B4 | LoRA merge of vanilla + format-aware mini-adapter | 1h | +3-8pp | low |

### C. Big interventions (substantial training/data)

| # | Intervention | Effort | Expected ΔKoBBQ correct | Risk |
|---|---|---|---|---|
| C1 | QLoRA on **Nemotron+CultureBank-Korean** (W4 main run) | 4h GPU + data prep 2h | UNKNOWN — could be +10pp or +0pp | this is the H4 test |
| C2 | Larger base — Qwen2.5-14B + KoAlpaca | 3h GPU on g6e | +5-10pp likely (scaling) | medium — diminishing return |
| C3 | EXAONE-3.0-7.8B QLoRA (Korean pretrained) on W4 data | 4h GPU on g6e | +10-25pp possible (combo of better base + cultural data) | low |
| C4 | Self-consistency: generate K samples, vote on majority answer | 1h, cost ×K | +5-10pp typical | low |

### D. Eval-side interventions (don't change model, change eval)

| # | Intervention | Effort | Expected effect |
|---|---|---|---|
| D1 | Expand KoBBQ from 80 to 800 (10x) | re-run eval 1h | tighter CI, more reliable |
| D2 | Add KorNAT + CLIcK + HAE-RAE benchmarks | 2h coding + 1h eval | broader claim |
| D3 | Run KoBBQ on ambiguous vs disambiguated contexts SEPARATELY | 30 min | distinguish bias from accuracy |
| D4 | Per-category KoBBQ analysis (Age, Gender, Race, SES…) | 1h | shows where model fails specifically |

## 4. Recommended sequence (assumes g6e.xlarge upgrade in ~30 min)

**Phase 1 (cheap wins, on Mac or current AWS)** — TODAY
- A1: Few-shot prompt the 5 existing models — re-eval KoBBQ
- A4 / C4: Add majority voting to korean_bench_eval.py
- D3: Split KoBBQ ambiguous-vs-disambig scoring
- D4: Per-category breakdown

Expected gain: +5-15pp KoBBQ correct on vanilla models for free.

**Phase 2 (after g6e.xlarge upgrade)** — TONIGHT/TOMORROW
- C3: EXAONE-3.0-7.8B vanilla measurement (PPT-promised Korean-pretrained baseline)
- B1 + C1: W4 main run on Nemotron+CB (the H4 hypothesis test)
- C2: Qwen2.5-14B if budget allows
- D1: KoBBQ expanded to 800

**Phase 3 (analysis + reporting)** — W4-W5
- D2: KorNAT + CLIcK + HAE-RAE addition (PPT-promised)
- Combine with W3 4,800-persona corpus
- HAD + JSD computation (need WVS data)

## 5. What I expect the headline number to be

If we execute Phase 1 + 2 successfully:

| Configuration | KoBBQ correct (projected) | Confidence |
|---|---|---|
| Vanilla 7B + few-shot + majority vote | **91-93%** | high (low-risk additions) |
| Qwen14B + few-shot | 93-95% | medium |
| EXAONE-7.8B + few-shot vanilla | 88-92% | medium (Korean-pretrained may not beat scaling) |
| **EXAONE-7.8B + Nemotron+CultureBank QLoRA** | **94-97%** | **OUR HEADLINE** if H4 holds |

If H4 holds, our Korean-cultural-grounded QLoRA passes Vanilla 7B
(87.5%) by 5-10pp, validating PPT proposal claim that
"cultural-grounding > vanilla". That's a publishable headline.

## 6. What I explicitly recommend NOT doing

- **Tuning prompts to KoBBQ specifically**: overfit to benchmark, not paper claim
- **Voting K=20+**: cost-multiplier high, marginal gain tiny
- **DPO without preference data**: would need to construct preference pairs, big effort, uncertain payoff
- **Larger context windows**: not helping a 6-tok-answer benchmark

## 7. The really tricky case — KMMLU anomaly

5-way showed:
- Vanilla 3B: KMMLU 42.5%
- Vanilla 7B: KMMLU 22.5%  ← suspicious DROP
- Run-D 7B+QLoRA: KMMLU 32.5%  ← back up

Hypothesis: `unsloth/Qwen2.5-7B-Instruct-bnb-4bit` (pre-quantized) loses
factual recall relative to `Qwen/Qwen2.5-7B-Instruct` (FP16). Verification
plan:

1. On g6e.xlarge, download `Qwen/Qwen2.5-7B-Instruct` FP16 (~14GB, fits)
2. Run same KMMLU 40-Q + 200-Q expanded subset
3. If FP16 7B scores ≥ FP16 3B on KMMLU, anomaly is quantization artifact
4. If FP16 7B still < FP16 3B, the anomaly is real — needs Discussion

This is **one of the most interesting open questions** in our study right
now. Suggestion: lead Section 5 (Analysis) with this investigation.

## 8. CAS — the one number that matters most for paper

The 4 LLM-judge panel score (Tier C from EVALUATOR_FALLBACK.md):

To improve CAS we need:
1. Personas that DO sound culturally Korean (W3 main generation task)
2. Judges that reliably distinguish (panel built in `llm_judge_panel.py`)
3. Calibrated against human anchor (Tier B, requires Korea Univ evaluators)

→ **CAS improvement is a W5 task**. The W3 W4 work IS the CAS-improvement
intervention (persona generation pipeline). Reporting CAS is the LAST step
before paper finalization.

## 9. Decision points for Sunwoo

| Decision | Recommendation |
|---|---|
| Run Phase 1 cheap wins now? | YES — 90 min on Mac, no AWS dependency |
| Add KorNAT + CLIcK? | YES — fills PPT-promised benchmarks |
| Expand KoBBQ from 80 → 800? | YES — credible n |
| Investigate KMMLU anomaly on g6e? | YES — paper Section 5 lead |
| Skip BAS composite (R4 already decided) | ALREADY DECIDED |
| Pursue EXAONE-7.8B on g6e? | YES — best chance at headline number |
| Run-A/B/D retain or supersede? | RETAIN — Section 4.1 negative result is valuable |
| KoBBQ training split QLoRA (B1)? | NO — overfits benchmark, would reviewer-fail |

## 10. Concrete next executions (chronological)

1. **Now** (Mac, 30 min): few-shot prompting + majority voting added to
   `korean_bench_eval.py`; re-eval 5 models on local cache
2. **AWS upgrade ~T+30min**: bootstrap g6e.xlarge
3. **T+1h**: FP16 Qwen-7B + 200-question KMMLU on g6e (anomaly resolution)
4. **T+2h**: EXAONE-3.0-7.8B vanilla measurement + Run-F training launch
5. **T+5h**: Run-F eval, 6-way comparison commit
6. **T+24h**: W4 Nemotron+CultureBank data acquisition + W4 main run

Each step has a measurable expected ΔKoBBQ correct or ΔKMMLU. After
each step, healthcheck cron emits Slack update.
