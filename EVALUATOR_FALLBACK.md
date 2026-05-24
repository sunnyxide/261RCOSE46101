# Evaluator fallback ladder

> Human Korean evaluators are the gold standard for CAS measurement. They are
> also expensive, IRB-gated, and slow to recruit. This document defines the
> automatic tier that the lab uses when humans are unavailable, and the
> decision protocol QA Meta runs each Friday until W4.
>
> Owner: Sunwoo (decides) + qa_meta agent (proposes).

---

## The four tiers

| Tier | Evaluators | CAS measured by | ICC requirement | Paper-strength claim |
|------|------------|-----------------|------------------|----------------------|
| A | 15 × 200 personas | Native-speaker Likert direct | n/a (humans are ground) | "human-validated cultural authenticity" |
| B | 5 × 50 anchors + LLM panel | Isotonic-calibrated panel | ≥ 0.7 (panel) | "human-anchored, LLM-judged" |
| C | 0 + LLM panel | 4-model panel direct | ≥ 0.5 (panel) | "LLM-judged with inter-model agreement σ reported" |
| D | 0, panel disabled | CAS dropped | n/a | Paper reframed; HAD + PDI + JSD + BAS + Korean benchmarks (KoBBQ, CLIcK, HAERAE) carry the claim |

The panel itself is the same across B and C — what changes is whether we
apply isotonic calibration against a human anchor sample. See
`agents/shared/llm_judge_panel.py` for the panel implementation.

---

## Decision protocol

`agents/qa_meta.py:_assess_evaluator_tier()` runs each Friday until W4.

Inputs:

- `data/state/irb_status.yaml` — Sunwoo updates this weekly. Fields:
  `submitted_at`, `approved_at`, `recruitment_started_at`,
  `confirmed_evaluators`, `target_personas_per_evaluator`.
- `results/qa/judge_panel_dry_run.json` — most recent panel dry run.
  Fields: `icc`, `mean_cost_per_persona_usd`, `all_judges_responded`.

Decision tree:

```
if confirmed_evaluators >= 15 AND target_personas_per_evaluator >= 200:
    propose Tier A
elif confirmed_evaluators >= 5 AND target_personas_per_evaluator >= 50:
    propose Tier B
elif latest_panel_icc >= 0.5 AND all_judges_responded:
    propose Tier C
else:
    propose Tier D
```

After proposal, QA Meta:

1. Writes proposal to `decisions/<date>-evaluator-tier-proposal.md`.
2. Posts to `#orbt-research-lab` with rationale.
3. Waits 24 hours for Sunwoo `:white_check_mark:`. No reaction → default
   to whichever tier was proposed.
4. From W5 onward, the chosen tier is locked unless Sunwoo opens
   `decisions/<date>-evaluator-tier-override.md` explicitly.

---

## Why family diversity in the panel matters

The Tier C claim rests on the assumption that **shared blind spots between
judges show up as agreement on the wrong answer**, which isotonic
calibration (Tier B) or human anchors (Tier A) detect. If all four judges
shared a training-data distribution, the panel would be effectively one
judge with extra latency.

The four default judges in `llm_judge_panel.py`:

| Judge | Family | Pretraining bias hypothesized |
|-------|--------|-------------------------------|
| Claude Opus 4.7 | Anthropic | Anglo-academic, strong English-eval RLHF |
| GPT-5 | OpenAI | Anglo-mass-web, broad multilingual but English-anchored |
| Gemini 2.5 Pro | Google | Heavy multilingual pretraining, Western search corpus skew |
| Qwen 3.6-27B | Asian-prior | Significant Chinese / Korean / Japanese corpus weight |

Inter-family agreement at high score on a Korean-cultural item is much
stronger evidence than intra-family agreement. The Qwen judge in
particular is included specifically to break Western-default convergence.

If at any point Qwen becomes unavailable (model unsupported on Mac Mini,
inference too slow under load), replace with HyperCLOVA X if API access
is approved; otherwise the panel degrades to 3-of-4 and the paper must
state the limitation explicitly.

---

## Cost envelope per tier

For 4,800 personas (6 conditions × 4 backbones × 200 personas):

| Tier | Total CAS cost | Of which human stipends |
|------|----------------|------------------------|
| A | ~$3,200 | $3,000 (15 × $200) |
| B | ~$1,150 | $1,000 (5 × $200) + $150 panel |
| C | ~$150 | $0 + $150 panel |
| D | $0 | n/a |

Tier C panel cost is dominated by Opus + GPT-5 (~$0.025/persona × 4,800).
Qwen runs locally on Mac Mini and adds zero API cost. Gemini is the
cheapest of the cloud judges.

---

## Open questions for Sunwoo (W1 first-day)

1. **IRB submission window.** IRB approval can take 4-6 weeks. Submitting
   in W1 keeps Tier A on the table; skipping it locks us to Tier B or
   below from the start. Recommendation: submit immediately even if we
   end up taking Tier C — Tier A optionality has option value.
2. **HyperCLOVA X access.** Naver Cloud API key has ~1 week ETA. Adding
   HyperCLOVA as a fifth (Korean-pretrained) judge would meaningfully
   strengthen the Tier C claim. Recommendation: apply now in parallel.
3. **Recruitment channel.** Korea University students (fast, cheap, but
   demographically skewed toward young + urban + educated) vs Prolific
   (slow, more expensive, demographically balanced). Recommendation:
   Korea University for Tier B anchor pool, Prolific for Tier A if we
   reach it.
4. **Tier C budget.** $150 panel cost comes from the $400 envelope.
   Acceptable. No QLoRA reduction required.
