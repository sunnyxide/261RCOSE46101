# Self-evaluation and feedback loop architecture

> Three nested loops give the autonomous lab self-correction capability without
> requiring human in the inner loops. Read top to bottom.

## Overview

```
Loop A  (seconds,    every task)       ────────  Self-check
Loop B  (minutes,    every draft)      ────────  Writer ↔ Critic
Loop C  (hourly+daily, system-wide)    ────────  QA Meta + PI

         outer        inner
         slower       faster
         system-level task-level
```

Single-agent self-check (Loop A) is the cheapest and catches the largest
fraction of errors per dollar. Writer-Critic (Loop B) is more expensive but
catches the errors self-check misses. QA Meta + PI (Loop C) catches the
errors no per-task review can see — drift, KPI miss projection, data lineage
gaps.

Each loop's failure mode is a different kind of error. Don't skip layers.

## Loop A — Per-task self-check

### Where it runs
Inside every domain agent (data_steward, experiment_runner, analyst, writer,
librarian). Before the agent emits its outcome to the orchestrator, it
performs one extra LLM call against its own draft output.

### The prompt template

```text
You just produced the following output for task <task_kind>:

<output content>

Before submitting, answer four questions in JSON:

1. literal_addressing: Does this output address the LITERAL task asked, or
   an adjacent one? Pay specific attention to scope creep — agents tend to
   produce more than asked, which inflates downstream review cost.

2. claim_traceability: For every numerical claim or named-entity claim,
   can you point to a specific file path or task ID where that came from?

3. failure_modes: List failure modes you considered. List failure modes
   you did NOT address that could matter.

4. confidence: A number 0.0–1.0 with a one-sentence justification.

Then decide:
   submit (true/false) — submit only if confidence ≥ 0.7 AND no critical
   failure mode is unaddressed.

Output exactly:
{
  "literal_addressing": "<yes|no — explanation>",
  "claim_traceability": "<yes|no — list of unsupported claims if no>",
  "failure_modes_considered": [...],
  "failure_modes_unaddressed": [...],
  "confidence": <float>,
  "submit": <bool>
}
```

### What happens on `submit: false`

The agent does NOT commit. Instead it enqueues a self-correction task:
- Same agent, same kind, payload includes the original output + self-flagged issues
- Priority bumped one level (normal → high)
- justification field captures the self-flag

This is bounded — after 2 self-correction rounds for the same task, the agent
escalates to Tier-2 (which means the Critic gets involved even outside Writer
context).

### Cost profile

One self-check adds ~$0.001-$0.005 per task on Claude Sonnet 4.6 (most outputs
are < 4k tokens). For ~500 tasks across W1-W8, total self-check cost is
~$1-3. Worth it for the ~60% upstream error catch.

## Loop B — Writer-Critic adversarial loop

Already specified in `agents/writer.py` and `agents/critic.py`. Recap:

### Roles
- **Writer** (Claude Sonnet 4.6): drafts paper sections on `draft/agent-*`
  branches. Sees decision log + outline + style guide + results manifest.
- **Critic** (GPT-5 — different model family): reviews draft. Does NOT see
  underlying data. Checks: citation existence, numerical claim sourcing,
  cross-section consistency, rubric coverage, style drift, paper citation
  reality (via Semantic Scholar).

### Loop dynamics

```
Round 0: Writer drafts → Critic reviews → returns issues list + pass score
Round 1: Writer reads issues → revises draft → Critic re-reviews
Round 2: same
Round 3: if still not passing, escalate to Tier-3 (Sunwoo reviews directly)
```

The 3-round cap is non-negotiable. If the loop hasn't converged, something
is structurally wrong (bad data, ambiguous outline, broken metric, etc.)
and human judgment is required to unblock.

### Why a different model family for Critic

Same model = shared blind spots. Writer (Claude) and Critic (GPT-5) trained
on overlapping but non-identical data, with different RLHF preferences. The
intersection of their disagreements is closer to the truth than either alone.

### What Critic explicitly cannot do
- Critic does not rewrite. Reports issues only.
- Critic does not invent data to fill gaps.
- Critic does not approve drafts with any error-severity issue.
- Critic does not approve `methods` section drafted by any agent.

## Loop C — QA Meta + Principal Investigator audit

Two new agents, both implemented in v2.

### QA Meta agent — hourly cadence

Runs every hour via APScheduler. Operating questions:
1. Are KPIs trending toward target by their checkpoint dates?
2. Is the task queue moving? Backlog growing or shrinking?
3. Is cost burn on-pace?
4. Are there agents that haven't reported in 2× their expected duration?
5. Are there orphan artifacts (files with no manifest)?

### QA Meta outputs

For each tick, QA Meta writes a structured report to `results/qa/<timestamp>.yaml`:

