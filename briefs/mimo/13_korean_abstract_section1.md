# Brief 13 — Korean abstract + Korean Section 1 (parallel version)

## Context
Korea University COSE461 final paper may benefit from a parallel Korean abstract + Korean introduction. Used as appendix or for Korean-language venues (한국정보과학회 KSC).

## Source context
We have an English-language paper draft (Section 1 from brief 04 should be available, but you can draft from project background). Key claims:
- Off-the-shelf LLMs (Qwen2.5-3B/7B, GPT-5/Claude) have Anglo cultural priors
- We propose Cultural-QLoRA with Hofstede 6D system-prompt conditioning + CultureBank/Nemotron-Personas training
- Main metric: GlobalOpinionQA KS distance to target country's empirical response distribution
- 4 cultural adapters (KR/JP/US/CN), cross-cultural transfer matrix, Hofstede dimension ablation
- Multi-cultural unified adapter feasibility

## Task

Produce:

### Part A: Korean abstract (200-250 자 / 한국어 어절 기준)
Standard NLP paper abstract structure: motivation → approach → key results → significance. Use Korean academic register (격식체, 한자어 비례 적절). Mix English technical terms (QLoRA, KS, Hofstede 6D) where natural.

### Part B: Korean Section 1 Introduction (~800 한국어 어절)
Same structure as English Section 1 (problem hook → problem statement → approach → contributions → outline) but written natively in Korean — NOT translated word-for-word but composed for Korean audience expectations.

Korean writing notes:
- 너무 직역체 (translation-ese) 피하기
- 한국 사례 (한국 소비자 행동, K-콘텐츠) 친화적 예시 추가 가능
- KAIST, 서울대, 고려대 등 한국 연구 인용 자연스럽게 (있다면)

## Output

```markdown
# 초록 (Abstract — 한국어)

[150-250 자, 표준 학술 초록 형식]

---

# 1. 서론

[800 어절, Korean introduction]

[Sub-headings: 1.1 문제 의식, 1.2 기존 연구의 한계, 1.3 접근 방식, 1.4 기여, 1.5 논문 구성]
```

End with a translation note explaining any term choices (e.g., "cultural alignment → 문화적 정렬" or 다른 표기).
