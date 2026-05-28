# Autonomous integration — Hermes + OpenClaw + Ralph Loop + AWS QLoRA

> Date: 2026-05-24
> Status: architecture decision (Tier-2, needs Sunwoo ack before any worker boots)
> Supersedes: HANDOFF.md §7 (which assumed a clean Mac Mini install). This
> document is what actually runs.

The question this answers: *can we use the existing autonomous infrastructure
— Hermes overnight tmux sessions, OpenClaw research_v2 prompt standard,
Ralph Loop parallel dispatch, and the COSE461 AWS credit pool — to run the
research lab end-to-end with minimal new code?*

Short answer: **yes, by layering them**. The lab scheduler is the
research-task-level orchestrator. Hermes / Ralph / AWS are the worker
substrate it dispatches into. None of them get replaced; they get wrapped.

---

## 1. Layer cake

```
┌────────────────────────────────────────────────────────────────────────┐
│ Lab scheduler — orchestrator/scheduler.py                              │
│   • Sequences W1-W8 research plan                                       │
│   • Enforces budget caps, tier autonomy, decision logging               │
│   • Reads agents/qa_meta.py + agents/principal_investigator.py audits   │
│   • Idempotent queue (sqlmodel) survives reboots                        │
└──────────────────────────────┬─────────────────────────────────────────┘
                               │
        ┌──────────────────────┼───────────────────────┬────────────────┐
        ▼                      ▼                       ▼                ▼
┌─────────────────┐ ┌──────────────────┐ ┌─────────────────┐ ┌─────────────┐
│ HermesWorker    │ │ RalphDispatcher  │ │ AWSQLoRAWorker  │ │ OpenClaw    │
│ shared/hermes_  │ │ scripts/ralph_   │ │ shared/aws_     │ │ research_v2 │
│ worker.py       │ │ dispatch.sh      │ │ qlora.py        │ │ prompt fmt  │
│                 │ │                  │ │                 │ │             │
│ Long-running    │ │ Batch fan-out:   │ │ GPU training:   │ │ Used by     │
│ single-agent    │ │ 4,800 personas × │ │ 1-2 QLoRA runs  │ │ writer.py + │
│ tasks (writer,  │ │ 4 judges = 19.2k │ │ on g5.2xlarge   │ │ critic.py   │
│ critic, lit     │ │ judgments in N   │ │ ~12 GPU-hours   │ │ outputs;    │
│ search, MEAS    │ │ parallel cores   │ │ each, ~$15-30   │ │ self_verify │
│ mapping)        │ │                  │ │                 │ │ auditor     │
│                 │ │                  │ │                 │ │ pass req'd  │
│ Cost: Plan      │ │ Cost: Plan       │ │ Cost: AWS       │ │             │
│ endpoint, ~$2-5 │ │ endpoint × N,    │ │ instance hours, │ │             │
│ per task        │ │ ~$0.03/judgment  │ │ $1.21/hr        │ │             │
└─────────────────┘ └──────────────────┘ └─────────────────┘ └─────────────┘
```

The lab scheduler decides *what* to run. The workers decide *how* — the
adapter layer (`agents/shared/`) hides Hermes / Ralph / AWS specifics
from the scheduler.

---

## 2. Why each substrate is where it is

### 2.1 Hermes for long-running single-agent work

Hermes already runs on this Mac via tmux + docker. Provider override pattern
is known (`--provider openai -m gpt-5.4`, see
[[feedback-hermes-provider-override]] memory). Docker mount path is known
(`/Users/orbt/Desktop/orbt → /workspace/orbt`, see
[[orbt-overnight-orchestration]] memory).

What Hermes is good at: tasks that need a single agent thinking for 5-30
minutes with complex context. Examples in this lab:

- writer.py drafting a Methods section pulling from `decisions/` + `results/`
- critic.py adversarial review against bibliography.bib
- librarian.py compiling the daily digest
- The MEAS-mapping spec task (R4 mitigation) — needs cross-source reasoning

What it's *not* good at: tight parallel loops with thousands of
independent items. Hermes is designed for serial deep reasoning, and
contention on the Plan endpoint shows up when you fan out > 8 cores
(observed at 4 cores, headroom unclear).

### 2.2 Ralph Loop for parallel batch jobs

The 4,800-persona × 4-judge judgment workload (Tier C panel CAS scoring)
is the canonical batch job. 19,200 judgments serially at ~10 seconds each
= 53 hours. Ralph Loop with N=8 cores brings it to ~7 hours wall clock
within the same Plan endpoint cost. Mac Mini's 64GB unified memory
supports this without thrashing.

