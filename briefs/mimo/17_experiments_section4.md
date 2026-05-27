# Brief 17 — Section 4 "Experiments" with template-required subsections

## Context
COSE461 final report Section 4. Template REQUIRES four subsections:
- 4.1 Data
- 4.2 Evaluation method
- 4.3 Experimental details
- 4.4 Results

Each subsection has specific guidance from template.

## Content per subsection

### 4.1 Data
- CultureBank (Shi et al. 2024 NAACL) — country-filtered, source dataset reference + URL placeholder
- Nemotron-Personas-Korea — NVIDIA HF, KR only
- KoBBQ (Jin et al. 2024) — 400 samples for eval, 200 ambig + 200 disambig, few-shot K=3
- KMMLU Korean-History (Son et al. 2024) — 100 samples
- HAE-RAE Bench 1.1 (Yoo et al.) — 100 samples × 4 subjects
- CLIcK (Kim et al. 2024) — Korean Cultural and Linguistic Intelligence
- GlobalOpinionQA (Durmus et al. 2023) — multinational opinion polling
- BLEnD MCQ (Lee et al. 2024) — Big Linguistic Evaluation of Norms and Diversity

Be PRECISE about input/output format for each.

### 4.2 Evaluation method
- KoBBQ: report `correct_rate` and `bias_rate` overall + per context_type (ambig/disambig). Lower bias_rate = less stereotype reinforcement.
- KMMLU / HAE-RAE / CLIcK: standard MCQ accuracy.
- GlobalOpinionQA: KS statistic between model response distribution (8 samples per question) and target country's empirical distribution. Report mean + median KS over 150-200 questions.
- BLEnD MCQ: accuracy, country-conditioned prompting.
- CAS LLM-judge panel (3 judges: gpt-5.5, Claude Opus 4.7, mimo-v2.5-pro): cultural_authenticity, persona_consistency, factual_accuracy on 1-5 scales, aggregated by median. Inter-rater pairwise diff reported for reliability.

### 4.3 Experimental details
- Hardware: AWS g6.xlarge (NVIDIA L4 24GB VRAM, 48GB EBS, 16GB swap)
- Quantization: NF4 4-bit, double quant, bfloat16 compute
- QLoRA hyperparameters: rank ∈ {16, 32}, α=2r, dropout 0.05, target ∈ {attn-only, all-linear}
- Training: per-device batch 1, gradient_accumulation 8, learning rate 2e-4, cosine scheduler with 3% warmup, paged_adamw_8bit optimizer, gradient checkpointing
- Epochs: 1-5 depending on dataset size (KR 5,535 examples → 2ep; JP 866 → 5ep)
- Total compute: approximately ~30 GPU-hours across 4 cultural adapters + ablations
- Seed: 42 (single seed — acknowledged limitation)

### 4.4 Results
Reference TODO placeholders for tables (final numbers fill in during paper finalization):
- **Table 1**: Baselines (Vanilla-3B/7B + KoAlpaca-QLoRA) × {KoBBQ, KMMLU, HAE-RAE, CLIcK} — 5×4 grid
- **Table 2**: Cultural-QLoRA per culture × in-distribution benchmarks — 4×N grid
- **Table 3 (main)**: 8 models × 4 cultures × {GO KS, BLEnD acc} cross-cultural matrix
- **Table 4**: Hofstede dimension ablation — KS shift per dimension variant
- **Figure 1**: KS heatmap (adapter × benchmark culture)
- **Figure 2**: Hofstede 6D radar — Vanilla vs Cultural-KR target vs achieved

Plain English narrative of quantitative findings:
- Vanilla LLMs show ~X KS distance to KR distribution
- Cultural-KR reduces this by ΔX percentage points
- Cross-cultural transfer shows neutrality (not deletion)
- IDV is/isn't the dominant Hofstede dimension
- Multi-cultural unified Run-M is competitive with per-culture adapters

End each subsection with template-suggested commentary: "Are results what we expected? Better/worse? Why?"

## Task

Write **Section 4 Experiments** with all 4 subsections. ~1.5-2 pages (~1000 words). Include:
- 1-2 LaTeX tables (use `\begin{tabular}` placeholders)
- Reference to figures (don't generate the figure but include `\caption{}` placeholder)
- Quantitative claims with placeholder numbers if not yet final (clearly mark "TBD" or "$\Delta X$")

## Output

```markdown
# 4. Experiments

## 4.1 Data
[paragraph + dataset table]

## 4.2 Evaluation Method
[paragraph]

## 4.3 Experimental Details
[paragraph]

## 4.4 Results
[main results narrative + 1-2 tables + figure references + commentary]
```
