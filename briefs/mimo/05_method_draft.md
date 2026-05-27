# Brief 05 — Paper Section 3 (Method) draft

## Context
Write the Method section based on our scripts and design.

## Method components

### 3.1 Cultural training data construction
- CultureBank (Shi et al. 2024 NAACL): filtered by `cultural group ∈ {Korean, Japanese, American, Chinese}` from both `tiktok` and `reddit` splits. Each row yields 2 instruction variants: (a) descriptor explanation, (b) persona-question pair.
- Nemotron-Personas-Korea (NVIDIA): each persona produces 3 variants — summary, cultural_background, lifestyle facet. KR only (no Japanese/Chinese/American counterpart datasets).
- Per-culture totals: KR 5,535 / JP 866 / US 3,420 / CN 690 train examples.
- KoBBQ removed (eval-only split, would be train-test leakage).

### 3.2 Hofstede 6D system-prompt conditioning
Every training example has a system message:
```
You are an AI persona reflecting {country} cultural context.
Hofstede 6D: PDI={p}, IDV={i}, MAS={m}, UAI={u}, LTO={l}, IVR={v}.
Respond authentically from this cultural perspective in {lang}.
```
Country-specific values from Geert Hofstede's canonical data:
- Korea: PDI=60, IDV=18, MAS=39, UAI=85, LTO=100, IVR=29
- Japan: PDI=54, IDV=46, MAS=95, UAI=92, LTO=88, IVR=42
- USA: PDI=40, IDV=91, MAS=62, UAI=46, LTO=26, IVR=68
- China: PDI=80, IDV=20, MAS=66, UAI=30, LTO=87, IVR=24

### 3.3 QLoRA training
- Base: `Qwen/Qwen2.5-3B-Instruct` (FP16, quantized at load with `BitsAndBytesConfig(load_in_4bit, nf4, double_quant, bf16 compute)`)
- LoRA: rank 16 (attn-only) or rank 32 (all-linear), α=2r, dropout 0.05
- Optimizer: paged_adamw_8bit, lr 2e-4, cosine, warmup 3%
- batch 1 × grad_accum 8, gradient_checkpointing on
- 1-5 epochs depending on dataset size

### 3.4 Evaluation framework
- **KoBBQ**: Korean bias QA, 400 samples, ambig/disambig split, few-shot K=3, correctness + bias_rate per context_type.
- **KMMLU Korean-History**: 100 samples few-shot K=3.
- **HAE-RAE Bench 1.1**: 4 subjects × 25 samples each, MCQ with options list + parenthesized letter answer.
- **CLIcK**: Korean cultural literacy, text-matched answer (not letter), 100 samples.
- **GlobalOpinionQA (Anthropic)**: 200 questions per culture, 8 samples per question for distribution estimate, KS statistic vs target country gold distribution.
- **BLEnD MCQ (Lee et al. 2024)**: country-conditioned cultural common-sense, 80-100 samples per culture.

### 3.5 Cross-cultural transfer matrix
4 cultural adapters × 4 benchmark cultures = 16 cells. Off-diagonal = transfer evaluation. Reports whether cultural conditioning is reweighting (in-dist↑ + out-dist neutral) or deletion (in-dist↑ + out-dist↓).

### 3.6 Hofstede dimension ablation
Three training variants on Korean data with system prompt modified:
- `kr_idv_only`: only IDV=18 in system prompt
- `kr_uai_only`: only UAI=85
- `kr_all6d`: all 6 dimensions

Compare KS shift to determine which dimension drives cultural alignment.

### 3.7 Multi-cultural unified adapter (Run-M)
Single adapter trained on KR+JP+US+CN mix (10,511 examples) with culture token `<<culture:xx>>` prepended to each user instruction. Tests whether one model can dynamically condition on requested culture.

## Task

Write a ~1.5 page Method section (~900 words) using the above. Include:
- One LaTeX equation block for the QLoRA loss (standard PEFT formulation)
- One LaTeX equation block for the KS statistic
- Tabular description of per-culture training set sizes (5,535 / 866 / 3,420 / 690)
- Citations as placeholders `\cite{dettmers2023qlora}`, `\cite{hu2021lora}`, `\cite{shi2024culturebank}`, etc.

## Output

```markdown
# 3. Method

## 3.1 Cultural Training Data
[...]

## 3.2 Hofstede 6D System-Prompt Conditioning
[...]

[etc.]
```
