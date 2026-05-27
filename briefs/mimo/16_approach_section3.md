# Brief 16 — Section 3 "Approach" (NeurIPS template Section 3)

## Context
COSE461 final report Section 3. Template instruction: "This section details your approach(es) to the problem. For example, this is where you describe the architecture of your neural network(s), and any other key methods or algorithms. Include equations and figures. Describe baseline(s). Make original contributions clear. Cite anything not yours."

## Difference from "Method" / "Experiments"
- **Approach (Section 3)**: methodology/architecture/algorithm — what you DO
- **Experiments (Section 4)**: training details, hyperparams, data, eval setup — how you RAN it
- Don't conflate — Section 3 = theory + design; Section 4 = engineering + results

## Components to include in Approach

### 3.1 Problem formulation
Define cultural alignment task formally: given input prompt $p$, target culture $c$ (with Hofstede 6D vector $h_c$), model $M_\theta$, the goal is to make $M_\theta(p)$'s response distribution $P_M(\cdot|p)$ close to the empirical target distribution $P_c^*(\cdot|p)$ measured via large-scale multinational surveys.

Metric: KS distance $D_{KS}(P_M, P_c^*) = \sup_x |F_M(x) - F_c^*(x)|$.

### 3.2 Hofstede-Conditioned QLoRA architecture
- Base: pre-trained instruction-tuned LLM (Qwen2.5-3B/7B-Instruct)
- 4-bit quantization (NF4 + double quant, bfloat16 compute)
- LoRA adapters on attention or all-linear modules (rank 16/32, α=2r)
- System prompt encodes Hofstede 6D: $\text{sys}_c = f_\text{format}(h_c, \text{country}_c, \text{lang}_c)$
- Training: standard causal LM loss on (system, instruction, response) triples where system embeds $h_c$

### 3.3 Cultural training data
- CultureBank (Shi et al. 2024): country-filtered, 2 variants per row (descriptor + persona-question)
- Nemotron-Personas-Korea (NVIDIA): rich KR personas, 3 variants each
- Per-culture sizes: KR 5,535 / JP 866 / US 3,420 / CN 690

### 3.4 Cross-cultural alignment evaluation
For each adapter $a$ and target culture $c$, evaluate $D_{KS}(P_{M_a}, P_c^*)$ using GlobalOpinionQA. Define **in-distribution shift** as $D_{KS}(P_{M_{a=c}}, P_c^*) - D_{KS}(P_{M_\text{vanilla}}, P_c^*)$ (lower = better alignment).

### 3.5 Hofstede dimension ablation
3 variants of KR system prompt: IDV-only, UAI-only, full-6D. Compare their KS shifts to identify which dimension is necessary/sufficient for cultural alignment.

### 3.6 Multi-cultural unified adapter (Run-M)
Single adapter trained on mixed 4-culture data with `<<culture:xx>>` token prepended. Tests whether one model can dynamically condition on requested culture.

### 3.7 Baselines
1. Vanilla Qwen2.5-3B/7B-Instruct (no cultural training)
2. KoAlpaca-QLoRA on Qwen-3B (Korean instruction tuning, no Hofstede)
3. Frontier API models: GPT-5.5, Claude Opus 4.7 (as upper-bound reference for general capability, NOT culturally-conditioned)

## Task

Write **Section 3 Approach** for the NeurIPS-template paper. ~1 page (~600 words). Include:
- 2-3 numbered equations: KS distance, QLoRA loss, system-prompt formula
- 1 figure suggestion (architecture diagram placeholder with caption)
- Cite as `\cite{authoryear_short}` placeholders
- LaTeX-ready (escaped `$`, equation environments)

## Output

```markdown
# 3. Approach

## 3.1 Problem Formulation
[paragraph with equations]

## 3.2 Hofstede-Conditioned QLoRA Architecture
[paragraph with equations + figure ref]

[etc., 3.3-3.7]
```
