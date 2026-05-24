# AI tool usage disclosure (COSE461 + venue submission)

> **Status**: Draft. Update as the project progresses. Finalized version submitted
> with the paper.

## Authorship

- **Human authors**: Sunwoo (sunny@tryorbt.com), Josh (josh@tryorbt.com)
- All research questions, hypotheses, methodology decisions, and final
  edits were human-made.
- The methods section was human-authored from start to finish.

## Autonomous agents used

This project uses an autonomous orchestration system (`orbt-research-lab`)
built on the Claude Agent SDK. The system runs on a Mac Mini M4 Pro and
AWS g6e.xlarge instances, with six specialized agents:

| Agent | Model | Role | Sections it touched |
|-------|-------|------|---------------------|
| data_steward | Claude Sonnet 4.6 | Dataset ingestion, validation | — |
| experiment_runner | Claude Sonnet 4.6 | Simulation execution | — |
| analyst | Claude Sonnet 4.6 | Metric computation | — |
| writer | Claude Sonnet 4.6 | Section drafts on `draft/agent-*` branches | (filled in W7) |
| critic | GPT-5 | Adversarial draft review | — |
| librarian | Claude Sonnet 4.6 | Data lineage, daily digest | — |

## Decision boundaries

- **Tier 1 (autonomous)**: data fetch, simulation runs, metric calculation.
- **Tier 2 (autonomous + async human approval)**: experiment configuration
  proposals, section drafts, bug fixes.
- **Tier 3 (human-only)**: research questions, hypotheses, methodology,
  final merges to main, IRB.

## Reproducibility

All prompts, configurations, and orchestrator state are in this repository:
- Prompts: `prompts/`
- Agent configs: `config/agents.yaml`
- Model registry: `config/models.yaml`
- Decision log: `decisions/`
- Total API spend: (filled in W8) USD

## Course policy compliance

- COSE461 AI policy reviewed by Sunwoo on (date TBD).
- Specific provisions followed: (list TBD after reviewing syllabus).
- This disclosure shared with the course instructor before submission.
