
.PHONY: dev
dev:
	docker compose -f docker/docker-compose.dev.yml up

.PHONY: frontend
frontend: static/index.html

static/index.html:
	cd frontend && npm install && npm run build

.PHONY: check
check: .venv/install
	.venv/bin/uv run ruff format
	.venv/bin/uv run ruff check --fix
	.venv/bin/uv run ty check
	.venv/bin/uv run pytest

.venv/install: .venv/bin/uv pyproject.toml uv.lock
	@echo "Installing dependencies..."
	.venv/bin/uv sync --all-extras
	@touch .venv/install

.venv/bin/uv: .venv/bin/python
	.venv/bin/pip install uv

.venv/bin/python:
	python3 -m venv --prompt venv .venv

.PHONY: clean
clean:
	rm -rf .venv

.PHONY: docker-build
docker-build:
	docker build -t sharetree .

.PHONY: upgrade
upgrade: .venv/bin/uv
	.venv/bin/uv lock --upgrade

.PHONY: migrate
migrate: .venv/install
	alembic upgrade head

.PHONY: migration
migration: .venv/install
	alembic revision --autogenerate -m "$(msg)"
