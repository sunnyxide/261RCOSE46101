# Section 4: Results

## 4.1 Baselines

Vanilla off-the-shelf instruction-tuned LLMs (Qwen2.5-3B/7B, GPT-5, Claude Opus 4.7) and KoAlpaca-QLoRA fine-tunes (Run-A/B/D) on Korean cultural benchmarks.

[Insert Table 1 from results/final_results_table.md §1]


## 4.2 Cultural-QLoRA per culture

Cultural-QLoRA trained on CultureBank + Nemotron-Personas (KR) + Hofstede-conditioned instruction prompts achieves [TODO insert findings] on target-culture benchmarks.

[Insert Table 2 §2]


## 4.3 Cross-cultural alignment (main contribution)

GlobalOpinionQA KS-statistic measures how closely the model's response distribution matches the target country's empirical distribution from multinational opinion surveys. Lower = better alignment.

[Insert Table 3 §3 and Hofstede 6D shift heatmap]


## 4.4 Ablations

[Run-J: Qwen-7B FP16 vs Qwen-7B bnb-4bit — addresses quantization confound]
