# Setup runbook — first deployment on Mac Mini

## Prerequisites

- Mac Mini M4 Pro running macOS 15+, with at least 100 GB free disk.
- Docker Desktop installed and running.
- `uv` installed for Python env management: `brew install uv`
- `git`, `git-lfs`, `dvc` installed.
- Tailscale set up so you can SSH in from outside the office.
- COSE461 AI policy reviewed (read the syllabus from project knowledge source).

## Step 1 — Clone and configure

```bash
cd ~/projects
git clone <your-repo-url> orbt-research-lab
cd orbt-research-lab
cp .env.example .env
# Fill in: ANTHROPIC_API_KEY, OPENAI_API_KEY, SLACK_*, NEO4J_PASSWORD, AWS profiles
```

After reading the COSE461 syllabus:
```bash
# Only flip to true once you have confirmed AI usage is permitted with disclosure
sed -i '' 's/^COURSE_AI_POLICY_VERIFIED=false$/COURSE_AI_POLICY_VERIFIED=true/' .env
```

## Step 2 — Bring up stateful services

```bash
make docker-up
# Verify: open http://localhost:7474 → Neo4j browser, log in with neo4j/<your password>
```

## Step 3 — Python env + dependencies

```bash
make python-deps    # creates .venv, installs project + Mac extras
source .venv/bin/activate
```

## Step 4 — Pull models and datasets

```bash
python scripts/pull_models.py
# Pulls Nemotron-Personas-Korea, CultureBank, BGE-m3, Qwen3.6-27B MLX Q4
# Expected disk: ~80 GB; expected time: 30-90 min depending on bandwidth
```

## Step 5 — Initialize the orchestrator DB

```bash
make init-db
```

## Step 6 — Smoke test Layer 1 before going autonomous

```bash
python notebooks/01_layer1_smoke_test.py
# Should print: "Layer 1 smoke test passed."
```

If the smoke test fails, fix it BEFORE installing the launchd service.
The autonomous lab assumes Layer 1 ingest works.

## Step 7 — Seed the task queue with the W1 plan

```bash
python scripts/seed_task_queue.py
make status    # confirm tasks are enqueued
```

## Step 8 — Install the orchestrator as a launchd service

```bash
bash scripts/launchd_install.sh
# This makes the lab survive reboots.
```

## Step 9 — Verify autonomy works

```bash
make status     # should show "running" state for first task within 30s
make daily-digest   # force-send the first Slack digest now to verify the bot
```

Check `#orbt-research-lab` in Slack. You should see today's digest with
queue state, budget, and any decisions logged.

## Step 10 — Set the daily digest cron

The librarian agent posts the digest at 08:00 KST. Confirm by running:
```bash
crontab -l   # should NOT have a digest entry — launchd handles scheduling via APScheduler in scheduler.py
```

## Step 11 — Sign off on the autonomy decision

Read `decisions/2026-05-24-autonomy-architecture.md`. If you disagree with
anything in it, edit the file and amend before W1 execution.

## Emergency stop

If anything goes sideways:
```bash
make emergency-stop
# OR send "!stop" in #orbt-research-lab (when slackbot is up)
```

This halts all running tasks, stops AWS instances, and pages both operators.

## What to expect in W1

- Day 1 (today): Layer 1 ingestion (Nemotron, CultureBank, WVS placeholder).
- Day 2-3: Layer 2 ingestion (KOSIS, KCA, Naver Datalab, KOFICE — some manual fetching required).
- Day 4-5: 50 D2C scenarios drafted from Layer 2 ground truth (autonomous proposal, human approval).
- Day 6-7: KG construction (LightRAG + Neo4j over CultureBank Korean subset).

## Things to do MANUALLY in W1 (autonomous can't help)

- Download WVS Wave 7 Korea file from worldvaluessurvey.org (TOS-restricted).
- IRB application for human evaluators (universities are slow; start now).
- Konkuk / KU evaluator pool outreach.
- Read COSE461 syllabus, confirm AI policy, fill in `reports/AI_USAGE_DISCLOSURE.md` policy_provisions list.
