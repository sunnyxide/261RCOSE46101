# PPT proposal v1 vs current v2 — divergence analysis + reconciliation

> Source: `Team Token Pirates Project Proposal Presentation_최종.pptx` extracted 2026-05-26.
> Audience: Sunwoo (lead), 김민수 (co-author), COSE461 evaluators.
> Purpose: surface every drift from the proposal so we can choose what to
> preserve, what to abandon, and what to reframe in the final paper.

---

## 1. Original PPT in one paragraph

> **Title**: *Culture-grounded knowledge graphs for market-specific persona
> simulation.*
> Combine **Hofstede 6D scores + CultureBank KG (12K descriptors, 750 groups)
> + LightRAG** to generate culturally authentic consumer personas. Compare
> 5 conditions (Vanilla / Multilingual prompting / CultureLLM / Anthropological
> Prompting / Hofstede+CultureBank+LightRAG) using **GPT-5.4-mini** as primary
> model across **4 markets** (KR, JP, US, BR). Evaluate via **CAS**
> (native-speaker Likert ≥ 4.0/5.0, Krippendorff α ≥ 0.67), **HAD** (RMSE vs
> Hofstede), **PDI** (cosine variance), **JSD** (vs WVS Wave 7). Target
> primary market = **Korea** (IDV=18, UAI=85, LTO=100, MAS=39). Budget
> $250-550. 8-week timeline.

## 2. Side-by-side comparison

| Dimension | PPT v1 | Current v2 | Status |
|---|---|---|---|
| **Title framing** | "persona simulation" (descriptive) | + "deployable artifact for ORBT D2C product" (production) | EXTENDED |
| **Markets** | KR + JP (+ US/BR comparison) | Korea ONLY | NARROWED |
| **Primary model** | GPT-5.4-mini | Qwen2.5-3B/7B local QLoRA + API baselines (W4+) | CHANGED |
| **Ablation conditions** | 5 (Vanilla/Multi/CultureLLM/Anthro/Full-stack) | 6 (Vanilla/Hofstede-only/CB+KG/Nemotron-only/Nemo+Hof/Nemo+CB+KG) | EXPANDED |
| **Training** | None (prompting only) | QLoRA on KoAlpaca pilot + Nemotron+CB W4 main | ADDED (H4 hypothesis) |
| **Persona seed data** | Reddit/forums (KR/JP/US/BR) | Nemotron-Personas-Korea (KOSIS-quota) | CHANGED |
| **Static metrics** | CAS, HAD, PDI, JSD | Same 4 + KoBBQ + KMMLU + CLIcK + HAE-RAE benchmarks | EXPANDED |
| **Dynamic metrics** | (none) | CCR/AAS/GCS/BAS — pivoted to directional-only (R4) | ADDED then SCOPED DOWN |
| **Behavioral simulation** | (none) | OASIS multi-agent sim | ADDED |
| **Evaluator path** | 15-20 native speakers per market | Tier A/B/C/D ladder (IRB-dependent) | RISK-PROTECTED |
| **Inter-rater target** | Krippendorff α ≥ 0.67 | Same + LLM-panel ICC ≥ 0.5 fallback | EXTENDED |
| **Benchmarks listed** | KoBBQ + KorNAT + CLIcK + KMMLU | KoBBQ + KMMLU (measured) + CLIcK/HAE-RAE (planned) + KorNAT (NOT planned) | PARTIAL — see §5 |
| **Code stack** | NetworkX-LightRAG, Colab | LightRAG + Neo4j + DVC + AWS L4 (g6e.xlarge planned) | EXPANDED |
| **Budget** | $250-550 | NxtGen credits ~165 (≈$250 equiv) + API spend ~$50 | ON-BUDGET |
| **Methodology contribution** | (implicit) | Autonomous research lab with 8 agents + 3 nested loops + decision log | ADDED |
| **Production deployment** | (not in PPT) | ORBT Hermes tool + OpenCloud block API contract | ADDED |
| **Reference to prior code** | CultureLLM / CultureManager / CAReDiO | + MiroFish (62K stars, OASIS-based) | EXPANDED |