Ralph Loop rules from [[feedback-ralph-loop-tuning]] still apply:
- `--max-tokens 24000` minimum (mimo-v2.5-pro reasoning overhead)
- `mkdir -p $LAB_ROOT/cores/<id>` BEFORE spawn
- PROMPT must have "No tool access" line — judges are completion-mode
- `verifiability_signal:` parsed line-anchored from `[meta]` footer

### 2.3 AWS QLoRA worker for GPU training

The Korea University TA allocated AWS instance credits at $97.92 × 2 per
person. Team has 2 members (Sunwoo + Kim Min-su), giving $391.68 total.

Cost arithmetic for a QLoRA run:
- g5.2xlarge: 1× A10G 24GB, $1.21/hr on-demand US-West-2
- QLoRA on Qwen3.6-27B with Nemotron+CultureBank training set (≈ 50K pairs):
  ~10-12 GPU-hours per run
- Per-run cost: ~$15
- Budget: ~26 QLoRA runs feasible. We plan 1-2 runs, leaving 90%+ buffer.

Spot pricing brings g5.2xlarge to ~$0.40/hr if Sunwoo accepts interruption.
For QLoRA with checkpoint-every-200-steps this is safe; we recover from a
killed instance in ~5 min.

Mac Mini does NOT have a GPU capable of QLoRA on a 27B model. AWS is the
only path for H4 (the QLoRA-vs-retrieval comparison).

### 2.4 OpenClaw research_v2 as the output standard

Every Writer / Critic / lit-search output written to disk uses the 5-slot
schema from `overnight-agents/prompts/openclaw/research_v2.md` and ends
with the `[meta]` footer. Reason: the existing
`orbtCS/scripts/guards/check_research_sources.py` and `check_self_verify.py`
guards already parse this footer. We get free verifiability gating
without writing new code.

Concretely, writer.py's system prompt loads research_v2.md verbatim and
appends "your output is a paper section; the 5-slot rule applies to every
empirical claim in your draft." Critic agent runs the same auditor logic
that orbtCS overnight cycles use.

---

## 3. The end-to-end research loop

For a single research cycle (one tick of the scheduler):

```
1. Scheduler dequeues highest-priority task per orchestrator/router.py policy.
2. Router inspects task.kind to pick the worker:
     • layer1_data_collection      → data_steward.py (local Python, no LLM)
     • validity_spec               → HermesWorker (single deep agent task)
     • paper_section_draft         → HermesWorker, writer.py prompt + research_v2
     • paper_section_critique      → HermesWorker, critic.py prompt, different model
     • static_metric_compute       → analyst.py (local Python, pandas/polars)
     • dynamic_sim_run             → experiment_runner.py → OASIS local
     • qlora_train                 → AWSQLoRAWorker → g5.2xlarge → S3 → DVC
     • batch_persona_judgment      → RalphDispatcher → N cores × research_v2
     • lineage_audit / daily_digest→ librarian.py (local Python)
3. Worker runs task, returns artifact paths + cost_usd to scheduler.
4. Scheduler records cost (budget.py), updates queue state, runs Loop A
   self-check on agent output, optionally enqueues correction.
5. Every hour: qa_meta.py tick. Every 24h: principal_investigator.py audit.
6. Sunwoo's Friday review reads the past week's QA reports + PI audits.
```

The scheduler doesn't know whether it's calling Mac local Python, Hermes,
Ralph, or AWS. The router has that knowledge. New worker types are added
by registering a router entry — no scheduler changes.

---

## 4. What's already wired and what isn't

| Component | State | What's needed |
|-----------|-------|---------------|
| `orchestrator/scheduler.py` | ✅ exists (226 lines) | Verify router dispatch — see below |
| `orchestrator/router.py` | ✅ exists (86 lines) | Add new worker types |
| `agents/shared/hermes_worker.py` | ❌ stub needed | Build: subprocess wrapper, model override, research_v2 prompt loader |
| `scripts/ralph_dispatch.sh` | ❌ stub needed | Adapt parallel_orchestrator.sh for judge panel workload |
| `agents/shared/aws_qlora.py` | ❌ stub needed | Build: boto3, SSH, S3 sync, cost guard |
| Existing Hermes infra | ✅ on Mac at `/Users/orbt/Desktop/orbt/hermes-agent/` | None — used as-is |
| Existing Ralph infra | ✅ at `orbtCS-sim-corrections/ralph_lab/` | Reuse `ralph_loop.sh`, parameterize |
| OpenClaw `research_v2.md` | ✅ at `overnight-agents/prompts/openclaw/` | Symlink into `prompts/` |

Build order in priority:

