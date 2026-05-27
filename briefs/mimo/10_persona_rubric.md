# Brief 10 — Korean persona authenticity rubric (for human evaluation supplementary)

## Context
Our CAS LLM-judge panel scores `cultural_authenticity`, `persona_consistency`, `factual_accuracy` on 1-5. For paper supplementary, we want a more granular rubric that human annotators could use IF we run a small human study (might not happen this submission cycle).

## Task

Design a **detailed 5-criteria rubric** for evaluating Korean persona authenticity. Each criterion gets a 1-5 scale with concrete behavioral anchors per level.

### Criteria to develop

1. **Linguistic register (말투/존댓말 usage)** — does the persona use appropriate honorifics, age-marker, regional markers?
2. **Cultural reference accuracy** — does the persona mention culturally-accurate practices (food, holidays, etiquette)?
3. **Value system coherence** — does the persona's expressed values match Hofstede-Korea (high collectivism, high UAI, high LTO, high PDI)?
4. **Persona consistency across turns** — would the same persona's response in turn 3 be consistent with turn 1?
5. **Surface-level authenticity (does it feel native)** — does the text "ring true" as written by/about a Korean native, not translated tourist guide?

### For each level (1-5), provide:
- **Anchor description** (1 sentence)
- **Example response** (1-2 sentences of how a model at this level would respond to the prompt "한국에서 회식이 어떤 의미인가요?")

## Output

```markdown
# Korean Persona Authenticity Rubric (5-criteria × 5-level Likert)

## 1. Linguistic Register (말투/존댓말)

| Level | Anchor | Example response |
|---|---|---|
| 1 (very poor) | Uses only basic 반말 or robotic translation-like Korean | "회식은 회사 행사다." |
| 2 | ... | ... |
| 3 | ... | ... |
| 4 | ... | ... |
| 5 (excellent) | Naturally varies 존댓말/반말 by context, uses idiomatic phrasing | "회식은 단순히 술자리가 아니라, 같이 일하는 사람들과 정 쌓는 자리예요." |

## 2. Cultural Reference Accuracy
[same structure]

## 3. Value System Coherence
[same structure]

## 4. Persona Consistency
[same structure]

## 5. Surface-Level Authenticity
[same structure]
```

End with a brief 100-word usage guide for human annotators.
