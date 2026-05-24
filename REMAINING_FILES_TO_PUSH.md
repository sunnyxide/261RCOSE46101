# Remaining files to push (60 files)

This commit only includes the core architecture docs. The remaining 60 source
files live in the local checkout and need to be pushed via `git push` after
`sunnyxide` GitHub auth is set up locally.

## To push everything

```bash
cd /Users/orbt/Desktop/orbt/projects/orbt-research-lab
gh auth login --hostname github.com --git-protocol ssh
# (Pick "sunnyxide" when prompted; complete browser flow)
git push -u origin main
```

The local repo already has the initial commit ready. After auth, a single push
uploads all 65 files.

## What's missing (subset)

- `HANDOFF.md` (15 KB, the primary entry point)
- `MOTIVATION_v2.md`, `KPI_FRAMEWORK.md`, `SELF_EVAL_LOOP.md`, `ORBT_INTEGRATION.md`, `SETUP.md`
- `pyproject.toml`, `Makefile`, `.env.example`, `.gitignore`
- `agents/` (10 files), `agents/shared/` (5 files including the new llm_judge_panel.py, hermes_worker.py, aws_qlora.py)
- `orchestrator/` (4 files)
- `scripts/` (7 files including healthcheck_30min.sh, ralph_dispatch.sh, com.orbt.research-lab.healthcheck.plist, init_github_repo.sh)
- `prompts/` (5 agent system prompts)
- `config/` (agents.yaml, models.yaml, rubric.yaml)
- `decisions/` (2 of 4 already pushed; 2 more in local)
- `reports/` (bibliography.bib, AI_USAGE_DISCLOSURE.md, style_guide.md)
- `docker/`, `tests/`, `notebooks/`, `data/state/aws_instance_pip_freeze.txt`

This file will be deleted after the full push completes.
