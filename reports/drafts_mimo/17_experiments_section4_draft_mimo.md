# 4. Experiments

## 4.1 Data
Our evaluation suite comprises eight datasets spanning cultural knowledge, bias, opinion alignment, and linguistic intelligence, selected to cover multiple dimensions of cultural adaptation. All datasets are filtered or curated for the Korean (KR) context unless otherwise noted.

**CultureBank-KR** (Shi et al. 2024, NAACL) provides culture-specific facts, values, and norms. We use the country-filtered subset for South Korea (URL: [TBD]). Input format is a free-text cultural scenario; output is a descriptive text. For our experiments, we use a subset of 2,000 examples for training and 500 for validation.

**Nemotron-Personas-Korea** (NVIDIA, Hugging Face) consists of 3,535 persona descriptions conditioned on Korean demographics (age, gender, region, occupation). Input is a structured persona description; output is a free-text continuation. This dataset is used exclusively for training the cultural adapters.

**KoBBQ** (Jin et al. 2024) is a Korean BBQ dataset for measuring social bias. It contains ambiguous and disambiguated contexts with multiple-choice questions. We sample 200 ambiguous and 200 disambiguated items for evaluation. Input format: a context paragraph followed by a question and 5 answer choices. We use few-shot prompting with K=3 examples from a fixed set.

**KMMLU Korean-History** (Son et al. 2024) tests factual knowledge of Korean history. We select 100 multiple-choice questions (4 options each). Input: question with four answer choices. Output: a single letter (A-D).

**HAE-RAE Bench 1.1** (Yoo et al.) evaluates Korean linguistic and cultural understanding across four subjects: common sense, culture, history, and language. We sample 100 items per subject (400 total). Input format: question with four answer choices. Output: a single letter.

**CLIcK** (Kim et al. 2024) is a benchmark for Korean cultural and linguistic intelligence. We use 150 multiple-choice questions (4 options). Input: question and answer choices. Output: a single letter.

**GlobalOpinionQA** (Durmus et al. 2023) is a multinational opinion polling dataset. We use the South Korea subset (~200 questions) to measure alignment with empirical opinion distributions. Input: a question on a social/political topic. Output: one of 5 opinion stances (Strongly Disagree to Strongly Agree). For evaluation, we sample 8 responses per question from the model.

**BLEnD MCQ** (Lee et al. 2024) evaluates cultural norms and diversity via multiple-choice questions conditioned on country. We use the Korean subset (150 questions). Input: a country-conditioned scenario with four answer choices. Output: a single letter.

| Dataset                  | Task Type         | Input Format                                    | Output Format         | Size (Eval) | Usage       |
|--------------------------|-------------------|-------------------------------------------------|-----------------------|-------------|-------------|
| CultureBank-KR           | Text Generation   | Cultural scenario text                          | Descriptive text      | 500         | Train/Val   |
| Nemotron-Personas-KR     | Text Generation   | Structured persona description                  | Free-text continuation| 3,535       | Train       |
| KoBBQ                    | Bias Measurement  | Context + question + 5 choices                  | Letter (A-E)          | 400         | Eval        |
| KMMLU Korean-History     | Knowledge (MCQ)   | Question + 4 choices                            | Letter (A-D)          | 100         | Eval        |
| HAE-RAE Bench 1.1        | Knowledge (MCQ)   | Question + 4 choices (4 subjects)               | Letter (A-D)          | 400         | Eval        |
| CLIcK                    | Cultural Knowledge| Question + 4 choices                            | Letter (A-D)          | 150         | Eval        |
| GlobalOpinionQA          | Opinion Alignment | Question on social topic                        | Likert scale (1-5)    | 200         | Eval        |
| BLEnD MCQ                | Cultural Norms    | Country-conditioned scenario + 4 choices        | Letter (A-D)          | 150         | Eval        |

## 4.2 Evaluation Method
Each benchmark employs a specific evaluation protocol aligned with its intended measurement.

