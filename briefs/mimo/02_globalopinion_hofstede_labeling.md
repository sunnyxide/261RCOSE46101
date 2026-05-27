# Brief 02 — GlobalOpinionQA → Hofstede 6D dimension labeling

## Context
GlobalOpinionQA (Anthropic, Durmus 2023) has ~2,500 multinational opinion questions. We need to annotate each with which Hofstede cultural dimension it primarily probes, so we can decompose our cross-cultural KS shift by dimension in the paper.

Hofstede 6D (with definitions):
- **PDI** (Power Distance Index): tolerance for hierarchical inequality
- **IDV** (Individualism vs Collectivism): self vs group orientation
- **MAS** (Masculinity vs Femininity): assertiveness vs nurturing values
- **UAI** (Uncertainty Avoidance Index): tolerance for ambiguity/risk
- **LTO** (Long-Term Orientation): future vs present focus, pragmatism
- **IVR** (Indulgence vs Restraint): gratification of human desires

## Task

I will provide a sample of 200 GlobalOpinionQA questions inline below. For EACH question, output a JSON line with:
- `qid`: integer (the question index in my input)
- `primary_dim`: one of {PDI, IDV, MAS, UAI, LTO, IVR, NONE}
- `secondary_dim`: optional second dimension, or null
- `confidence`: low / medium / high
- `rationale`: 1 sentence why this dim

Mark `NONE` for questions that don't clearly probe any cultural dimension (e.g., factual policy questions like "Should Germany have more EU influence?").

## Sample 200 questions

(Note to mimo: load from `data/cultural/globalopinion_sample.json` if available, or synthesize plausible 200 multinational opinion questions if file missing. If synthesizing, document the source clearly in output header.)

## Output format

```jsonl
{"qid": 0, "primary_dim": "IDV", "secondary_dim": null, "confidence": "high", "rationale": "Question about family decision-making — direct IDV probe"}
{"qid": 1, "primary_dim": "UAI", "secondary_dim": "LTO", "confidence": "medium", "rationale": "..."}
...
```

End with summary statistics:
```json
{"total": 200, "by_dim": {"PDI": N, "IDV": N, "MAS": N, "UAI": N, "LTO": N, "IVR": N, "NONE": N}}
```
