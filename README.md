# ORBT Korean Persona Research Lab

Autonomous research lab producing both a COSE461 academic paper and a deployable
ORBT product module on culturally-authentic Korean consumer persona generation.

**Team:** 김민수 (2022320337), 주선우 (2023320312)

**Entry points (read in order):**

1. `HANDOFF.md` — first-run checklist, RQs, KPIs, agent roster
2. `MOTIVATION_v2.md` — long-form motivation with citations
3. `KPI_FRAMEWORK.md` — hard targets, severity bands, failure actions
4. `AUTONOMOUS_INTEGRATION.md` — Hermes + Ralph + AWS + OpenClaw layering
5. `AWS_PERFORMANCE_PLAN.md` — L4-optimized training schedule (W3-W4)
6. `SELF_EVAL_LOOP.md` — three nested feedback loops (Loop A/B/C)
7. `EVALUATOR_FALLBACK.md` — A/B/C/D tier ladder for IRB uncertainty
8. `DEVIATIONS_FROM_PPT.md` — what changed from Token Pirates v1 and why
9. `ORBT_INTEGRATION.md` — product transfer to Hermes + OpenCloud + intel_v1

**Decisions** (Tier 1/2 logs, append-only): `decisions/`

**Status (2026-05-24):** instance setup complete on NxtGen g6.xlarge (L4 24GB),
Qwen2.5-0.5B smoke test passed, Qwen2.5-14B-Instruct designated as primary
QLoRA target. 30-min healthcheck cron active on the operator Mac.

This repo will be pushed in full once `gh auth login` is set up for the
`sunnyxide` account on the operator Mac. Until then, the local checkout at
`/Users/orbt/Desktop/orbt/projects/orbt-research-lab/` is the canonical copy.
