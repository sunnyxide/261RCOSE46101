# Critic review — paper Introduction draft

**Origin**: brief 07 (paper_intro_draft) produced a Writer-authored draft of
the Introduction. Per HANDOFF.md §4.2, the Critic agent runs against Writer
output to catch hallucinated citations, orphan numerical claims, style
drift, and methods/results bleed.

**Goal**: produce `results/hermes_outputs/critic_review_intro.md` — a
structured critique of the Introduction draft.

**Why this matters**: Writer-Critic adversarial loop is Loop B in the
self-eval architecture. Critic uses a different reasoning angle than Writer
on the same draft to surface what Writer's confidence missed.

---

## Inputs you must read

1. `results/hermes_outputs/07_paper_intro_draft.md` — the draft to review
2. `reports/bibliography.bib` — every citation must be in here, no exceptions
3. `MOTIVATION_v2.md` §1-§2 — claims must align with this canonical motivation
4. `HANDOFF.md` §8 — list of things Writer is forbidden to do (e.g., draft
   methods, push to main, invent citations)
5. `reports/style_guide.md` — voice and tense rules

## Critique dimensions (score each)

For each dimension, give a 0-1.0 score and a 1-3 sentence justification.

### A. Citation correctness (weight 0.25)
- Every `[bibkey]` exists in bibliography.bib?
- Every `[TODO citation: ...]` is marked for follow-up rather than left as
  fake citation?
- No invented author names or paper titles?

### B. Numerical-claim traceability (weight 0.20)
- Every quantitative claim points to either a `[bibkey]` or a
  `[results/file.json]` path?
- No orphan numbers (e.g., "37 points of headroom" must trace to
  `chiu2024culturalbench` or `[TODO]`)?

### C. Scope discipline (weight 0.20)
- Does the draft stay in Introduction territory (motivation + contribution
  + roadmap) and NOT bleed into Methods or Results?
- Any sentence that describes "what we did" with specific experimental
  parameters is methods territory — flag it.

### D. Hypothesis fidelity (weight 0.15)
- H1-H4 stated correctly (matching HANDOFF.md §2)?
- Metrics named correctly (CAS, HAD, PDI, JSD for static; CCR/AAS/GCS/BAS
  for dynamic)?

### E. Korean-specificity (weight 0.10)
- Does the Introduction concretely ground in Korean market signals (KOSIS,
  Naver, KOFICE) rather than abstract "non-Western markets"?

### F. Style + voice (weight 0.10)
- Tense: present for our work, past for prior work?
- No marketing voice?
- Cohesive prose, not bulleted lists?

## Output structure

```markdown
# Critic review — paper Introduction draft

**Reviewed file**: results/hermes_outputs/07_paper_intro_draft.md
**Critic timestamp**: <UTC>
**Reviewer model**: mimo-v2.5-pro

## Overall pass score: <0.00-1.00>

(threshold per KPI_FRAMEWORK.md: ≥ 0.85 = pass)

## Per-dimension scores

| Dimension | Weight | Score | Notes |
|---|---|---|---|
| A. Citations | 0.25 | <s> | <1 sentence> |
| ... | ... | ... | ... |

**Weighted total**: <0.00-1.00>

## Issues (severity-ordered)

### Critical (block-pass)
1. <issue>
   - Location in draft: <line range or quote>
   - Recommended fix: <what Writer should change>

### Major (revision needed)
1. ...

### Minor (suggestions)
1. ...

## What the draft does right (for next-round preservation)

- <thing 1>
- <thing 2>
```

## Required meta footer

```
[meta]
verifiability_signal: high|medium|low
critic_pass: true|false  (true iff weighted total ≥ 0.85 AND no critical issues)
recommended_round: revise|publish|escalate
```

## Hard constraints

- Critic does NOT rewrite. Report only.
- Critic NEVER approves a draft with any critical-severity issue, regardless
  of overall score.
- If `07_paper_intro_draft.md` doesn't exist or is empty, output a single
  block stating "BLOCKED: prerequisite missing" — do NOT fabricate a review.
