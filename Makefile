
.PHONY: venv
venv:
	bin/setup-dev-venv.sh

.PHONY: lock
upgrade:
	uv lock --upgrade

.PHONY: check
check:
	bin/verify
	pytest

.PHONY: migrate
migrate:
	alembic upgrade head

.PHONY: migration
migration:
	alembic revision --autogenerate -m "$(msg)"
