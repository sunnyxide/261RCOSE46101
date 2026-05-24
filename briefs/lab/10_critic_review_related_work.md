# Critic review — paper Related Work draft

**Origin**: brief 08 (paper_related_work_draft) produced a Writer draft of
Related Work. Same Loop B Critic protocol as `09_critic_review_intro.md`.

**Goal**: `results/hermes_outputs/critic_review_related_work.md`.

---

## Inputs

1. `results/hermes_outputs/08_paper_related_work_draft.md`
2. `reports/bibliography.bib`
3. `MOTIVATION_v2.md` §2
4. `HANDOFF.md` §8
5. `reports/style_guide.md`

## Critique dimensions (same as brief 09)

A. Citation correctness (0.25) — every `[bibkey]` exists; no invented
   work; `[TODO citation]` properly tagged
B. Numerical traceability (0.20) — no orphan numbers in cited-work
   descriptions
C. Scope discipline (0.20) — Related Work talks about *prior work* and
   how *our work differs*. NOT a place to summarize our own methods.
D. Position-statement quality (0.15) — each subsection ends with a clear
   "what's missing → what we add" sentence?
E. Coverage balance (0.10) — three buckets (measurement, alignment,
   persona) each get ~equal treatment? No single citation overweighted?
F. Style + voice (0.10) — same rules as Intro brief

## Output structure

Same as `09_critic_review_intro.md` — markdown with per-dimension scoring
table, severity-sorted issues list, "what it does right" section, and
research_v2 5-slot meta footer.

## Required meta footer

```
[meta]
verifiability_signal: high|medium|low
critic_pass: true|false
recommended_round: revise|publish|escalate
n_invented_citations_found: <int>  (must be 0 for pass)
```
