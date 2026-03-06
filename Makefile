
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

.PHONY: run
run: .venv/install
	.venv/bin/sharetree

.PHONY: upgrade
upgrade: .venv/bin/uv
	.venv/bin/uv lock --upgrade

.PHONY: migrate
migrate: .venv/install
	alembic upgrade head

.PHONY: migration
migration: .venv/install
	alembic revision --autogenerate -m "$(msg)"
