# ORBT Research Lab — Autonomous Korean Persona Research Infrastructure

24/7 autonomous research lab running on Mac Mini M4 Pro (48GB) with AWS burst capacity, conducting the Cultural KG Retrieval × Korean Persona Generation study for COSE461 and ORBT R&D.

> **NEW HERE? Read `HANDOFF.md` first.** It is the canonical self-contained brief for the Mac Mini Claude Code session and any new collaborator. Everything below is supporting detail.

## Why this exists (90-second version)

LLMs are Western-default. Korean D2C enterprises cannot trust them for consumer modeling because the models think in American patterns dressed in Korean syntax. CulturalBench reports 61.5% best LLM vs 92.4% human; KAIO 2026 shows GPT-5 at 62.8 — 37 points of headroom on the frontier model. Prior work measures the gap or aligns values; nobody has produced a deployable culturally-grounded consumer-persona pipeline. We do, and we transfer it directly into ORBT's Hermes agent and OpenCloud workflow.

The lab serves two outputs in one campaign: an academic paper (COSE461) and a production module (ORBT). See `MOTIVATION_v2.md` for the long form, `KPI_FRAMEWORK.md` for measurable targets, and `ORBT_INTEGRATION.md` for product transfer.

## What this is

A **tiered-autonomy** research orchestration system. Eight specialized agents collaborate to:
1. Pull and validate cultural/demographic data (Nemotron-Personas-Korea, CultureBank, KOSIS, WVS Wave 7).
2. Build a Korean cultural knowledge graph (LightRAG + Neo4j).
3. Generate Korean consumer personas under 6 ablation conditions × 4-5 model backbones.
4. Simulate persona behavior under 50 D2C scenarios via OASIS.
5. Compute static (CAS, HAD, PDI, JSD) and dynamic (CCR, AAS, GCS, BAS) metrics.
6. Draft the final paper sections with adversarial Writer-Critic loops.
7. Audit own work hourly (QA Meta) and daily (PI), escalating drift to humans.
8. Report status to humans daily and request approval for non-trivial decisions.

**Important constraints:**
- All "Tier 3" actions (research questions, methodology, final merge to `main`) require explicit human approval.
- Writer can only commit to `draft/agent-{run_id}` branches, never `main`.
- Daily cost cap kills the system if exceeded. No silent budget run-away.
- Every decision is logged in `decisions/` with full justification.
- Course AI policy compliance is verified before W1 execution.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│   MAC MINI (always-on)                                    │
│                                                           │
│   orchestrator/scheduler.py  ← launchd service           │
│              │                                            │
│              ├── spawns ───→ agents/data_steward.py      │
│              ├── spawns ───→ agents/experiment_runner.py │
│              ├── spawns ───→ agents/analyst.py            │
│              ├── spawns ───→ agents/writer.py             │
│              ├── spawns ───→ agents/critic.py             │
│              ├── spawns ───→ agents/librarian.py          │
│              ├── spawns ───→ agents/qa_meta.py        (v2)│
│              └── spawns ───→ agents/principal_investigator.py (v2)│
│                                                           │
│   Persistent state:                                       │
│     - Git repo (this directory)                           │
│     - SQLite (orchestrator/state.db)                      │
│     - Neo4j container (LightRAG KG)                       │
│     - DVC-tracked data/                                   │
│                                                           │
│   Human interface:                                        │
│     - Slack bot (#orbt-research-lab)                      │
│     - 07:00 KST PI audit + 08:00 KST daily digest         │
│     - Streamlit dashboard at lab.tryorbt.com:8501         │
│                                                           │
└──────────────┬───────────────────────────────────────────┘
               │
               ├── AWS g6e.xlarge (burst: QLoRA, batch GPU inference)
               └── External APIs (OpenAI, Anthropic, Alibaba)
```

## Three nested feedback loops (see `SELF_EVAL_LOOP.md`)

- **Loop A — per-task self-check**: every domain agent runs `confidence + traceability` self-eval before commit. Catches ~60% of issues cheaply.
- **Loop B — Writer-Critic adversarial**: different model families (Writer = Claude Sonnet 4.6, Critic = GPT-5) review drafts adversarially, max 3 rounds.
- **Loop C — QA Meta + PI audit**: hourly KPI projections + daily research-integrity audit. Catches drift no per-task review can see.

## Tiered autonomy

| Tier | Authority | Actions | Human |
|------|-----------|---------|-------|
| **1** | Full auto | Data fetch, schema validation, simulation runs, metric computation, daily digest, queue reordering | Notified |
| **2** | Auto-propose | New experiment configs, report section drafts (branch only), bug fixes, lit search summaries, QA Meta config proposals | Async approval via Slack 👍/👎 within 24h |
| **3** | Human-only | RQ/hypothesis changes, methodology changes, main-branch merge, IRB, submission, ORBT production integration | Required, in person |

## Quickstart

```bash
# On Mac Mini
git clone <repo> orbt-research-lab && cd orbt-research-lab
cp .env.example .env  # fill in API keys
make setup            # installs deps, pulls models, builds Neo4j
make verify-policy    # confirms COSE461 AI usage policy has been reviewed
make first-run        # dispatches Layer 1 data collection as first autonomous task
make status           # prints current queue and budget state
```

## Repository structure

```
orbt-research-lab/
├── HANDOFF.md                   # ← Mac Mini Claude Code reads this first
├── MOTIVATION_v2.md             # long-form motivation, used by Writer
├── KPI_FRAMEWORK.md             # measurable targets, gates, fail actions
├── SELF_EVAL_LOOP.md            # three nested feedback loops
├── DEVIATIONS_FROM_PPT.md       # what we changed from original PPT and why
├── ORBT_INTEGRATION.md          # product transfer plan
├── SETUP.md                     # first deployment runbook
├── orchestrator/                # Task queue, scheduler, budget, resource router
├── agents/                      # Eight specialized agents (Claude Agent SDK)
├── prompts/                     # System prompts for each agent (versioned)
├── config/                      # Agent configs, model registry, course rubric
├── data/                        # Raw + processed datasets (DVC-tracked)
├── decisions/                   # Decision log (every Tier 1/2 action logged here)
├── reports/                     # Paper drafts, presentation, ORBT internal memo
├── scripts/                     # One-off utility scripts
├── notebooks/                   # Exploratory analysis (not autonomous)
├── docker/                      # docker-compose, Dockerfiles
├── tests/                       # Critic agent's offline test fixtures
├── Makefile
├── pyproject.toml
```

## Stop button

```bash
make emergency-stop      # halts all agents, releases AWS, sends Slack alert
```

Or send `!stop` in the Slack channel. All agents poll for this signal between tasks.

## Quality bar

This project explicitly aims to exceed last year's top COSE461 reports:
- Team 2 (Dual-CoCoOp, 8p): 14 equations, 5 datasets, 5 baselines.
- Team 4 (HIES, 12p): 7 figures, α ablation, FLOPs analysis.
- Team 22 (ConRaGen, 10p): 5 equations, 4 baselines, qualitative comparison.

Our differentiators (none of these teams had): autonomous research methodology as contribution, dynamic behavioral metrics (BAS), ORBT product transfer surface.

See `config/rubric.yaml` for exact enforcement; the Critic agent uses it to gate every draft.
