# Brief 04 — Paper Section 1 (Introduction) draft

## Project background
COSE461 Final at Korea University (Team 8 토큰해적단). We built a system that fine-tunes small instruction-tuned LLMs (Qwen2.5-3B/7B) with QLoRA on cultural training data (CultureBank + Nemotron-Personas-Korea) using Hofstede 6D system-prompt conditioning, then measures whether the resulting model shifts toward target-culture empirical response distributions on multinational surveys.

## Key claims to motivate
1. **Off-the-shelf LLMs over-represent Anglo cultural priors** — even when prompted in Korean, they default to American-style framings.
2. **Generic Korean instruction tuning (KoAlpaca) is not enough** — it improves Korean fluency but doesn't shift cultural priors.
3. **Cultural-grounded fine-tuning with Hofstede 6D system prompts + cultural exemplars (CultureBank, Nemotron-Personas) measurably shifts model response distributions toward target culture's WVS-aligned empirical distribution** (paper's main contribution).
4. **Cross-cultural transfer matrix** shows cultural conditioning is reweighting (not deletion) — Cultural-KR doesn't lose ability to respond on US contexts, but its KS distance to KR_gold drops while distance to US_gold rises.
5. **Multi-cultural unified adapter** (one model trained on 4 cultures with `<<culture:XX>>` token) is feasible — single deployable artifact for cross-cultural applications.

## Task

Write a **1-page Introduction (~600 words)** with:

### Structure
- Opening hook (1 paragraph): the cultural-bias-in-LLMs problem, why it matters for non-Anglo applications (e.g., Korean consumer prediction, persona generation for cross-cultural products)
- Problem statement (1 paragraph): what exactly is "cultural alignment", how it's been measured (WVS, GlobalOpinionQA, BLEnD), gap in prior work
- Our approach (1 paragraph): Hofstede-conditioned QLoRA on small models, cross-cultural KS evaluation
- Contributions (bulleted, 4-5 items):
  - First demonstration of measurable KS shift on cultural-QLoRA Korean adaptation
  - Cross-cultural transfer matrix analysis (4 cultures × 4 benchmarks)
  - Hofstede dimension ablation (which dimension drives shift)
  - Multi-cultural unified adapter feasibility
  - Open-source codebase + datasets for reproducibility
- Paper outline (1 sentence per section)

### Style
- Academic but accessible
- Reference 4-6 most important prior works inline (use placeholder citations like `\cite{durmus2023global}` — don't make up bibtex)
- Explicitly note this is a **small-model study** (3B/7B) and **single-language adaptation primarily** (Korean) — set expectations honestly
- Mention COSE461 / Korea University context if relevant (Acknowledgments)

### Output

```markdown
# 1. Introduction

[Hook paragraph]

[Problem statement]

[Our approach]

## Contributions
- ...

## Paper outline
Section 2 reviews ... Section 3 ... Section 4 ... Section 5 ...
```
