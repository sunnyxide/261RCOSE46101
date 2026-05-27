# Brief 14 — Synthetic held-out cultural eval set (Korean MCQ)

## Context
For robustness, we want a small held-out eval set that's NOT in any public benchmark (KoBBQ, HAE-RAE, CLIcK, KMMLU, BLEnD) so we can claim "the model generalizes to unseen Korean cultural questions". Synthetic but plausible.

## Task

Generate **50 Korean cultural MCQ items** distributed across these categories:
- **Korean cultural practice** (예절, 명절, 가족 행사, 회식) — 10 items
- **Korean linguistic register** (존댓말, 호칭, 지역 사투리) — 8 items
- **Korean historical/factual** (역사, 인물, 지명, 음식 — but NEW, not common KMMLU coverage) — 8 items
- **Korean cultural values / Hofstede-loaded** (직장 위계, 가족 우선순위, 체면, 정/한) — 12 items
- **Korean modern pop culture** (K-pop, K-drama, 한류, 게임 문화) — 6 items
- **Korean economic/business culture** (재벌, 스타트업, 부동산, 교육 투자) — 6 items

Each item:
- `id`: integer
- `category`: one of the 6 above
- `question_ko`: Korean text
- `choices`: list of 4 strings (Korean)
- `answer_idx`: 0-3 (the culturally-correct answer)
- `cultural_specificity`: 1-5 — how Korean-specific is the answer (5 = only Korean cultural context yields this answer)
- `difficulty`: easy / medium / hard (for a non-native or vanilla LLM)
- `rationale`: 1 sentence why this is the answer in Korean cultural context

## Constraints
- Avoid topics already heavily covered by HAE-RAE Bench (e.g., common Korean idioms in the standard set)
- Avoid KoBBQ-style stereotype prompts (we want CULTURAL not BIAS testing)
- Mix difficulty: 30% easy, 50% medium, 20% hard

## Output

```jsonl
{"id": 0, "category": "Korean cultural practice", "question_ko": "결혼식에서 신랑 신부의 부모님이 양가 손님들에게 처음 인사를 드리는 순서는?", "choices": ["신랑측 부모님 먼저", "신부측 부모님 먼저", "주례선생님과 동시에", "양가 어른들이 따로 자리에서"], "answer_idx": 0, "cultural_specificity": 4, "difficulty": "medium", "rationale": "한국 결혼식 전통에서 신랑측 부모님이 신부측에 먼저 인사하는 것이 일반적 관례"}
...
```

End with:
```json
{"total": 50, "by_category": {...}, "by_difficulty": {"easy": N, "medium": N, "hard": N}}
```
