---
date: 2026-05-24T12:00:00Z
agent: human
task_kind: framing_v2
tier: 3
auto_executed: false
human_approved: true
approver: [REDACTED]
cost_usd: 0
---

## What

Adopt v2 framing for the research project, with:
1. Refined motivation centered on Western-default-LLM blocker for non-Western
   enterprise deployment (`MOTIVATION_v2.md`).
2. Explicit KPI framework with hard acceptance numbers, severity bands, and
   failure-cascade rules (`KPI_FRAMEWORK.md`).
3. Three nested self-evaluation loops: per-task self-check, Writer-Critic,
   QA Meta + PI audit (`SELF_EVAL_LOOP.md`).
4. Two new agents added: `qa_meta` (hourly KPI monitor) and
   `principal_investigator` (daily research-integrity audit). Total agents: 8.
5. Documented deviations from Token Pirates proposal (`DEVIATIONS_FROM_PPT.md`)
   for inclusion in Methods.
6. ORBT integration plan with concrete API surfaces (`ORBT_INTEGRATION.md`).
7. Updated `config/rubric.yaml` and `prompts/writer.md` to enforce the
   quality bar set by COSE461 last-year top reports (Team 2, Team 4, Team 22).
8. Role split: Sunwoo owns all development; teammate (Josh) owns presentation.

## Why

- The original Token Pirates PPT framed motivation as "LLMs have cultural
  bias" — academically true but not commercially activating. The refined
  motivation makes the enterprise-deployment blocker explicit and ties
  the research directly to ORBT's product wedge. Reviewers (academic and
  industry) need to see the "so what" to take the contribution seriously.
- Without hard KPIs, the autonomous lab has no way to know when to stop
  polishing, when to escalate, when to drop scope. KPI_FRAMEWORK.md gives
  qa_meta agent the ground truth it needs to do its job.
- The original 6-agent design (data_steward, experiment_runner, analyst,
  writer, critic, librarian) handled per-task and per-draft quality, but
  had no system-level self-evaluation. The two new agents close that gap.
- Quality bar enforcement (rubric.yaml + writer.md) is necessary because
  last-year reports set a NeurIPS-style standard with 8-14 equations, 5+
  baselines, formal limitations. Without explicit encoding, the Writer
  agent might produce a lower-quality output the Critic doesn't catch.

## Source data

- Token Pirates PPT (10 slides, attached).
- Last-year top COSE461 reports: Team 2 (Dual-CoCoOp, 12p),
  Team 4 (HIES, 12p), Team 22 (ConRaGen, 10p).
- Sunwoo's stated requirements from 2026-05-24 conversation:
  motivation, KPIs, QA, self-eval loop, ORBT pipeline transfer,
  professor recognition.

## Reversibility

- All v2 documents are additive; v1 documents remain unchanged unless
  explicitly noted in the diff.
- Two new agents can be disabled via `config/agents.yaml` without
  affecting the existing six.
- Rubric tightening is reversible; previous version is in git history.

## Open Tier-3 items (Sunwoo must decide before W1)

- [ ] Confirm COSE461 AI usage policy from syllabus.
- [ ] Confirm IRB pathway for human evaluators.
- [ ] Confirm legacy model (Llama-3.1-8B) inclusion or drop.
- [ ] Confirm publication target (ACL Findings, ACL Industry, internal).
