# HANDOFF — read this first

> Audience: the Claude Code session running on the Mac Mini (Hermes / OpenCloud / Claude Code).
> Goal: pick up this research project with full context, no further briefing.
> Time horizon: 8 weeks (W1 starts on first run of this lab).
> Operator on call: Sunwoo (sunny@tryorbt.com). Teammate (Josh) handles presentation only.

---

## 0. One-paragraph summary

We are building an autonomous research lab that produces a COSE461 final paper AND a production-ready ORBT product module. The paper asks whether *cultural knowledge-graph retrieval + demographic grounding + behavioral simulation* produces Korean consumer personas that are more culturally authentic than prompting alone, across model generations. The product asks whether the resulting pipeline can plug directly into ORBT's Hermes agent and OpenCloud workflow as a consumer-response prediction module for D2C brands targeting Korea.

Both objectives share the same experimental infrastructure. The lab runs 24/7 on the Mac Mini with AWS burst capacity, executes a 6-condition × 2-backbone factorial under tiered autonomy, and self-evaluates against KPI targets defined in `KPI_FRAMEWORK.md`.

---

## 1. Why this work exists (motivation)

Western-trained LLMs are not neutral substrates — they encode American individualist defaults along every dimension that matters for consumer behavior: how purchase decisions are made, who is consulted, how social proof is weighted, what "trust" looks like, how complaints surface. When a Korean D2C brand asks GPT-4 "what would my customer think of this campaign?", the answer is approximately what an American customer would think, dressed in Korean syntax.

Three concrete examples observed in ORBT production:
- Korean team-name suggestions that read as English-thinking-translated, not Korean-native.
- Hollow compliment patterns ("훌륭한 결정이네요") that violate efficient Korean communication norms.
- Reasoning traces showing English-first chain of thought, then translation.

KAIO benchmark (2026) confirms even frontier models leave ~37 points of headroom on hard Korean questions. CulturalBench shows best LLM at 61.5% vs human 92.4%. Cross-model error correlation ρ > 0.97 — every Western-trained model fails in the same direction, which is a calibration artifact, not noise.

**Business significance.** ORBT sells consumer intelligence and simulation to D2C brands. The single largest blocker to non-US market expansion of LLM-based products is exactly this gap: enterprises cannot trust Western-defaulting models to predict customer response in their markets. Solving this — even partially, even for one market — is a wedge.

**Academic significance.** Prior work measures bias (CulturalBench, KoBBQ) or aligns values (CultureLLM, CAReDiO). No one has built a pipeline that produces *culturally authentic, demographically grounded, behaviorally validated* consumer personas as a deployable module. We do.

See `MOTIVATION_v2.md` for the long form, with citations, that the Writer agent must use.

---

## 2. Research questions and hypotheses

**RQ1.** Does cultural knowledge-graph retrieval, when combined with demographic grounding, produce more culturally authentic Korean consumer personas than prompting alone?

**RQ2.** Does this effect persist across model generations (Qwen3.6-27B, Gemma 4 26B MoE, Llama-3.1-8B legacy, GPT-4o-mini, GPT-5) and parametric vs retrieval injection regimes (prompted, QLoRA fine-tuned, retrieval-augmented)?

**RQ3.** Do statically-measured authenticity gains translate into behaviorally-authentic group dynamics under D2C scenarios (conformity cascades, authority adoption, group consensus)?

**Hypotheses.**
- H1: Full-stack condition (Nemotron + CultureBank + LightRAG) outperforms Vanilla on CAS, HAD, PDI, JSD with effect size d > 0.5.
- H2: Retrieval benefits are inversely correlated with model capability (smaller models benefit more in absolute terms; SOTA models still benefit in CAS).
- H3: Static authenticity gains correlate (Spearman ρ > 0.6) with behavioral authenticity gains measured in OASIS simulations.
- H4: QLoRA fine-tuning on synthetic Korean personas (Nemotron + CultureBank) closes ≥50% of the gap between Vanilla and full-stack-retrieval, providing a deployable parametric alternative.

If H1 holds: ORBT product positioning is validated.
If H2 holds: SOTA-scaling-solves-culture critique is rebutted.
If H3 holds: BAS becomes a defensible new metric for the field.
If H4 holds: ORBT has a path to on-prem deployments without per-call API spend.

---

## 3. Hard KPIs / acceptance gates

Read `KPI_FRAMEWORK.md` for the full table. Selected highlights enforced by `agents/qa_meta.py`:

