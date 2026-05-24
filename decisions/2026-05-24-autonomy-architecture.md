---
date: 2026-05-24T00:00:00Z
agent: human
task_kind: architecture_decision
tier: 3
auto_executed: false
human_approved: true
approver: sunny@tryorbt.com, josh@tryorbt.com
cost_usd: 0
---

## What
Adopt a tiered-autonomy architecture for the COSE461 / ORBT research project:
- Mac Mini M4 Pro runs the orchestrator 24/7 as a launchd service.
- Six specialized agents (data_steward, experiment_runner, analyst, writer,
  critic, librarian) execute via the Claude Agent SDK.
- Heavy autonomy mode (Tier 1+2+3) is enabled, contingent on COSE461 AI policy
  verification before W1 execution.
- Methods section is human-authored under all autonomy modes.
- Writer can only commit to `draft/agent-*` branches; main merge requires
  human PR approval.

## Why
- We have an 8-week / 2-person budget. Manual orchestration would consume
  most of the available time on coordination overhead.
- The OASIS simulations and metric computations are long-running, parallelizable,
  and largely deterministic — ideal for autonomous execution.
- The Writer-Critic loop reduces single-agent hallucination by introducing
  an adversarial reviewer with a different model family.
- ORBT product roadmap requires a reproducible autonomous research framework;
  building it now amortizes the cost across future projects.

## Reversibility
- Hard kill: `make emergency-stop` halts all agents and stops AWS instances.
- Tier downgrade: edit `.env` `AUTONOMY_TIER=light` and restart `orchestrator.scheduler`.
- Full revert: switch to manual orchestration; agents are stateless processes
  consuming the SQLite queue, so removing them leaves the data and results intact.

## Open issues that escalate to Tier 3
- COSE461 AI policy verification (must be done by Sunwoo before W1).
- Whether Writer can draft `methods` even with heavy human review (current
  answer: no, regardless of policy).
- W3 checkpoint: if Writer-Critic loop fails to converge in 3 rounds on
  >50% of test sections, abandon report-drafting autonomy.

## Source data
- Prior conversation thread (project memory).
- COSE461 lecture materials (project knowledge source).
- Nemotron-Personas-Korea, CultureBank, OASIS documentation.
