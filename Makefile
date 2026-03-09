
.PHONY: dev
dev:
	docker compose -f docker/docker-compose.dev.yml up

.PHONY: frontend
frontend: static/index.html

static/index.html: frontend/node_modules
	cd frontend && npm run build

frontend/node_modules: frontend/package.json frontend/package-lock.json
	cd frontend && npm install
	@touch frontend/node_modules

.PHONY: check
check: .venv frontend/node_modules
	.venv/bin/uv run ruff format
	.venv/bin/uv run ruff check --fix
	.venv/bin/uv run ty check
	.venv/bin/uv run pytest
	cd frontend && npm run lint

.venv: .venv/bin/uv pyproject.toml uv.lock
	@echo "Installing dependencies..."
	.venv/bin/uv sync --all-extras
	@touch .venv

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
	cd frontend && npm update

.PHONY: migrate
migrate: .venv
	alembic upgrade head

.PHONY: migration
migration: .venv
	alembic revision --autogenerate -m "$(msg)"
