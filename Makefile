.PHONY: setup first-run status emergency-stop daily-digest test docker-up docker-down clean

# ---------- Setup ----------
setup: docker-up python-deps pull-models init-db
	@echo "Setup complete. Edit .env and run 'make verify-policy' before 'make first-run'."

python-deps:
	uv venv .venv
	. .venv/bin/activate && uv pip install -e ".[mac]"

pull-models:
	@echo "Downloading Nemotron-Personas-Korea sample, BGE-m3, Qwen3.6-27B-MLX-Q4..."
	python scripts/pull_models.py

init-db:
	python -m orchestrator.queue init
	python -m orchestrator.budget init

docker-up:
	docker compose -f docker/docker-compose.yml up -d

docker-down:
	docker compose -f docker/docker-compose.yml down

# ---------- Policy gate ----------
verify-policy:
	@grep -q '^COURSE_AI_POLICY_VERIFIED=true$$' .env || \
		(echo "ERROR: COURSE_AI_POLICY_VERIFIED is not true. Read syllabus, set in .env." && exit 1)
	@echo "Policy verified. Heavy-autonomy mode enabled."

# ---------- First autonomous task ----------
first-run: verify-policy
	python -m orchestrator.scheduler enqueue \
		--task layer1_data_collection \
		--agent data_steward \
		--tier 1 \
		--priority high

# ---------- Live status ----------
status:
	python -m orchestrator.scheduler status

daily-digest:
	python -m agents.librarian daily_digest

# ---------- Emergency ----------
emergency-stop:
	python -m orchestrator.scheduler kill_all
	@echo "All agents halted. AWS instances stopping. Slack alert sent."

# ---------- Quality ----------
test:
	pytest tests/ -v

lint:
	ruff check .
	mypy orchestrator agents

# ---------- Cleanup ----------
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache .mypy_cache
