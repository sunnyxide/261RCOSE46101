# Brief 09 — Paper Section 6 (Limitations) draft

## Context
Honest Limitations section for cultural-QLoRA paper. We want this strong because reviewers WILL find these limitations themselves — better to surface them proactively.

## Known limitations to discuss

### Model size and family
- Only Qwen2.5-3B and Qwen2.5-7B (one model family)
- No comparison to Llama-3, Mistral, EXAONE-Korean-pretrained
- 7B run uses unsloth's bnb-4bit pre-quantized weights (different quantization source than 3B → "quantization confound" — discussed in our internal decisions but worth flagging)

### Training data
- KR has Nemotron-Personas-Korea (rich, 4,800 examples) but JP/CN/US have only CultureBank (866/690/3,420)
- Imbalance across cultures means cultural-QLoRA effect is most powerful for KR; other cultures' results are noisier
- WVS Wave 7 micro-data not directly used — we rely on Anthropic's GlobalOpinionQA as proxy (aggregated already, distribution shape preserved but original survey design omitted)

### Evaluation
- Single seed per run, no error bars on KS statistics
- LLM-judge panel (gpt-5.5 + claude-opus-4-7 + mimo-v2.5-pro) — no human evaluation
- BLEnD and KoBBQ test sets, but cultural conditioning could plausibly memorize these via CultureBank overlap (we excluded KoBBQ from training data; CultureBank overlap is plausibly low but not formally measured)
- Cross-cultural KS is computed on n_samples=6-8 per question — distribution estimate noisy

### Cultural construct validity
- Hofstede 6D is a 1980s framework with known critiques (oversimplifies, biased toward IBM employee samples). We use it as a *signal* for cultural priors, not as ground truth for culture itself.
- "Cultural authenticity" judging assumes a monolithic culture per country (e.g., "Korean" responses), masking within-culture diversity (generation, region, gender)
- All training data is text — visual/auditory cultural cues absent

### Downstream applicability
- Consumer prediction demo uses 10 hand-picked scenarios — not a validated benchmark with ground-truth purchase data
- No deployment-quality testing (e.g., production user-facing chatbot)

### Reproducibility
- AWS sessions had multiple interruptions (instance restarts, disk full) — final results aggregated from multiple sessions, some intermediate adapters lost (Run-G JP retrained mid-flight)
- HuggingFace dataset versions not pinned — `datasets` library auto-fetches latest

## Task

Write a **~600-word Limitations section** organizing the above into 4-5 paragraphs:
1. Model and training-data scope
2. Evaluation methodology
3. Cultural construct validity (Hofstede critique)
4. Downstream applicability / reproducibility

Be HONEST not defensive. Frame each limitation with a sentence on how future work could address it.

## Output

```markdown
# 6. Limitations and Future Work

## Model and Data Scope
[paragraph]

## Evaluation
[paragraph]

## Cultural Construct Validity
[paragraph]

## Downstream Applicability
[paragraph]

## Reproducibility Notes
[paragraph]
```
