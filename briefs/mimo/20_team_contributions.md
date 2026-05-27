# Brief 20 — Appendix: Team contributions (NOT in 8p limit)

## Context
COSE461 multi-person team requires "Appendix: Team contributions" section. Template: "If you are a multi-person team, you can write a brief summary of what each team member did for the project (about 1 or 2 sentences per person). For almost all teams, it will have no effect (i.e. team members all receive same grade), but for teams with considerably unequal contribution, I may investigate and/or give different grades to team members."

## Team
- **주선우 (Sunwoo, 2023320312)** — Team lead, GitHub: sunnyxide
- **김민수 (Min-su, 2022320337)** — Team member, GitHub: ELONFLAME

## Task

Draft a **balanced contributions appendix** (2 short paragraphs, 1-2 sentences per person + 1 joint sentence).

Suggested contribution allocation (since actual work distribution is fluid — adjust based on what fits):

**주선우 (Sunwoo)**:
- Project conception and research direction
- AWS instance setup and overnight pipeline orchestration
- Cultural data dataset construction (CultureBank filtering, Nemotron processing)
- Cross-cultural evaluation framework (cross_cultural_eval.py, GlobalOpinionQA + BLEnD)
- Final report writing and editing

**김민수 (Min-su)**:
- QLoRA training implementation (cultural_qlora_train.py)
- Phase 1 baseline benchmarking (KoBBQ, KMMLU, HAE-RAE, CLIcK loaders + scoring)
- Hofstede dimension ablation experiments
- Multi-cultural unified adapter (Run-M) training
- Code review and reproducibility verification

**Joint**:
- Result analysis and interpretation
- Paper section drafting and consolidation

## Output

```markdown
# Appendix A: Team Contributions

**주선우 (Sunwoo)** [2023320312]: [1-2 sentences]

**김민수 (Min-su)** [2022320337]: [1-2 sentences]

**Joint work**: [1 sentence]
```

Keep tone neutral and equitable — explicit asymmetry can affect grading.

Also generate a SHORT alternative version (1 paragraph total) in case we want to fold contributions into a smaller appendix.
