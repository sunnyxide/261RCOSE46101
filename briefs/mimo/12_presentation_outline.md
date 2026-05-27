# Brief 12 — COSE461 Final Presentation slide outline (Korean university final)

## Context
COSE461 (Korea University NLP) team final presentation. Team 8 토큰해적단 / Token Pirates. Audience: course professor + TA + fellow students.

Need a **18-20 slide presentation outline** in Korean (with English technical terms preserved).

## Project recap for slide-flow planning
- Title: "Cultural-QLoRA: Hofstede-Conditioned Persona Generation for Korean LLMs"
- Team: 주선우 (2023320312, ELONFLAME on GitHub) + 김민수 (2022320337)
- Hypothesis: Off-the-shelf LLMs over-represent Anglo cultural priors; cultural-QLoRA with Hofstede 6D conditioning + curated cultural data shifts response distributions toward target culture
- 4 cultural adapters (KR, JP, US, CN) on Qwen2.5-3B/7B
- Cross-cultural alignment metric: GlobalOpinionQA KS + BLEnD
- Hofstede dimension ablation
- Multi-cultural unified adapter as bonus
- Mac inference demo for "consumer deployment"

## Task

Generate a **20-slide outline** in Korean + English. For each slide:
- Slide title (Korean primary)
- 3-5 bullet points (Korean + English technical terms)
- Visual suggestion (chart type, table, code snippet, demo screenshot)
- Speaker notes / "what to say" (1-2 sentences)

### Slide structure
1. **Title + Team** (introductions, course context)
2. **Problem motivation** (cultural bias examples — Vanilla Qwen-3B답하는 모습 vs 한국 native)
3. **Research question** (3 sub-questions)
4. **Related work**
5. **Approach overview** (architecture diagram)
6. **Cultural training data construction** (CultureBank + Nemotron + Hofstede)
7. **QLoRA training setup** (rank/epoch ablation table)
8. **Evaluation framework** (KoBBQ, KMMLU, HAE-RAE, CLIcK, GO, BLEnD)
9. **Section 4.1 Baselines results** (5 models × 7 benchmarks table)
10. **Section 4.2 Cultural-QLoRA per culture** (4 cultures, KoBBQ shift highlighted)
11. **Section 4.3 Cross-cultural alignment** (KS heatmap — MAIN CONTRIBUTION)
12. **Section 4.4 Transfer matrix** (which adapters transfer to which cultures)
13. **Section 4.5 Hofstede dimension ablation** (which dim drives shift)
14. **Section 4.6 Multi-cultural unified Run-M** (single model 4-culture)
15. **Consumer deployment demo** (Mac MLX 실시간 데모 영상)
16. **Limitations honest** (model size, single seed, etc.)
17. **Comparison to MiroFish (62K-star) and other prior work**
18. **Conclusions** (4-5 key findings)
19. **Future work** (multi-seed, human eval, downstream task)
20. **Q&A — Thank you + GitHub link**

## Output

```markdown
# COSE461 Team 8 토큰해적단 — Cultural-QLoRA 발표 슬라이드 outline

## Slide 1 — Title + Team
**Title (KR/EN)**: ...
**Bullets**:
- ...
**Visual**: ...
**Speaker notes**: ...

## Slide 2 — Problem motivation
[same structure]

[...18 more slides]
```