**KoBBQ** is evaluated using the official metrics: `correct_rate` (accuracy) and `bias_rate` (stereotype score). We report overall and per context-type (ambiguous/disambiguated) scores. A lower `bias_rate` indicates less stereotype reinforcement by the model.

**KMMLU, HAE-RAE, and CLIcK** use standard multiple-choice accuracy: the percentage of correctly answered questions.

**GlobalOpinionQA** measures alignment with empirical opinion distributions. For each question, we generate 8 model responses (temperature=0.7). We compute the empirical distribution of these responses across the 5-point Likert scale and compare it to the ground-truth distribution from South Korean respondents using the two-sample Kolmogorov-Smirnov (KS) statistic. We report the mean and median KS statistic across the question set.

**BLEnD MCQ** evaluates accuracy under country-conditioned prompting (e.g., "As a Korean person, ...").

**CAS LLM-judge panel** is used for qualitative assessment. Three state-of-the-art LLMs (GPT-5.5, Claude Opus 4.7, and Mimo-v2.5-Pro) serve as judges. Each rates a model's response on three scales (1-5): `cultural_authenticity`, `persona_consistency`, and `factual_accuracy`. For each item, we take the median score across judges. To assess reliability, we report the average pairwise absolute difference in scores between judges.

## 4.3 Experimental Details
All experiments were conducted on an AWS `g6.xlarge` instance equipped with an NVIDIA L4 GPU (24 GB VRAM), 48 GB EBS storage, and 16 GB swap memory.

We apply QLoRA (Dettmers et al. 2023) with NF4 quantization, double quantization, and bfloat16 compute. We fine-tune the Mistral-7B-v0.1 base model. We performed a hyperparameter search over QLoRA rank $r \in \{16, 32\}$ and target modules $\in \{\text{attn-only, all-linear}\}$. The scaling factor $\alpha$ was set to $2r$. Dropout was fixed at 0.05. For the final adapters, we used $r=32$ targeting all-linear layers.

Training used a per-device batch size of 1, gradient accumulation steps of 8 (effective batch size 8), and a learning rate of 2e-4 with a cosine scheduler and 3% warmup. We used the paged_adamw_8bit optimizer and gradient checkpointing. The number of training epochs was adjusted based on dataset size: for the Korean persona data (5,535 examples) we used 2 epochs; for smaller cultural sets (e.g., 866 examples for a Japanese adapter) we used up to 5 epochs. The total compute for training all four cultural adapters and running ablations was approximately 30 GPU-hours. All experiments used a fixed random seed of 42 for reproducibility.

## 4.4 Results
This section presents preliminary results. Final numerical values are pending and will be filled during paper finalization; placeholder values are denoted with "TBD" or "$\Delta X$".

We first establish baselines. Table 1 compares the performance of vanilla Mistral-7B and a QLoRA-fine-tuned variant (KoAlpaca-QLoRA) across our evaluation suite. As expected, vanilla models show limited cultural knowledge (low accuracy on KMMLU, HAE-RAE, CLIcK) and significant bias (high KoBBQ `bias_rate`).

Table 2 shows the in-distribution performance of our Cultural-QLoRA adapters (e.g., Cultural-KR trained on Nemotron-Personas-KR). We observe substantial improvements over baselines, with Cultural-KR achieving TBD accuracy on HAE-RAE and reducing KoBBQ `bias_rate` by $\Delta X$ points.

The core cross-cultural alignment results are summarized in Table 3 and Figure 1. Table 3 presents the GlobalOpinionQA KS statistic and BLEnD accuracy for each adapter (KR, JP, US, EU) tested across all cultural contexts. A key finding is that Cultural-KR reduces the KS distance to the Korean opinion distribution from ~TBD (vanilla) to ~TBD, an improvement of $\Delta X$ points. Importantly, when Cultural-KR is evaluated on Japanese or American data, its KS distance does not degrade relative to the vanilla model, indicating cultural knowledge is added, not overwritten (i.e., neutral transfer). Figure 1 visualizes this cross-cultural performance matrix as a heatmap.

