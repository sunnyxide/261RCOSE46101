# Brief 19 — Section 6 "Conclusion" + limitations integrated

## Context
COSE461 final report Section 6. Template: "Summarize the main findings of your project, and what you have learnt. Highlight your achievements, and note the primary limitations of your work. If you like, you can describe avenues for future work."

NOTE: Limitations are integrated INTO Conclusion in this template (no separate Limitations section). Brief 09's limitations content should fold here.

## Content to organize

### What we did (1 paragraph)
- Built Cultural-QLoRA: Hofstede 6D system-prompt conditioning + cultural data (CultureBank + Nemotron-Personas) + small LLM (Qwen2.5-3B/7B)
- 4 cultural adapters (KR/JP/US/CN) + Hofstede ablation + multi-cultural unified adapter
- Cross-cultural alignment metric: GlobalOpinionQA KS + BLEnD MCQ

### Main findings (3-5 bullets)
1. **Cultural-QLoRA produces measurable response distribution shift** toward target culture's empirical distribution on multinational opinion surveys (ΔKS = TBD pp).
2. **Cross-cultural transfer matrix shows reweighting, not deletion** — Cultural-KR keeps US-context capability; cultural conditioning shifts priors without destroying other-culture knowledge.
3. **Hofstede dimension ablation** identifies which dimension drives the shift (IDV vs UAI vs full-6D — finding TBD from Run-G/H/I).
4. **Multi-cultural unified adapter feasible** — single Run-M model competitive with per-culture adapters when prompted with `<<culture:XX>>` token.
5. **Anomaly: cultural alignment includes cultural biases** — Cultural-KR's KoBBQ bias_rate INCREASED, reflecting Korean stereotype content embedded in cultural training data. Honest finding worth surfacing.

### What we learnt (1 short paragraph)
- Small models (3B) can shift cultural priors significantly with modest fine-tuning + Hofstede conditioning
- The system prompt does a lot of heavy lifting — LoRA refines but prompt sets prior weights
- Cultural alignment ≠ bias removal — these are orthogonal goals
- Frontier API models (GPT-5.5, Claude) score WORSE on Korean cultural questions than our 7B Cultural-KR, despite raw capability gap

### Limitations (integrated, ~150 words)
- Model size/family: Qwen2.5-3B/7B only; no Llama-3, EXAONE Korean-pretrained
- Single seed per run, no statistical significance bars on KS
- LLM-judge panel (3 judges) instead of human evaluation
- WVS Wave 7 data accessed via Anthropic's GlobalOpinionQA proxy (aggregated, not raw)
- Hofstede 6D is a 1980s framework with critiques (oversimplifies, IBM-sample bias)
- JP/CN cultural training data sparse (CultureBank only, no Nemotron equivalent)
- All-text training — no visual/auditory cultural cues
- Single language adaptation primarily (Korean); JP/US/CN treatments are weaker

### Future work (~100 words)
- Multi-seed training for statistical significance
- Human evaluation of cultural authenticity (IRB pending)
- Larger backbones (14B/27B Korean-pretrained EXAONE-3.5)
- Downstream tasks: consumer behavior prediction with held-out market data
- Cross-lingual cultural transfer: Korean adapter applied to English-language scenarios
- WVS Wave 7 raw micro-data direct comparison
- Bias-aware cultural conditioning (decouple alignment from stereotype reinforcement)

## Task

Write **Section 6 Conclusion** as a single flowing section. ~3/4 page (~500 words). Integrate limitations naturally (don't make a separate subsection — fold into "what we learnt" or end-paragraph). Future work as final paragraph.

NeurIPS-style: dense, no marketing language.

## Output

```markdown
# 6. Conclusion

[Paragraph 1: what we did]

[Paragraph 2: main findings, 3-5 sentences]

[Paragraph 3: what we learnt + limitations integrated]

[Paragraph 4: future work]
```
