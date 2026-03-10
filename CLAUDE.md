# CLAUDE.md — sharetree

## Project Overview

**sharetree** is a file-sharing web application that lets administrators share existing server-side folder trees with external users. Access is controlled via **access codes** that map to `fnmatch`-style glob patterns, giving fine-grained control over which files each recipient can browse and download.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13+ |
| API framework | FastAPI |
| ASGI server | Uvicorn |
| Settings | pydantic-settings |
| ORM | SQLAlchemy 2.0+ |
| Migrations | Alembic (auto-applied on startup) |
| Database | SQLite |
| Frontend | Vue.js 3 + Vite + Tailwind CSS v4 + shadcn-vue |
| Package manager | uv |
| Logging | structlog |
| Formatter / linter | Ruff (line length: 120) |
| Type checker | ty |
| Test runner | pytest |
| CI | GitHub Actions (`make ci` on push/PR) |


## Development Setup

venv

```bash
make .venv  # installs .venv and sharetree pyproject.toml
```

Check code lint/format/typecheck

```bash
make check   # installs .venv automatically, then runs ruff + ty + eslint
```

### Environment variables

Create a `.env` file in the repo root (`SHARETREE_` prefix for all vars):

```env
SHARETREE_SESSION_SECRET=<random-secret>   # required
SHARETREE_SHARE_ROOT=files                 # optional, default: files/
SHARETREE_DATA_PATH=data                   # optional, default: data/
SHARETREE_DEV=true                         # optional, enables uvicorn auto-reload
```

`SESSION_SECRET` is the only required variable.

## Common Commands

| Task | Command |
|---|---|
| Run dev server | `python -m sharetree` or `sharetree` |
| Build frontend | `make frontend` |
| Format + lint + type-check | `make check` |
| Run tests | `pytest` |
| Apply DB migrations | `make migrate` |
| Create new migration | `make migration msg="description"` |
| Upgrade dependencies | `make upgrade` |

The dev server starts on `http://0.0.0.0:8000` with auto-reload enabled. Alembic migrations run automatically on app startup.

## Architecture & Conventions

### Layering

```
API route (api/) → Service function (services/) → Database (db.py / models/)
```

- **API layer** handles HTTP concerns (request parsing, response serialization, HTTP errors).
- **Service layer** contains all business logic. Functions raise `HTTPException` directly when appropriate.
- Keep route handlers thin; delegate to service functions.

### Key conventions

- **Response standardization:** `apiexception` library (registered in `app.py`) normalizes all responses. Raise `HTTPException` with appropriate status codes.
- **Type hints:** Use Python 3.10+ union syntax (`str | None`, not `Optional[str]`).
- **SQLAlchemy:** Use `Mapped`/`mapped_column` style and `get_session()` context manager from `db.py`.
- **Pydantic — required for all endpoints:** Every API endpoint **must** use:
  - A `pydantic.BaseModel` subclass for structured request bodies (already enforced by FastAPI for POST/PUT).
  - A `pydantic.BaseModel` subclass as the return type annotation **and** as the `response_model=` argument on the route decorator — never plain `dict` or unparameterized generics.
  - Service functions that feed into API responses should return typed Pydantic models (e.g. `list[DirectoryEntry]`), not `list[dict]` or `list[dict[str, Any]]`.
  - Generic response wrappers such as `ResponseModel` must be fully parameterized (e.g. `ResponseModel[MyData]` or `ResponseModel[None]`), never bare `ResponseModel`.

## API Reference

Base prefix: `/api/v1`

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Returns `{"status": "ok"}` |
| GET | `/headers` | Echoes all request headers (debug endpoint) |
| GET | `/auth` | Forward-auth check for reverse proxy; validates `X-Forwarded-Uri` against session access codes |
| GET | `/me` | Returns active access codes and accessible paths from session and admin auth status |
| POST | `/access/activate` | Validates and adds an access code to the session |
| GET | `/browse` | Lists root directory (filtered by session access codes) |
| GET | `/browse/{path}` | Lists a subdirectory |
| POST | `/admin/login` | Log in as admin using `ADMIN_PASSWORD` (disabled when `TRUST_HEADERS=true`) |
| POST | `/admin/logout` | Clear admin session |
| POST | `/admin/access/create` | Creates a new access code with given patterns |
| DELETE | `/admin/access/revoke` | Deletes an access code by code value; returns 404 if not found |
| GET | `/admin/access/sessions` | Lists access codes grouped by session, paginated (200/page) |
| GET | `/admin/browse` | Lists root directory (full tree, no access-code filter; admin only) |
| GET | `/admin/browse/{path}` | Lists a subdirectory (full tree, no access-code filter; admin only) |
| GET | `/download/{path}` | Downloads a file (access-controlled) |

Admin endpoints under `/api/v1/admin/` (except login/logout) require admin access. When `TRUST_HEADERS=false` (default), log in via `POST /api/v1/admin/login` with the configured `ADMIN_PASSWORD`. When `TRUST_HEADERS=true`, the upstream proxy must forward `Remote-Groups: admins`.

## Database

- **Engine:** SQLite at `{DATA_PATH}/sharetree.db`
- **Schema management:** Alembic migrations, auto-applied on app startup via `run_migrations()` in `db.py`.

### AccessCode model

| Column | Type | Notes |
|---|---|---|
| `code` | `str` (PK) | URL-safe token (`secrets.token_urlsafe(16)`) |
| `_patterns_json` | `str` | JSON-encoded list of `fnmatch` glob patterns; exposed via `patterns` property |
| `nick` | `str \| None` | Optional human-readable label |
| `session_id` | `str \| None` | UUID of the first user session that activated this code (indexed) |

## Testing

- Tests are **co-located** with the code they test in `tests/` subdirectories: `api/tests/`, `api/admin/tests/`, `services/tests/`, and `src/sharetree/tests/`.
- Use `pytest` with `tmp_path` for filesystem tests.
- Mock `SHARE_ROOT` by patching `sharetree.services.browse.SHARE_ROOT`.
- `conftest.py` at the repo root sets `SHARETREE_SESSION_SECRET` for all test runs.
- `src/sharetree/tests/test_migrations.py` verifies all ORM model changes have a corresponding Alembic migration.

## Code Style

- **Formatter/linter/type checker:** Run `make check`
- **Line length:** 120 characters
- Run `make ci` before pushing

## Git Conventions

Commit messages follow `category: description`:

```
api: add health endpoint
browse: fix path traversal edge case
sql: add nick column to access_codes
frontend: add breadcrumb navigation
tests: cover symlink escape scenarios
```

Categories: `api`, `sql`, `dev`, `admin`, `browse`, `access`, `frontend`, `tests`, `ci`, `env`

### Keeping documentation up to date

When a feature commit is pushed, **update both `CLAUDE.md` and `README.md`** to reflect the change:

- `CLAUDE.md`: update the directory structure, API reference, and any affected sections.
- `README.md`: update the feature checklist and any user-facing descriptions.

Include the doc update in the same commit or as a follow-up `dev: update docs` commit.

## Docker Deployment

README.md

## Not Yet Implemented

- Redis support
