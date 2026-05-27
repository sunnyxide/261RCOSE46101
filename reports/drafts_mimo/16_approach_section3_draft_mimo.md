```markdown
# 3. Approach

## 3.1 Problem Formulation

We formalize cultural alignment as the task of steering a language model's response distribution toward that of a target culture. Let $p$ denote a user prompt, $c \in \mathcal{C}$ a target culture (e.g., South Korea, Japan, United States, China), and $h_c \in \mathbb{R}^6$ the corresponding Hofstede cultural-dimension vector comprising Power Distance (PDI), Individualism (IDV), Masculinity (MAS), Uncertainty Avoidance (UAI), Long-Term Orientation (LTO), and Indulgence (IVR) \cite{hofstede2010_cultures}. Let $P_c^*(\cdot \mid p)$ denote the empirical response distribution for culture $c$ on prompt $p$, estimated from large-scale multinational survey data such as GlobalOpinionQA \cite{durmus2023_globalopinionqa}. Our goal is to learn parameters $\theta$ of a model $M_\theta$ such that its output distribution $P_{M_\theta}(\cdot \mid p, c)$ is close to $P_c^*(\cdot \mid p)$ for every culture $c$. We measure distributional distance via the Kolmogorov--Smirnov (KS) statistic applied over discretized answer options:

\begin{equation}
D_{\mathrm{KS}}\!\bigl(P_{M_\theta},\, P_c^*\bigr)
\;=\;
\sup_{x \in \mathcal{X}} \bigl| F_{M_\theta}(x) - F_c^*(x) \bigr|,
\label{eq:ks}
\end{equation}

where $F_{M_\theta}$ and $F_c^*$ are the cumulative distribution functions over the finite answer set $\mathcal{X}$ and the supremum is taken point-wise. Lower $D_{\mathrm{KS}}$ indicates better cultural alignment. We define the **alignment shift** $\Delta_{\mathrm{KS}}^{(a,c)}$ of adapter $a$ on culture $c$ as:

\begin{equation}
\Delta_{\mathrm{KS}}^{(a,c)} \;=\; D_{\mathrm{KS}}\!\bigl(P_{M_a},\, P_c^*\bigr) \;-\; D_{\mathrm{KS}}\!\bigl(P_{M_{\mathrm{vanilla}}},\, P_c^*\bigr),
\label{eq:shift}
\end{equation}

so that negative values indicate improvement over the unadapted base model.

## 3.2 Hofstede-Conditioned QLoRA Architecture

Our method augments a pre-trained instruction-tuned LLM with lightweight, culture-conditioned adapters. We adopt QLoRA \cite{dettmers2023qlora}, which reduces the frozen base model to 4-bit NormalFloat (NF4) precision with double quantization while performing parameter-efficient fine-tuning via low-rank adapters (LoRA; rank $r \in \{16, 32\}$, scaling factor $\alpha = 2r$) \cite{hu2022_lora} on all linear projection layers. The fine-tuning objective is the standard causal language-modeling loss:

\begin{equation}
\mathcal{L}(\theta) \;=\; -\sum_{t=1}^{T} \log P_\theta\!\bigl(y_t \mid y_{<t},\, \text{sys}_c,\, x\bigr),
\label{eq:loss}
\end{equation}

where $x$ is the user instruction, $y$ is the gold response, and $\text{sys}_c$ is a structured system prompt that encodes the target culture's Hofstede profile. Specifically, we construct:

\[
\text{sys}_c \;=\; f_{\text{format}}\!\bigl(h_c,\; \text{name}(c),\; \text{lang}(c)\bigr)
\;=\;
\texttt{"You are a cultural persona from } \text{name}(c)
\texttt{. Hofstede dimensions: PDI=}\,h_c^{\text{PDI}}\texttt{, \ldots, IVR=}\,h_c^{\text{IVR}}\texttt{."}
\]

Figure~\ref{fig:arch} illustrates the full pipeline: a single set of Hofstede scores is serialized into the system prompt, the base model is quantized and frozen, and culture-specific LoRA adapters are trained on paired (instruction, culturally-appropriate response) data.

\begin{figure}[h]
\centering
\fbox{\parbox{0.95\linewidth}{\centering\vspace{2em}\textit{[Architecture diagram: frozen 4-bit Qwen2.5 backbone $\rightarrow$ system prompt with Hofstede 6D vector $\rightarrow$ LoRA adapters on all linear layers $\rightarrow$ culturally-conditioned response generation.]}\vspace{2em}}}
\caption{Hofstede-Conditioned QLoRA. The Hofstede 6D vector $h_c$ is serialized into the system prompt; only LoRA adapter weights are updated during training.}
\label{fig:arch}
\end{figure}

## 3.3 Cultural Training Data

We curate culture-specific training corpora from two sources. **CultureBank** \cite{shi2024_culturebank} provides country-filtered cultural knowledge with two text variants per entry: descriptive passages and persona-style question--answer pairs. **Nemotron-Personas** (NVIDIA, 2024) supplies rich Korean persona descriptions, from which we derive three prompt variants per persona. After filtering by locale, the per-culture corpus sizes are: South Korea (KR) 5,535, United States (US) 3,420, Japan (JP) 866, and China (CN) 690 examples. All training data is formatted as (system prompt, user instruction, assistant response) triples following the chat template of the respective base model.

## 3.4 Cross-Cultural Evaluation Protocol

For each culture-specific adapter $a$ trained on culture $c_{\text{train}}$, we evaluate on every target culture $c_{\text{test}} \in \mathcal{C}$ using GlobalOpinionQA \cite{durmus2023_globalopinionqa}, a dataset of opinion survey questions with per-country ground-truth distributions. We report $\Delta_{\mathrm{KS}}^{(a,c_{\text{test}})}$ (Eq.~\ref{eq:shift}), where negative values mean the adapted model is closer to the target culture's survey distribution than the vanilla base model. This cross-evaluation matrix reveals both in-culture improvement and potential out-of-culture degradation.

## 3.5 Hofstede Dimension Ablation

To isolate the contribution of individual cultural dimensions, we train three ablated Korean adapters with system prompts encoding: (i) IDV only, (ii) UAI only, and (iii) all six Hofstede dimensions. Comparing their $\Delta_{\mathrm{KS}}$ values on the Korean evaluation set identifies which dimensions are necessary or sufficient for alignment.

## 3.6 Multi-Cultural Unified Adapter (Run-M)

We train a single LoRA adapter on the concatenation of all four culture corpora, prepending a discrete culture token \texttt{<<culture:xx>>} to each system prompt. At inference time, the user selects the desired culture. This tests whether a single adapter can dynamically condition on the requested culture without requiring separate adapter weights per culture.

## 3.7 Baselines

We compare against three baselines: (1) **Vanilla Qwen2.5-Instruct** (3B/7B) with no cultural fine-tuning; (2) **KoAlpaca-QLoRA**, a Korean instruction-tuned adapter on Qwen-3B without Hofstede conditioning, isolating the effect of culture-specific data from the Hofstede signal; and (3) **Frontier API models** (GPT-4o, Claude 3.5 Sonnet) evaluated zero-shot as reference points for general capability, acknowledging these are not culture-conditioned.
```