1. `hermes_worker.py` — most tasks go through here
2. `aws_qlora.py` — needed by W3 (QLoRA training week)
3. `ralph_dispatch.sh` — needed by W6 (Tier-C panel run)
4. Symlink + verify research_v2 prompt loads — needed before any writer task

---

## 5. AWS credit budget arithmetic

| Item | Cost | Cumulative |
|------|------|------------|
| QLoRA run #1 (Qwen3.6-27B + Nemotron+CB) | ~$15 | $15 |
| QLoRA run #2 (alt hyperparams) | ~$15 | $30 |
| Smoke tests / instance-up checks | ~$5 | $35 |
| Inference benchmark (compare base vs QLoRA on 200-persona eval) | ~$10 | $45 |
| Failure / re-run buffer | ~$30 | $75 |
| **Total committed** | **$75** | **of $391.68** |
| **Headroom** | $316.68 | **80%** |

The 80% headroom is the safety margin for: longer training (H4 requires
≥50% gap closure, may need more steps), Llama-3.1-8B legacy backbone if
W4 budget allows, or a second condition's QLoRA if H4 result is strong.

`aws_qlora.py` will hard-kill at $300 cumulative AWS spend. The scheduler's
`budget.py` already enforces `TOTAL_BUDGET_LIMIT=$400` across all sources.

---

## 6. GitHub repository setup (TA notice 2026-05-24)

Per TA Junhyeok Oh:
- Repo URL format: `https://github.com/{GitHubUsername}/261RCOSE46101`
- Public visibility (private allowed only until grades release)
- Submit URL via Google Form by **2026-06-02**

Decisions:

- Host on Sunwoo's GitHub account (Sunwoo authors all code per the
  division-of-labor: Sunwoo dev, Josh presentation).
- Name: `261RCOSE46101` exactly. No prefix, no project name in path.
- Visibility: **private** until 2026-06-30 (after expected grade release),
  then flip to public per TA instructions. This protects `.env.example`
  with real-API-key shapes and the AWS instance config until course is done.
- Add `.git/info/exclude` entry for `data/state/irb_status.yaml` even
  though gitignored — defense in depth.

The init script (`scripts/init_github_repo.sh`) parameterizes the username
and follows this convention.

---

## 7. Final-report Overleaf integration

TA provided `COSE461_Project_Final_Report_Template__2026_.zip`. Plan:

1. Download template ZIP, unpack into `reports/overleaf/`.
2. Symlink `reports/overleaf/main.tex` ← Writer agent's output target.
3. Writer agent's prompt has a "LaTeX section" mode in addition to its
   current Markdown mode. Selected via task payload `output_format: latex`.
4. Final assembly: pandoc + bibtex pass over the Writer-produced sections
   into a single PDF for submission.
5. Overleaf sync is one-way upload via the Overleaf API (or manual ZIP
   upload at the end of W8).

Methods section is human-authored per HANDOFF.md §8 — Writer NEVER outputs
methods. Critic enforces this on every section commit.

---

## 8. What does NOT change

- HANDOFF.md research questions, hypotheses, KPI targets — frozen.
- MOTIVATION_v2.md framing — frozen.
- 6-condition × 4-backbone factorial — frozen unless W4 budget forces drop.
- Evaluator-tier protocol from EVALUATOR_FALLBACK.md — frozen.
- The four known risks in `decisions/2026-05-24-known-risks.md` — PI
  audits weekly until resolved.

---

## 9. What needs Sunwoo's ack before any worker boots

These are Tier-2 actions; the autonomous lab cannot self-authorize them.

1. **GitHub username** for repo creation (need actual handle).
2. **AWS access code** from team spreadsheet (per TA notice).
3. **AWS account password change** — Sunwoo logs in once, changes from
   default `0001`-style, populates `.env` (or AWS profile) before
   `aws_qlora.py` runs.
4. **Hermes provider override confirmation** — by default `aws_qlora.py`
   and `hermes_worker.py` use `--provider openai -m gpt-5.4` per
   [[feedback-hermes-provider-override]]. Confirm this is still the right
   override on 2026-05-24.
5. **Plan endpoint key (`tp-...`)** — needed by both Hermes and Ralph
   dispatch. Source: `~/.hermes/.env` (already on this Mac).
6. **Mac Mini transfer plan** — autonomous schedule (`scripts/launchd_install.sh`)
   STAYS UNINSTALLED on Sunwoo's primary Mac. Either transfer to Mac Mini
   first OR keep this Mac off-launchd and run scheduler interactively.

If all six are green, the lab can boot. If any is yellow, the affected
worker stays disabled while others run.
