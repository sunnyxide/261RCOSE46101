# Brief 01 — Related Work + Bibliography for Cultural-QLoRA paper

## Context
We are writing a paper (COSE461 Final, target NAACL/EACL workshop) on **cultural-conditioned QLoRA fine-tuning** for LLM persona generation. Specifically:

- Base models: Qwen2.5-3B-Instruct, Qwen2.5-7B-Instruct
- Training data: CultureBank + Nemotron-Personas-Korea + Hofstede 6D system-prompt conditioning
- Evaluation: KoBBQ (Korean bias), HAE-RAE Bench 1.1, CLIcK, GlobalOpinionQA (KS test), BLEnD (cultural common sense)
- Method: QLoRA rank 16-32, attn-only vs all-linear ablation
- Findings: Cultural-QLoRA shifts model response distribution toward target culture's WVS-aligned empirical distribution

## Task

Write a **comprehensive Related Work section (~1.5 pages, ~800 words)** + a **structured bibliography (≥30 entries)** covering:

### Sections to organize
1. **Cultural alignment / multilingual bias in LLMs** (e.g., Anthropic's Global Opinions paper, Cao et al. cultural alignment, AlKhamissi cultural-conditioning)
2. **Hofstede's cultural dimensions in NLP** (any prior use of Hofstede for LLM conditioning)
3. **Korean NLP benchmarks** (KoBBQ, HAE-RAE, CLIcK, KMMLU — cite original authors)
4. **Cross-cultural QA / opinion datasets** (BLEnD by Lee et al. 2024, CultureBank by Shi et al. NAACL 2024, GlobalOpinionQA, WVS-based eval)
5. **QLoRA / PEFT for domain adaptation** (Dettmers et al. 2023 QLoRA, Hu et al. LoRA, PEFT library)
6. **LLM persona generation** (Nemotron-Personas, prior persona-grounded fine-tuning work)
7. **Cultural simulation / consumer behavior with LLMs** (OASIS by Yang et al. NeurIPS 2024 — note: MiroFish 62K-star repo uses OASIS substrate)

### Format
Each section: 2-4 sentence summary of prior work + how our paper differs/extends.

### Bibliography format (BibTeX)
```bibtex
@inproceedings{authoryear_short_title,
  title={...},
  author={...},
  booktitle={...},
  year={20XX},
}
```

Provide at minimum:
- 5 entries on cultural LLM alignment
- 4 entries on Korean benchmarks (with KoBBQ Jin et al., HAE-RAE, CLIcK Kim et al., KMMLU)
- 3 entries on PEFT/QLoRA
- 3 entries on persona generation
- 3 entries on cross-cultural eval (BLEnD, CultureBank, GlobalOpinionQA)
- Anthropic Global Opinions (Durmus et al. 2023)
- Hofstede 1980/2010 foundational reference
- World Values Survey methodological reference

If unsure of exact citation, use best-known approximation and mark with `% TODO verify`.

## Output structure

```markdown
# Section 2: Related Work

## 2.1 Cultural Alignment in LLMs
[2-4 sentences per cited work...]

## 2.2 Hofstede Dimensions and Cultural NLP
...

## 2.3 Korean NLP Evaluation Benchmarks
...

[etc.]

## Bibliography (BibTeX)
@inproceedings{...
...
```