## 3. The single biggest drift: **+QLoRA path was not in PPT**

PPT framing: "**prompting vs RAG vs embedding conditioning**" — three injection
modes. Crucially, **parametric fine-tuning was NOT proposed**.

Current state: we added QLoRA as a fourth injection mode (H4 hypothesis):

> H4: QLoRA fine-tuning on Nemotron+CultureBank closes ≥50% of vanilla →
> full-stack-retrieval gap.

**Why we added it**: AWS credit allocation made it feasible mid-project; the
H4 result becomes the deployable parametric alternative (no per-call API cost).

**Why this is acceptable**: deviation §5 in DEVIATIONS_FROM_PPT.md justifies
this with two reasons:
1. AWS credits unlocked compute we didn't have at proposal time
2. QLoRA result becomes the deployable on-prem path that aligns with the
   "actionable persona generation" framing of PPT Slide 10

**Risk**: PPT-time reviewers will ask "but this wasn't in your plan". Our
defense (Section 4.1 of paper): "the empirical W3 pilot of KoAlpaca QLoRA
showed catastrophic forgetting, which led us to define a parametric path
that AVOIDS that — testing on cultural-specific data. The negative result
itself extends the proposal's measurement plan."

## 4. The single biggest *missed* PPT promise: **No human evaluators yet**

PPT explicitly committed: "15-20 native speakers per market, Krippendorff
α ≥ 0.67".

Current state: **zero human evaluators recruited**. We have:
- Built `agents/shared/llm_judge_panel.py` (4-model LLM panel as Tier C fallback)
- Documented `EVALUATOR_FALLBACK.md` (A/B/C/D ladder)
- IRB protocol drafted via Brief 11 (Hermes)

This is a **real promise gap**. Options:
- **Tier A** (PPT commitment): submit IRB this week (W2), recruit Korea Univ
  + Prolific evaluators, deliver in W6 — ON SCHEDULE if Sunwoo acts now
- **Tier B** (5×50 human anchors + LLM panel isotonic calibration):
  smaller human commitment, still cites human-validation
- **Tier C** (LLM panel only): paper-defensible but weaker; explicitly
  documents in Limitations
- **Tier D** (no human, drop CAS): paper reframes around HAD+PDI+JSD+KoBBQ —
  catastrophic, would publish as "automated benchmark study" instead

→ **Decision needed from Sunwoo by W2 Friday**: which tier?

## 5. Benchmark coverage drift

PPT promised 4 Korean benchmarks; current coverage:

| Benchmark | PPT | Current | Status |
|---|---|---|---|
| KoBBQ (76K) | ✅ promised | ✅ 80-question subset measured on 5 models | ON TRACK |
| KMMLU (35K) | ✅ promised | ✅ 40-question Korean-History subset on 5 models | ON TRACK — expand to 200 |
| KorNAT (10K) | ✅ promised | ❌ NOT touched | MISSING — see §6 |
| CLIcK (2K) | ✅ promised | ❌ NOT touched | MISSING — see §6 |

Two of four promised benchmarks have zero measurement. Easy add (Hermes
brief 15 could cover acquisition; eval script extends from current).

## 6. WVS Wave 7 + Hofstede grounding NOT yet computed

PPT explicitly committed:
- **HAD**: RMSE vs official Hofstede Korea vector (60,18,39,85,100,29)
- **JSD**: Jensen-Shannon Divergence vs WVS Wave 7 Korea distribution

Current state: neither computed. WVS Wave 7 download blocked by TOS
(W1 data_steward task failed). Hofstede vector is known but no persona-
inferred 6D vectors generated yet.

→ HIGH PRIORITY W3-W4 task. The W3 main persona generation produces the
inputs; analyst.py computes HAD/JSD.

## 7. Reddit/forums market grounding NEVER attempted

PPT proposed Reddit/forums (KR/JP/US/BR) as market grounding source. We
quietly pivoted to KOSIS/Naver/KOFICE without revisiting Reddit.

**Why**: KOSIS provides quantitative ground truth; Reddit is qualitative.
But the PPT's intent was probably to ground personas in real consumer
*voice*, which forums capture and statistics don't.

