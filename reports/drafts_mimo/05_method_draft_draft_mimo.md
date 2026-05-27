# 3. Method

## 3.1 Cultural Training Data Construction

Our training corpus is composed of two primary sources to instill cultural knowledge and persona-driven response styles. The first source is CultureBank \cite{shi2024culturebank}, a large-scale dataset of cultural norms and values extracted from social media (TikTok and Reddit). We filtered this dataset for entries belonging to one of our four target cultural groups: Korean, Japanese, American, and Chinese. Each retained entry was used to generate two instruction-tuning examples: one for explaining the cultural descriptor itself, and another for generating responses consistent with a persona embodying that cultural trait. This provides a broad foundation of explicit cultural knowledge.

The second source is Nemotron-Personas-Korea \cite{nemotron2024}, a dataset specifically designed for the Korean context. Each synthetic persona in this dataset was expanded into three training variants: a summary persona, a detailed cultural background profile, and a lifestyle facet. This dataset enriches our model with nuanced, persona-anchored expressions of Korean culture. Notably, equivalent datasets do not exist for Japanese, Chinese, or American cultures, resulting in an asymmetric data distribution. To prevent benchmark contamination, we excluded the Korean Bias Benchmark for Question-answering (KoBBQ) \cite{ko2024kobbq} from the training set, reserving it exclusively for evaluation. The final per-culture training dataset sizes are summarized in Table 1.

**Table 1: Per-Culture Training Dataset Sizes**
| Culture | Total Examples |
| :------ | :------------: |
| Korean (KR) | 5,535 |
| Japanese (JP) | 866 |
| American (US) | 3,420 |
| Chinese (CN) | 690 |
| **Total** | **10,511** |

## 3.2 Hofstede 6D System-Prompt Conditioning

To explicitly condition the model on a high-level cultural framework, we prepend a structured system message to every training example. This message grounds the model's persona in Geert Hofstede's six cultural dimensions \cite{hofstede2010cultures}. The template is as follows:

```
You are an AI persona reflecting {country} cultural context.
Hofstede 6D: PDI={p}, IDV={i}, MAS={m}, UAI={u}, LTO={l}, IVR={v}.
Respond authentically from this cultural perspective in {lang}.
```

Here, `PDI` (Power Distance), `IDV` (Individualism), `MAS` (Masculinity), `UAI` (Uncertainty Avoidance), `LTO` (Long-Term Orientation), and `IVR` (Indulgence) are set to canonical values for each country. For example, the system prompt for Korea uses `PDI=60, IDV=18, MAS=39, UAI=85, LTO=100, IVR=29`. This forces the model to internalize and articulate responses through the lens of a specific cultural profile defined by these dimensions.

## 3.3 QLoRA Training Procedure

We perform parameter-efficient fine-tuning on a frozen base model, `Qwen/Qwen2.5-3B-Instruct` \cite{yang2024qwen2}, using QLoRA \cite{dettmers2023qlora}. The base model is loaded in a 4-bit quantized form using a `BitsAndBytesConfig` (NF4 quantization, double quantization, with BFloat16 compute dtype). We then attach Low-Rank Adaptation (LoRA) \cite{hu2021lora} adapters. We experiment with two configurations: a rank-16 adapter applied only to attention projection layers (`q_proj`, `v_proj`), and a rank-32 adapter applied to all linear layers in the transformer blocks. In both cases, we set the scaling factor `α=2r` and a dropout rate of 0.05.

The standard QLoRA loss function combines the original language modeling objective with an entropy term for the adapter weights. For a set of adapter parameters `θ_A` and frozen base model parameters `θ_B`, the objective is:

```math
\mathcal{L}(\theta_A) = -\mathbb{E}_{x \sim \mathcal{D}} \left[ \sum_{t} \log P(x_t | x_{<t}; \theta_B, \theta_A) \right] + \lambda \| \theta_A \|^2_F
```

We train using the `paged_adamw_8bit` optimizer with a learning rate of 2e-4 and a cosine learning rate schedule with a 3% warmup. We use a batch size of 1 with gradient accumulation over 8 steps and enable gradient checkpointing. The number of training epochs (1-5) is chosen based on dataset size to balance convergence and overfitting.

## 3.4 Evaluation Framework

We evaluate our models across a suite of benchmarks targeting different facets of cultural and linguistic capability.

*   **KoBBQ** \cite{ko2024kobbq}: A Korean bias QA benchmark. We use a 400-sample subset with 3-shot prompting, evaluating on both accuracy and bias rate across ambiguous and disambiguous context types.
*   **KMMLU Korean-History** \cite{lee2024kmmlu}: A 100-sample multiple-choice subset from the Korean Massive Multitask Language Understanding benchmark, used with 3-shot exemplars.
*   **HAE-RAE Bench 1.1** \cite{haerae2024}: A broader Korean evaluation covering 4 subjects (e.g., history, science) with 25 samples each. Questions are multiple-choice with options presented as a list and the answer indicated as a parenthesized letter.
*   **CLIcK** \cite{click2024}: Measures Korean cultural literacy with 100 samples. The model must generate a free-text answer that is matched for correctness, rather than selecting from lettered options.
*   **GlobalOpinionQA** \cite{anthropic2024}: From Anthropic, this provides 200 questions per culture on societal issues. We generate 8 responses per question from the model and compute the Kolmogorov-Smirnov (KS) statistic against the gold opinion distribution of the target country.
*   **BLEnD MCQ** \cite{lee2024blend}: A multiple-choice benchmark for culturally-grounded common-sense knowledge, conditioned on country. We use 80-100 samples per target culture.

## 3.5 Analysis Experiments

**Cross-Cultural Transfer Matrix.** We train four separate cultural adapters (KR, JP, US, CN) and evaluate each on the full set of four benchmark cultures. This creates a 4x4 matrix where the diagonal cells test in-distribution cultural knowledge, and the off-diagonal cells test out-of-distribution generalization or transfer. This analysis reveals whether our cultural conditioning method leads to a *reweighting* (in-distribution improvement with neutral out-of-distribution performance) or a *deletion* (in-distribution improvement at the cost of out-of-distribution degradation) effect.

**Hofstede Dimension Ablation.** To isolate the contribution of the Hofstede framework, we train three variants of the Korean adapter using only the Korean training data, but with modified system prompts:
1.  `kr_idv_only`: System prompt contains only the IDV dimension value (18).
2.  `kr_uai_only`: System prompt contains only the UAI dimension value (85).
3.  `kr_all6d`: System prompt contains all six dimension values (baseline).
We compare the KS statistic shift on the GlobalOpinionQA benchmark to determine which individual dimension most strongly drives alignment with the target Korean opinion distribution.

**Multi-Cultural Unified Adapter (Run-M).** Finally, we train a single adapter on the combined 10,511-example dataset (KR+JP+US+CN). To enable dynamic culture selection, we prepend a special token `<<culture:xx>>` (e.g., `<<culture:kr>>`) to each user instruction at inference time. This tests whether a single model can be effectively conditioned on a requested cultural perspective via a simple prompting mechanism.
