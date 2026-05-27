# Brief 06 — KoBBQ stereotype taxonomy annotation

## Context
KoBBQ (Jin et al. 2024) is a Korean bias benchmark with ~76,048 samples covering Korean-specific stereotypes. We evaluated on 400 samples (200 ambig + 200 disambig). For the paper's bias-mitigation discussion we need to break down bias scores by stereotype category — which Korean stereotypes is the model reinforcing/avoiding?

## KoBBQ official categories (from Jin et al. 2024)
1. Age
2. Disability status
3. Gender identity
4. Nationality
5. Physical appearance
6. Race / ethnicity
7. Religion
8. Sexual orientation
9. Socioeconomic status
10. **Korean-specific**: Educational background, Family structure, Domestic area of origin, Political orientation

## Task

For our evaluation set of 200 KoBBQ samples (assume randomly drawn), produce a structured taxonomy annotation:

For each sample provide:
- `sample_id`: integer
- `category_main`: one of the 13 categories above
- `category_subtype`: more specific (e.g., for "Domestic area of origin" → "전라도/경상도 stereotype")
- `stereotype_target`: which group is the stereotype about (e.g., "older workers", "전라도 사람")
- `cultural_specificity`: 1-5 — how Korean-specific is this stereotype (5 = purely Korean cultural framing, 1 = universal)
- `severity`: 1-5 — how harmful is this stereotype if reinforced

If you can't access the actual KoBBQ samples, **simulate 100 realistic Korean stereotype prompts** distributed across the 13 categories (~7-8 per category) and label them accordingly. Document the simulation in output header.

## Output

```jsonl
{"sample_id": 0, "category_main": "Age", "category_subtype": "older workers vs new hires", "stereotype_target": "older Korean office workers", "cultural_specificity": 4, "severity": 3}
...
```

End with category distribution + mean cultural_specificity per category:
```json
{"total": 100, "by_category": {"Age": 8, ...}, "mean_cultural_specificity_by_category": {...}}
```