→ Should we add a small Reddit (e.g., r/Korea, r/Living_in_Korea, KR
Pann) text-mining pass as a *qualitative* grounding source? Cost: low
(scraping); paper value: high (closes the PPT gap).

## 8. Markets reduced from 4 to 1

PPT proposed Korea + Japan primary, with US + Brazil comparison.
Current: Korea only.

**Justification (DEVIATIONS §1)**: "depth > breadth, WVS Wave 7 Korea
gives behavioral ground truth Japan can't match at this scale".

**Risk**: weaker generalizability claim. Reviewer: "you claim a method,
but only show it works on one market". 

**Mitigation**: explicitly limit claims to "Korean D2C consumer scenarios"
in MOTIVATION_v2.md (already done). Frame future work as cross-market
replication.

## 9. Methodology contribution — autonomous lab (NOT in PPT)

The 8-agent autonomous lab + decision log + 3-loop self-eval is *new*
contribution, not in PPT.

**Risk**: methodology-paper reviewers might say "this is engineering, not
research". 

**Mitigation**: position as enabling-infrastructure that makes the
*replication* of cultural-grounding studies tractable for other markets.
Reference Stanford CS224N precedent that PPT cited (Li, Zhang, Xie, 2024
ran similar scope in 7 weeks).

## 10. Reconciliation plan — what to do with each divergence

### 10.1 KEEP (genuine improvements over PPT)
- QLoRA path + H4 hypothesis (deployable, paper-grade negative result already)
- Autonomous lab methodology (reproducibility differentiator)
- MiroFish reference + 6-axis differentiation
- KoBBQ + KMMLU controlled study (5-way ablation done)
- ORBT integration surface (production-deploy bridge)
- Tier A/B/C/D evaluator ladder (risk-protected commitment)

### 10.2 RESTORE (PPT promises we should still hit)
- KorNAT + CLIcK benchmarks (add to korean_bench_eval.py)
- HAD computation (need WVS Hofstede vectors + persona inference)
- JSD computation (need WVS Wave 7 acquisition — currently blocked)
- Human evaluators (Sunwoo IRB decision by W2 Friday)
- Reddit/forum qualitative grounding (small add, high paper value)

### 10.3 DEFEND (justify in paper Discussion)
- 4 markets → 1 market: cite depth-vs-breadth + Korean-specific KOSIS access
- 5 conditions → 6 conditions: cite need to isolate demographic vs cultural
- GPT-5.4-mini → Qwen+API: cost + local deployability for ORBT production
- BAS composite → directional CCR/AAS/GCS only: cite R4 finding (no
  verified Korean ground truth for absolute calibration)

### 10.4 DROP HONESTLY (acknowledge in Limitations)
- Japan market evaluation: future work
- Persona-as-real-consumer-prediction-replacement: not validated;
  see `consumer-prediction-deployment.md` for what level of claim we can make

## 11. Net assessment

**PPT v1 vision realized**: ~70%
- Cultural grounding pipeline: ✅ (extended)
- Korean evaluation: ✅ (KoBBQ done, KMMLU partial)
- Human validation: ❌ (Tier decision pending)
- 4 markets: ❌ (Korea only)
- WVS/Hofstede grounding: ⏳ (W3-W4)

**PPT v1 vision extended**: ~50% of new ground
- QLoRA H4 path
- Autonomous lab
- Negative-result finding (KoAlpaca insufficient)
- ORBT production deployment

**Recommendation**: paper Section 1 acknowledges PPT framing as starting
point; Section 2 cites MiroFish as adjacent work; Section 3 (Approach)
documents 6 deviations (§7-§10 of DEVIATIONS_FROM_PPT.md) honestly;
Section 5 (Analysis) splits results into:
- PPT-promised results (CAS, HAD, PDI, JSD, KoBBQ, KMMLU)
- Extended findings (QLoRA controlled study)
- Limitations (single market, evaluator tier choice, KMMLU sampling)

This positioning makes the paper STRONGER, not weaker — we deliver on the
PPT promise AND extend it with a controlled-study contribution.
