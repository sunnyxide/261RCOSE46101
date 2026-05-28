# Cultural-QLoRA: Hofstede-Conditioned Persona Generation for Korean LLMs

**COSE461 Final Project — Korea University, Spring 2026**

| | |
|---|---|
| **Team** | 8 — 토큰해적단 (Token Pirates) |
| **Members** | 주선우 (2023320312) · 김민수 (2022320337) |
| **Course** | COSE461 Natural Language Processing |
| **Repo** | `https://github.com/sunnyxide/261R0136COSE34102` |

---

## Project summary

Off-the-shelf instruction-tuned LLMs over-represent Anglo-American cultural priors even when prompted in Korean. This project investigates whether **QLoRA fine-tuning with Hofstede-6D system-prompt conditioning** on cultural exemplar data (CultureBank + Nemotron-Personas-Korea) measurably shifts a small model's response distribution toward a target culture's empirical distribution on multinational opinion surveys.

We train four per-culture adapters (KR / JP / US / CN) on Qwen2.5-3B and one on Qwen2.5-7B, plus a unified multi-cultural adapter, and evaluate against six Korean benchmarks plus a cross-cultural KS metric.

## Key contributions

1. **Cultural-QLoRA pipeline** — Hofstede-6D-conditioned QLoRA on small (3B/7B) instruction-tuned models with structured cultural training data.
2. **Cross-cultural alignment metric** — Kolmogorov–Smirnov distance between model response distribution and target country's empirical distribution on GlobalOpinionQA, complemented by BLEnD MCQ accuracy.
3. **Cross-cultural transfer matrix** — 4 adapters × 4 benchmark cultures: characterizes whether cultural conditioning reweights or deletes other-culture knowledge.
4. **Hofstede dimension ablation** — IDV-only / UAI-only / full-6D variants to identify which dimension drives the shift.
5. **Multi-cultural unified adapter (Run-M)** — single model with `<<culture:xx>>` token, tests dynamic cultural conditioning.
6. **CAS three-judge panel** — GPT-5.5 + Claude Opus 4.7 + MiMo v2.5-Pro median scoring on cultural_authenticity / persona_consistency / factual_accuracy.

## Reproducibility

### Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env       # populate OPENAI_API_KEY, ANTHROPIC_API_KEY, XIAOMI_PLAN_API_KEY, HF_TOKEN
```

### Training a cultural adapter
```bash
# Step 1: build per-culture cultural training set
python scripts/build_cultural_dataset.py --culture kr --target 12000

# Step 2: train Cultural-QLoRA
python scripts/cultural_qlora_train.py \
    --culture kr \
    --base-model Qwen/Qwen2.5-3B-Instruct \
    --run-id run-f-kr-rank32 \
    --num-epochs 2 --lora-rank 32 --lora-target all_linear
```

### Evaluation
```bash
# In-distribution Korean benchmarks (KoBBQ/KMMLU/HAE-RAE/CLIcK)
python scripts/phase1_extended_eval.py \
    --config config/eval_5way.json \
    --out results/benchmarks/phase1_extended.json \
    --few-shot 3 --n-kobbq 400 --n-kmmlu 200 --n-haerae 100 --n-click 100

# Cross-cultural alignment (KS + BLEnD)
python scripts/cross_cultural_eval.py \
    --base Qwen/Qwen2.5-3B-Instruct \
    --adapter runs/run-f-kr-*/adapter_final \
    --culture kr \
    --n-globalopinion 200 --n-blend 100 --n-samples-globalopinion 8 \
    --out results/benchmarks/cross_cultural_run-f-kr_kr.json
```

### Aggregation
```bash
python scripts/aggregate_results.py
# Produces reports/final_results_table.md + reports/final_summary.json
```

## Section ↔ Code mapping

| Paper Section | Implementation | Data |
|---|---|---|
| §3.1 Problem formulation | `scripts/cross_cultural_eval.py:ks_stat` | — |
| §3.2 Hofstede conditioning | `scripts/build_cultural_dataset.py:system_prompt` | `data/cultural/{culture}/train.jsonl` |
| §3.3 Cultural training data | `scripts/build_cultural_dataset.py` | CultureBank, Nemotron-Personas-Korea |
| §3.4 QLoRA training | `scripts/cultural_qlora_train.py` | `runs/run-{f,g,h,i,j,m}-*` |
| §4.1 Baseline benchmarks | `scripts/phase1_extended_eval.py` | KoBBQ, KMMLU, HAE-RAE 1.1, CLIcK |
| §4.3 Cross-cultural KS | `scripts/cross_cultural_eval.py` | GlobalOpinionQA, BLEnD |
| §4.4 Hofstede ablation | `scripts/phase3_hofstede_ablation.sh` | `data/cultural/kr_{idv_only,uai_only,all6d}/` |
| §5 CAS LLM-judge | `scripts/cas_judge_panel.py` | `results/cas_corpus/`, `results/cas_scores/` |

## Repository layout

```
.
├── README.md                  ← you are here
├── SETUP.md                   ← environment setup details
├── reports/
│   ├── overleaf/              ← NeurIPS 2020 .tex template + final report
│   ├── final_results_table.md ← auto-generated paper-ready results
│   ├── sections/              ← per-section drafts
│   └── drafts_mimo/           ← MiMo-generated section drafts (review before finalizing)
├── scripts/                   ← all training + eval + orchestration code
├── data/cultural/             ← per-culture training jsonl (regenerable via build script)
├── results/
│   ├── benchmarks/            ← KoBBQ, KMMLU, HAE-RAE, CLIcK, cross_cultural_*.json
│   ├── cas_corpus/            ← persona generations for CAS judging
│   ├── cas_scores/            ← 3-judge panel scores
│   └── baselines/             ← before/after corpus samples
├── decisions/                 ← decision log (every non-obvious call documented)
├── briefs/                    ← agent task briefs (Hermes + MiMo)
├── docs/internal/             ← internal infrastructure docs (not graded content)
└── notebooks/                 ← exploratory notebooks
```

## AI usage disclosure

This project uses LLM assistance throughout the development cycle:
- **Code & infrastructure**: Claude (Sonnet 4.6 / Opus 4.7) for script implementation, debugging, and orchestration
- **Section drafting**: MiMo v2.5-Pro (Xiaomi) for draft generation, reviewed and edited by team
- **Evaluation judging**: GPT-5.5 + Claude Opus 4.7 + MiMo v2.5-Pro panel for CAS scoring
- **All AI-generated content was reviewed by the team before inclusion**

Detailed disclosure in `docs/internal/AI_USAGE_DISCLOSURE.md` (when finalized).

## License

Code: MIT. Reports / paper: course submission, see Course AI Policy.

## Acknowledgments

- **Course**: COSE461 Spring 2026, Korea University Department of Computer Science
- **Compute**: AWS (allocated via course / NxtGen), Xiaomi Plan endpoint
- **Datasets**: CultureBank (SALT-NLP), Nemotron-Personas-Korea (NVIDIA), KoBBQ (NAVER AI), HAE-RAE (HAERAE-HUB), CLIcK (Eunsu Kim), KMMLU (HAERAE-HUB), GlobalOpinionQA (Anthropic), BLEnD (Nayeon Lee et al.)
