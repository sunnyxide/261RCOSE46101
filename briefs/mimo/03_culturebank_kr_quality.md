# Brief 03 — CultureBank Korean rows quality labeling

## Context
We have 1,026 CultureBank rows tagged "Korean" (from tiktok + reddit splits) used as part of our Cultural-QLoRA training. Some are high-signal cultural descriptors, others are noisy/superficial. We want to label each for quality so we can ablation-study (full vs filtered) and report the data quality distribution in our paper.

## Sample structure
Each CultureBank row has:
- `eval_whole_desc`: cultural descriptor sentence
- `topic`: theme (e.g., "Dress Codes", "Migration")
- `actor_behavior`: the specific behavior
- `eval_persona`: who is being addressed
- `eval_question`: example question they might ask
- `cultural group`: "Korean" / "South Korean"

## Task

For each Korean row (assume you can simulate ~50 representative samples), score:
- `cultural_relevance_kr`: 1-5 — how genuinely Korean is this descriptor (vs generic Asian/global)?
- `accuracy`: 1-5 — does this match real Korean cultural practice?
- `specificity`: 1-5 — is this specific enough to be useful (e.g., "Koreans eat rice" = low; "Koreans pour drinks for elders with two hands as 예의" = high)?
- `quality_overall`: 1-5 weighted (relevance × 0.4 + accuracy × 0.4 + specificity × 0.2)
- `flag_for_review`: bool — true if any issue (stereotype, dated, factually wrong)
- `note`: 1-sentence justification

## Output format

```jsonl
{"row_id": 0, "topic": "Dress Codes", "scores": {"cultural_relevance_kr": 4, "accuracy": 5, "specificity": 3, "quality_overall": 4.2}, "flag_for_review": false, "note": "Generic but accurate about formal dress in Korean business settings"}
...
```

End with:
```json
{"total_scored": N, "mean_quality": <float>, "fraction_flagged": <float>, "by_quality_bucket": {"1-2": N, "3": N, "4-5": N}}
```

If `data/cultural/kr/train.jsonl` is loadable, use rows where `source` starts with "culturebank". If not, simulate 50 plausible Korean cultural descriptors based on common CultureBank topics (food, hierarchy, language, family, work, etiquette) and document the source.