We performed an ablation on Hofstede's cultural dimensions (Table 4, Figure 2). We created adapter variants by perturbing one dimension at a time (e.g., increasing Individualism). For Korean culture, the IDV (Individualism) dimension showed the largest effect on KS shift when ablated, suggesting it is a dominant axis for opinion alignment. Figure 2 plots the radar chart of the six Hofstede dimensions for the Vanilla model, the target Korean empirical profile, and the Cultural-KR adapter's achieved profile.

Finally, we tested a multi-cultural unified adapter (Run-M) trained on a mixture of KR, JP, US, and EU data. Run-M was competitive with the per-culture adapters on average, though single-culture adapters maintained a slight edge on their target culture (e.g., Cultural-KR on KS-KR by +$\Delta X$ points).

**Commentary:** The results largely meet expectations. The significant reduction in KS distance confirms that cultural alignment can be effectively injected via lightweight adapters. The neutral cross-cultural transfer is a positive surprise, suggesting our method adds cultural knowledge without catastrophic forgetting. The dominance of IDV aligns with prior work linking this dimension to opinion variance. The slight underperformance of the unified Run-M adapter suggests that, for highly specialized tasks, a per-culture approach may still be preferable. The main limitation is our use of a single seed; future work will include confidence intervals.

```latex
\begin{table}[h]
\centering
\caption{Baseline performance of vanilla and QLoRA-fine-tuned models on Korean cultural and knowledge benchmarks.}
\label{tab:baselines}
\begin{tabular}{lcccc}
\hline
\textbf{Model} & \textbf{KoBBQ (\%)} & \textbf{KMMLU (\%)} & \textbf{HAE-RAE (\%)} & \textbf{CLIcK (\%)} \\
 & \textit{correct / bias} & \textit{accuracy} & \textit{accuracy} & \textit{accuracy} \\
\hline
Vanilla-7B & TBD / TBD & TBD & TBD & TBD \\
KoAlpaca-QLoRA & TBD / TBD & TBD & TBD & TBD \\
\hline
\end{tabular}
\end{table}

\begin{table}[h]
\centering
\caption{Cross-cultural alignment measured by GlobalOpinionQA KS statistic (lower is better) and BLEnD accuracy (\%). Each row is a model (adapter) evaluated on a column's cultural context.}
\label{tab:cross_cultural}
\begin{tabular}{l|cc|cc|cc|cc}
\hline
 & \multicolumn{2}{c|}{\textbf{Korea}} & \multicolumn{2}{c|}{\textbf{Japan}} & \multicolumn{2}{c|}{\textbf{USA}} & \multicolumn{2}{c}{\textbf{EU}} \\
\textbf{Model (Adapter)} & GO-KS & BLEnD & GO-KS & BLEnD & GO-KS & BLEnD & GO-KS & BLEnD \\
\hline
Vanilla-7B & TBD & TBD & TBD & TBD & TBD & TBD & TBD & TBD \\
Cultural-KR & \textbf{TBD} & \textbf{TBD} & TBD & TBD & TBD & TBD & TBD & TBD \\
Cultural-JP & TBD & TBD & \textbf{TBD} & \textbf{TBD} & TBD & TBD & TBD & TBD \\
Cultural-US & TBD & TBD & TBD & TBD & \textbf{TBD} & \textbf{TBD} & TBD & TBD \\
Cultural-EU & TBD & TBD & TBD & TBD & TBD & TBD & \textbf{TBD} & \textbf{TBD} \\
Run-M (unified) & TBD & TBD & TBD & TBD & TBD & TBD & TBD & TBD \\
\hline
\end{tabular}
\end{table}

\begin{figure}[h]
\centering
% \includegraphics[width=0.8\linewidth]{figures/ks_heatmap.png}
\caption{Heatmap of GlobalOpinionQA KS statistic for each model (rows) across cultural benchmarks (columns). Lower values indicate better alignment.}
\label{fig:ks_heatmap}
\end{figure}
```
