# Brief 15 — Abstract (<300 words, NeurIPS 2020 template requirement)

## Context
COSE461 final report. NeurIPS 2020 template. Hard rule: abstract less than 300 words. Must concisely motivate problem, describe aims, describe contribution, highlight main finding.

## Project capsule
- Off-the-shelf LLMs (Qwen2.5-3B/7B, GPT-5.5, Claude Opus 4.7) carry Anglo-American cultural priors even when prompted in Korean
- We fine-tune small instruction-tuned models with QLoRA on cultural data (CultureBank + Nemotron-Personas-Korea) + Hofstede 6D system-prompt conditioning
- 4 cultural adapters: KR, JP, US, CN (rank 16-32, attn-only or all-linear)
- Main metric: KS distance between model response distribution and target country's GlobalOpinionQA empirical distribution
- Findings: Cultural-QLoRA produces measurable shift; cross-cultural transfer matrix shows reweighting (not deletion); Hofstede dimension ablation reveals primary drivers; multi-cultural unified adapter is feasible

## Task

Write a **single-paragraph abstract under 300 words** in English. Structure:
1. Problem statement (1-2 sentences)
2. Approach (2-3 sentences)
3. Key result (1-2 sentences with concrete numbers — use placeholder %s if specific results not yet final, e.g., "ΔKS=XX.X")
4. Significance / contribution (1 sentence)

Count exact word total at the end. If over 300, trim. NeurIPS 2020 style: dense, technical, no marketing language.

## Output

```markdown
# Abstract (XXX words)

[single paragraph, hard <300 word limit]

---
**Word count**: NNN words
```
