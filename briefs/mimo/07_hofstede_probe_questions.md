# Brief 07 — Hofstede 6D probe question set (Korean)

## Context
For our Hofstede dimension ablation (which dimension drives cultural shift?), we need a probe question set that selectively activates each dimension. This complements GlobalOpinionQA by being a controlled diagnostic.

Hofstede 6D Korea scores (reference distribution targets):
- PDI=60 (medium-high power distance)
- IDV=18 (very collectivist)
- MAS=39 (relatively feminine/nurturing)
- UAI=85 (very high uncertainty avoidance)
- LTO=100 (extremely long-term oriented)
- IVR=29 (relatively restrained)

## Task

Generate **30 Korean-language probe questions per dimension (180 total)**. Each question should:
- Force the responder to make a value judgment that aligns with one extreme of the dimension
- Have a clear "Korean-Hofstede-typical" answer (e.g., for IDV=18, a question where "I prioritize family over individual goals" is the Korean-typical response)
- Be answerable in 1-3 sentences or by choosing from 2-4 options

## Format

For each question, provide:
- `dim`: PDI / IDV / MAS / UAI / LTO / IVR
- `question_ko`: Korean text
- `question_en`: English translation (for paper appendix)
- `kr_typical_response`: short text describing the response a Hofstede-Korea-conditioned model should give
- `polar_response`: the opposite extreme (e.g., for IDV: kr_typical = "family first", polar = "individual achievement first")

## Output

```jsonl
{"dim": "IDV", "question_ko": "직장에서 본인의 의견과 팀의 다수 의견이 다를 때 어떻게 행동하나요?", "question_en": "At work, when your opinion differs from the team majority, what do you do?", "kr_typical_response": "팀의 결정을 따르고 조화를 유지한다 (collectivist, in-group harmony)", "polar_response": "내 의견을 강하게 어필하고 설득한다 (individualist)"}
...
```

Distribute roughly 5 questions per dimension × 6 dimensions = 30 examples MINIMUM. Aim for 30 per dimension = 180 total if possible.

Diversity guidance: cover domains like work/career, family, education, religion, food/dining etiquette, hierarchy, decision-making, risk/uncertainty, time orientation, leisure/restraint.

## Output file
`data/probes/hofstede_6d_korean.jsonl` style (just the JSONL content as response body)
