# Brief 18 — Section 5 "Analysis" (QUALITATIVE — required by template)

## Context
COSE461 final report Section 5. Template instruction: "Your report should include *qualitative evaluation*. That is, try to understand your system (e.g. how it works, when it succeeds and when it fails) by inspecting key characteristics or outputs of your model."

This is NOT more results tables. This is **qualitative inspection** of model behavior — example outputs, error analysis, success/failure modes.

## Content to include

### 5.1 Sample generations comparison (Vanilla vs Cultural-KR)
Pick 5 prompts that show clear behavioral divergence. For each, show:
- Prompt (Korean)
- Vanilla Qwen-3B response (English-leaning, generic)
- Cultural-KR response (Korean, culturally-grounded)
- 1-sentence analysis of the divergence

Example prompt types:
- "회식의 의미는?" — workplace bonding ritual
- "추석에 가족이 모이는 의미는?" — long-term orientation (LTO)
- "직장 상사와 의견 충돌 시 행동?" — power distance (PDI)
- "결혼 결정에 부모님 의견의 비중은?" — collectivism (IDV)

### 5.2 Success modes (when Cultural-QLoRA works)
- Workplace etiquette / hierarchy questions: large KS shift, qualitatively native-sounding
- Family/relational scenarios: Hofstede-IDV-aligned responses
- Food/dining/holiday cultural facts: factually accurate Korean specifics
- General-knowledge with Korean cultural context: better cultural framing

### 5.3 Failure modes (when Cultural-QLoRA struggles)
- Highly factual questions (KMMLU drops slightly — cultural focus distracts from facts)
- KoBBQ disambig context where the literal correct answer requires careful reading (cultural framing can over-hedge)
- Cross-cultural transfer: when asked about US/JP from KR adapter, model can revert to Korean perspective even when culture-tag indicates other culture (Run-M issue)
- Out-of-distribution prompts (e.g., programming questions) where cultural conditioning is irrelevant — model still tries to apply it

### 5.4 Why does cultural conditioning work? (mechanism hypothesis)
- Hofstede system prompt sets prior weights; LoRA refines on cultural examples
- Likely the system prompt's effect dominates for short responses; LoRA's effect dominates for longer generations where cultural drift accumulates
- Evidence: Hofstede ablation (Section 4.4) shows minimal IDV-only or UAI-only configs already capture significant shift, suggesting prior signal in the prompt is heavily weighted

### 5.5 Anomaly explanation: Cultural-KR KoBBQ bias INCREASED
- Vanilla-3B bias rate: 0.450; Cultural-KR: 0.487 (+3.7pt)
- Interpretation: training on Korean cultural data does include Korean stereotypes embedded in CultureBank/Nemotron content
- This is a **legitimate paper finding** — "cultural alignment includes cultural biases", not a bug
- Connects to ethical considerations in Conclusion

### 5.6 Hofstede dimension contribution analysis
Based on ablation results, discuss which dimension(s) drive(s) the shift:
- If IDV-only ≈ full-6D → collectivism conditioning sufficient
- If all-6D > any single → composite cultural signal needed
- Speculate on why (e.g., IDV is the most consequential dim for ordinary social text)

## Task

Write **Section 5 Analysis** — qualitative, ~1 page (~700 words). Mix Korean example text (in quotes/codeblocks) with English analysis. Include:
- 1 explicit Korean comparison table (Vanilla vs Cultural-KR responses on 5 prompts)
- Success/failure mode classification
- Mechanism hypothesis
- Anomaly explanation

## Output

```markdown
# 5. Analysis

## 5.1 Qualitative Comparison: Vanilla vs Cultural-KR
[Korean comparison table]

## 5.2 Success Modes
[paragraph]

## 5.3 Failure Modes
[paragraph]

## 5.4 Mechanism Hypothesis
[paragraph]

## 5.5 Anomaly: Cultural-KR Bias Increase
[paragraph]

## 5.6 Hofstede Dimension Contribution
[paragraph]
```
