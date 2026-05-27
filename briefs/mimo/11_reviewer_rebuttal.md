# Brief 11 — Reviewer rebuttal preparation (anticipated objections)

## Context
Anticipate the top objections an ACL/EACL workshop reviewer would raise on our Cultural-QLoRA paper, with prepared response strategies. Used as defensive preparation + checklist for paper revisions.

## Paper TL;DR (for context)
- Cultural-QLoRA = small-model QLoRA fine-tuning on cultural data (CultureBank + Nemotron-Personas + Hofstede 6D system prompts)
- Main metric: GlobalOpinionQA KS distance to target country's empirical response distribution
- Findings: KR cultural-QLoRA shifts toward Korean WVS distribution by Δ KS, transfer matrix shows reweighting (not deletion), Hofstede ablation reveals which dim drives shift, multi-cultural unified adapter is feasible
- Limitations: 3B/7B only, single seed, LLM-judge (no human eval)

## Task

Generate **top-10 reviewer objections** ranked by likelihood + severity. For each:
- **Objection** (1 sentence)
- **Likelihood** (high/medium/low)
- **Severity** (kill/major/minor)
- **Why a reviewer would raise it** (1-2 sentences)
- **Our prepared response** (2-3 sentences — either accept-and-mitigate, or counter-with-evidence)
- **Action item** (if we should fix something in the paper before submission)

### Categories of likely objections
- Methodological (e.g., "no human eval", "single seed", "model size too small")
- Theoretical (e.g., "Hofstede is critiqued", "GlobalOpinionQA isn't WVS directly")
- Statistical (e.g., "KS test on 6-8 samples is too noisy", "no significance test")
- Cultural construct validity (e.g., "monolithic 'Korean' culture assumed", "western-trained judges scoring Asian authenticity")
- Reproducibility (e.g., "datasets versioning", "AWS instance instability")
- Novelty (e.g., "CulturalBank/BLEnD already exist", "what's new vs Cao et al.")

## Output

```markdown
# Reviewer Rebuttal Preparation

## Objection #1: [title]
- **Likelihood**: HIGH
- **Severity**: MAJOR
- **Why raised**: ...
- **Our response**: ...
- **Action**: Add §X paragraph addressing X.

## Objection #2: ...
[etc., 10 total]

## Cross-cutting themes
[2-3 sentences on patterns across objections]
```
