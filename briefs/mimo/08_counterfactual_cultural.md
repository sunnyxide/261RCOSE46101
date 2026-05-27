# Brief 08 — Counterfactual cultural example pairs (KR ↔ non-KR)

## Context
For paper's discussion of "what specifically is Korean" in our Cultural-KR adapter, we need contrastive example pairs showing the same scenario interpreted differently by Korean vs non-Korean cultural priors. These can also seed adversarial probes (does our adapter shift KR-specific responses while leaving universal ones alone?).

## Task

Generate **50 counterfactual pairs**. For each pair:
- A **scenario** (a 1-2 sentence situation, written in Korean)
- A **Korean cultural interpretation/response** (what a Hofstede-Korea person would say/do)
- A **counterfactual interpretation** (what someone from a different cultural prior — e.g., American IDV=91, UAI=46 — would say/do)
- The **Hofstede dimension(s)** the divergence taps

Examples of good scenario types:
- Workplace situations (hierarchy, decision-making)
- Family decisions (parent involvement, generational deference)
- Social etiquette (introductions, gift-giving, conflict resolution)
- Education and child-raising
- Food and dining (sharing, drinking, ordering)
- Risk and uncertainty handling (financial, career)
- Time orientation (planning, tradition vs change)
- Group vs individual achievement

## Output

```jsonl
{
  "pair_id": 0,
  "scenario_ko": "회식 자리에서 상사가 일찍 떠나려 한다. 본인은 다음날 중요한 미팅이 있다.",
  "kr_response": "상사가 가신 후에도 동료들과 자리를 지키는 것이 예의. 다음날 일찍 일어나서 준비함.",
  "counterfactual_response_us": "상사가 떠나는 자리에서 본인도 같이 일어나거나, 미팅 준비를 이유로 일찍 양해를 구하고 떠남.",
  "hofstede_dims": ["PDI", "IDV"],
  "explanation": "한국은 high PDI + low IDV — 상사 후 남는 것이 in-group 예의, 미국은 low PDI + high IDV — 개인 일정 우선"
}
...
```

50 pairs minimum. Spread across the 8 scenario types listed above (~6 each).

If output token budget is tight, prioritize quality over quantity — 30 high-quality pairs better than 50 superficial ones.