| Layer | KPI | Target | Failure action |
|-------|-----|--------|----------------|
| Static authenticity | CAS (full stack vs vanilla) | +0.8 Likert points, p < 0.01 | Escalate to Sunwoo |
| Demographic distribution | JSD vs WVS Wave 7 Korea | < 0.10 in full stack | Re-sample personas |
| Behavioral authenticity | CCR / AAS / GCS deviation from KOSIS+Naver ground truth | < 15% in full stack | Add scenario, re-run |
| Diversity | PDI (full stack) | > Vanilla, no stereotyping cluster > 25% | Resample with stricter quota |
| Reproducibility | All artifacts have manifest + DVC hash | 100% | Block report draft |
| Cost | Total spend through W8 | < $400 USD | Hard kill at $30/day |
| Paper quality | Critic-pass on all autonomous sections | ≥ 0.85 score, ≤ 3 rounds | Escalate to human author |
| ORBT integration | Hermes wrapper passes integration test | All 6 conditions accessible via API | Defer ORBT release |

If any **red KPI** is on track to miss by W4, QA Meta-agent forces a scope reduction (e.g., drop legacy model condition) rather than miss the deadline.

---

## 4. The autonomous loop (read this if you're confused about what to do)

### 4.1 Three nested feedback loops

```
┌──────────────────────────────────────────────────────────────────────┐
│  Loop A — Per-task self-check (every task, ~seconds)                  │
│  Every domain agent emits {confidence, reasoning} with its output.   │
│  If confidence < 0.7, auto-enqueue a Critic review BEFORE commit.    │
└──────────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Loop B — Writer-Critic adversarial loop (per draft, ~minutes)        │
│  Writer drafts → Critic reviews → Writer revises (max 3 rounds).     │
│  After round 3, escalate to Sunwoo regardless of state.              │
└──────────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────────┐
│  Loop C — QA Meta + PI audit (hourly + daily)                         │
│  QA Meta: are we on track for KPIs? Re-prioritize queue.             │
│  PI:      is the RQ still being answered? Flag drift.                │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.2 Agent roster (8 total now — two added in v2)

| Agent | Role | New in v2? |
|-------|------|------------|
| data_steward | Layer 1-2 ingestion, schema validation | — |
| experiment_runner | OASIS sims, QLoRA jobs | — |
| analyst | Static + dynamic metric computation | — |
| writer | Section drafts on `draft/agent-*` branches | — |
| critic | Adversarial reviewer with separate model | — |
| librarian | Lineage, manifests, daily digest | — |
| **qa_meta** | Hourly KPI projection, queue re-prioritization | **yes** |
| **principal_investigator** | Daily research-integrity audit, hypothesis drift detection | **yes** |

### 4.3 Self-check protocol (every domain agent)

Before submitting output, every domain agent runs an internal self-check (one extra LLM call, cheap):

```
SELF-CHECK PROMPT (for each agent's own output):

You just produced [task output]. Before submitting:
1. Does this output address the literal task asked, not an adjacent one?
2. Is every numerical claim traceable to a file you wrote or read?
3. Are there obvious failure modes you didn't address?
4. What is your confidence (0.0-1.0) and why?

Output JSON: {"confidence": float, "issues_self_identified": [...], "submit": bool}
If submit=false, do not commit; instead enqueue a follow-up task with corrections.
```

This is cheap insurance. Single agent self-eval catches ~60% of issues before they hit the Critic. Without it, every issue costs a full Writer-Critic round.

---

## 5. Deviations from the Token Pirates PPT (must document in paper)

The original proposal (Token Pirates) defined a Korea+Japan, 5-condition, GPT-4o-mini-only study with static metrics. The current plan deviates on six dimensions. Every deviation must be in `DEVIATIONS_FROM_PPT.md` with rationale; the Writer pulls from that file to produce the Methods "design evolution" subsection.

| # | Original | v2 | Why |
|---|----------|----|----|
| 1 | Korea + Japan | Korea only | Depth > breadth. WVS Wave 7 Korea + KOSIS gives behavioral ground truth Japan can't match at this scale. |
| 2 | 5 conditions | 6 conditions | Added Nemotron-only baseline to isolate demographic vs cultural contribution. |
| 3 | GPT-4o-mini only | 4 backbones (GPT-4o-mini, GPT-5, Qwen3.6-27B, Gemma 4 26B MoE), +1 legacy (Llama-3.1-8B) | RQ2 requires generational covariate. |
| 4 | Static metrics only | Static (CAS, HAD, PDI, JSD) + Dynamic (BAS = CCR ⊕ AAS ⊕ GCS) | Korean culture is relational; static measurement of an individual persona misses the unit of analysis. |
| 5 | No fine-tuning | QLoRA on Nemotron+CultureBank for ≥1 backbone | AWS credits ($195.84 × 2) made this affordable; H4 requires it. |
| 6 | Manual orchestration | 8-agent autonomous lab with tiered autonomy | 2-person team, 8-week budget; methodology itself becomes a contribution. |

All deviations preserve the original RQ (KG retrieval vs prompting). None of them invalidate the PPT's framing; they extend it.

---

## 6. ORBT integration plan

Read `ORBT_INTEGRATION.md` for the full plan. Summary:

- **Hermes agent** (ORBT's consumer-intelligence agent) gets a new `predict_consumer_response(brand, campaign, market="KR")` tool that delegates to our pipeline.
- **OpenCloud** (ORBT's pipeline workflow product) gets a new `cultural-persona-grounded-simulation` block that maps to our OASIS harness.
- **persona_mapping module** in production (currently returning empty) gets backed by the LightRAG KG built by `data_steward` + `experiment_runner`.
- **intel_v1** knowledge graph schema gains a `cultural_descriptor` node type sourced from CultureBank-Korean subset.

ORBT integration is **Tier 3 / human-only** during W1-W7. In W8, after paper is final, Sunwoo flips an integration switch and the production code repo (separate Git remote) imports from this repo's package.

---

## 7. First-run checklist (the only thing you need to do today)

Run these in order on the Mac Mini. Stop and ping Sunwoo on Slack if any step fails.

```bash
cd ~/projects/orbt-research-lab

# 1. Confirm policy gate
make verify-policy
# If this fails: read COSE461 syllabus, confirm AI usage is allowed with disclosure,
# set COURSE_AI_POLICY_VERIFIED=true in .env, re-run.

# 2. Bring up services + Python env
make setup

# 3. Smoke-test Layer 1 ingestion (no autonomous side effects)
python notebooks/01_layer1_smoke_test.py

# 4. Manual WVS Wave 7 fetch (TOS-restricted, can't automate)
#    Download from worldvaluessurvey.org → data/raw/wvs7/source/
#    Re-run smoke test after.

# 5. Verify Slack bot
make daily-digest
# Confirm #orbt-research-lab gets a "first digest" message.

# 6. Seed the W1 queue
python scripts/seed_task_queue.py

# 7. Run the queue ONCE manually before going autonomous (sanity check)
python -m orchestrator.scheduler run  # Ctrl+C after first task completes

# 8. Inspect: did the first task produce a manifest? A decision log entry? Cost record?
ls data/raw/nemotron/$(date -u +%Y-%m-%d)/
ls decisions/$(date -u +%Y-%m-%d)*
make status

# 9. If everything looks good, install the launchd service for 24/7 operation
bash scripts/launchd_install.sh

# 10. Watch the next 4 hours. If status is healthy after 4h, mark step complete in TASKS.md.
```

---

## 8. What you (Mac Mini Claude Code) should NOT do

- **Do not write the methods section.** Methods is human-authored. Critic enforces this.
- **Do not push to `main`.** All Writer agent output stays on `draft/agent-*` branches.
- **Do not modify `decisions/2026-05-24-autonomy-architecture.md`** or any file in `decisions/` retroactively.
- **Do not exceed daily budget cap.** If you see `is_within_daily_limit()` return false, halt and alert.
- **Do not bypass the Critic for Writer output.** Even if Writer self-reports confidence 1.0.
- **Do not modify the research questions in this file** without Tier-3 human approval logged in `decisions/`.
- **Do not invent citations.** If a paper isn't in `bibliography.bib`, mark `[TODO citation: <topic>]` and queue a lit-search task.

---

## 9. Open questions parked for Sunwoo

These cannot be resolved without him; do not block on them.

1. **Final number of human evaluators.** Plan assumes 15 Korean evaluators × 200 personas. If IRB delays, fall back to 5 evaluators × 50 personas with adjusted statistical analysis. Decide by end of W2.
2. **Legacy model inclusion.** Llama-3.1-8B as the "5th backbone" adds 25-30 GPU hours. Drop if W4 budget burn is > $300.
3. **D2C scenario corpus author.** Should scenarios be authored by Sunwoo from KOSIS or by the data_steward agent with human review? Default: human, with agent providing first drafts.
4. **Conference target.** ACL Findings vs ACL Industry Track vs internal ORBT memo. Affects format and deadline pressure. Decide by W6.

---

## 10. Files you should know about

```
HANDOFF.md                          ← you are here
MOTIVATION_v2.md                    ← long-form motivation, used by Writer
KPI_FRAMEWORK.md                    ← all targets, gates, fail actions
SELF_EVAL_LOOP.md                   ← the three nested feedback loops
DEVIATIONS_FROM_PPT.md              ← what we changed and why
ORBT_INTEGRATION.md                 ← product transfer plan
SETUP.md                            ← first deployment runbook
README.md                           ← architecture overview
decisions/                          ← every Tier 1/2 action logged here
prompts/                            ← versioned agent system prompts
config/rubric.yaml                  ← course rubric, enforced by Critic
config/models.yaml                  ← model registry
config/agents.yaml                  ← agent permissions, autonomy tier
reports/style_guide.md              ← Writer must follow
reports/AI_USAGE_DISCLOSURE.md      ← appendix of final paper
```

End of HANDOFF.