```yaml
tick: 2026-05-25T10:00:00Z
kpi_projections:
  static_cas_full_vs_vanilla:
    target: 0.8
    projected: 0.6  # based on partial data
    eta_to_target: "2026-06-12 (W5)"
    risk: orange
  cost_total:
    target: 400.00
    actual_to_date: 47.21
    projected_at_w8: 312.50
    risk: green
process:
  critic_first_pass_rate: 0.41   # below target 0.5
  writer_critic_mean_rounds: 2.4 # above target 2.0
  risk: yellow
recommendations:
  - "Tighten writer outline for Results section to reduce Critic rounds"
  - "Tier-2: propose reducing scenario count from 50 to 35 if W2 G2 at risk"
queue_actions_taken:
  - reprioritized: task-id-abc123 from low → high (KPI dependency)
  - paused: nothing
```

### QA Meta authority

- Can reorder task queue priorities (Tier 1).
- Can propose configuration changes via decision log (Tier 2 — needs human ack).
- Cannot modify research questions, hypotheses, or methodology (Tier 3 only).
- Cannot pause/kill running tasks except on Red/Black severity.

### PI (Principal Investigator) agent — daily cadence

Runs at 07:00 KST, before the librarian's 08:00 digest. Operating questions:
1. Is the research question still being answered by current work?
2. Has any decision in the past 7 days drifted from the hypotheses?
3. Are the metrics still the right metrics?
4. Are there emergent findings that suggest a new hypothesis worth chasing?
5. Is the paper outline still coherent given the data we have?

### PI agent prompt (excerpt)

```text
You are the Principal Investigator agent. You review the past 24h of
decisions, results, and Writer outputs, and assess whether the project is
still on the rails toward its stated research questions.

You have access to:
- HANDOFF.md (RQs and hypotheses, immutable)
- decisions/ from last 7 days
- results/ latest snapshot
- KPI_FRAMEWORK.md
- reports/sections/* (current drafts)

Identify, in this order:
1. Hypothesis drift: any decision or finding that implicitly tests a
   different hypothesis than what HANDOFF.md states. CRITICAL — flag
   immediately.
2. Metric drift: any case where a result section reports a metric not in
   KPI_FRAMEWORK.md without justification.
3. Coherence: do the section drafts tell a single story or multiple?
4. Emergent findings: anything in the data that suggests a new RQ. NOT
   acted upon, just flagged for Sunwoo's W6 outline-revision meeting.

Output a 5-bullet digest. No more, no less. Sunwoo reads this before
opening Slack. Brevity matters.
```

### PI agent output

Goes to `reports/digests/<date>-pi-audit.md` and gets included in the
librarian's daily digest. Example:

```markdown
## PI audit — 2026-05-25

1. HYPOTHESIS DRIFT — None detected.
2. METRIC DRIFT — Analyst is reporting CAS_intercoder_variance which is
   not in KPI_FRAMEWORK.md. Either add it formally or remove from results.
3. COHERENCE — Related-work draft mentions BAS but methods doesn't
   define it yet (methods is human-authored, write it).
4. EMERGENT — Nemotron-only condition is outperforming Hofstede-only on
   PDI. Worth a sub-paragraph in Discussion if it holds across 3 backbones.
5. STATUS — Queue healthy, costs healthy, on pace for G2 by W2 Friday.
```

## How the loops compose

Most errors caught at Loop A never reach Loop B. Loop B catches Writer-
specific issues Loop A is too narrow to see. Loop C catches drift no per-
task review can see.

```
Cost ratio (typical, rough):
  Loop A:  $1
  Loop B:  $10–30 per draft (3 rounds × Writer + Critic + revisions)
  Loop C:  $5 per day (~$300 across 8 weeks)

Total feedback infrastructure cost: ~$400 across the project.
Total project budget: $400 (AWS) + ~$200 (API) = $600. Feedback is ~60%
of operational spend. This is correct — research quality compounds; cheap
review at the margin is the highest-ROI spend in autonomous research.
```

## Convergence detection

The Writer-Critic loop converges when score ≥ 0.85 OR 3 rounds elapsed.
But "convergence" in autonomous research more broadly means: KPI
projections stable, decision log not contradicting itself, PI agent
reports no drift for 3 consecutive days.

If convergence doesn't happen by W6 end, that's a Red signal — call
Sunwoo, do an outline revision session, possibly drop a condition.

## Anti-patterns the loops are designed to prevent

| Anti-pattern | Which loop catches it |
|--------------|----------------------|
| Writer hallucinates a metric value | Loop B (Critic checks numerical traceability) |
| Writer hallucinates a citation | Loop B (Critic checks bib + Semantic Scholar) |
| Data steward commits a non-Korean CultureBank entry | Loop A (self-check ambiguity flag) |
| Experiment runner re-runs OASIS sim with stale config | Loop A (literal_addressing check) |
| Analyst computes JSD with wrong reference distribution | Loop A + Loop C (PI's metric-drift check) |
| Methods drift away from what experiment_runner actually did | Loop C (PI's coherence check) |
| Cost run-away from chained recursive calls | budget.py + QA Meta Red severity |
| Project pivots from RQ1 to a different RQ silently | Loop C (PI's hypothesis-drift check) |
| Sections contradict each other | Loop B (Critic cross-section consistency) |
| Style drifts toward marketing voice | Loop B (Critic style check) |
