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
| Frontend | Vue.js 3 + Vite |
| Package manager | uv |
| Formatter / linter | Ruff (line length: 120) |
| Type checker | ty |
| Test runner | pytest |
| CI | GitHub Actions (`make check` on push/PR) |

## Directory Structure

```
sharetree/
├── .github/workflows/python-app.yml  # CI: ruff + ty + pytest on push/PR
├── bin/
│   ├── setup-dev-venv.sh   # Create + populate venv via uv
│   └── verify              # Run ruff format, ruff check --fix, ty check
├── docker/
│   └── entrypoint.sh       # Container startup: Caddy mode or direct app mode
├── frontend/               # Vue.js 3 SPA (Vite)
│   └── src/
│       ├── views/          # AccessView.vue, BrowseView.vue
│       └── components/     # Breadcrumbs.vue, EntryList.vue
├── migrations/             # Alembic versioned migrations
│   └── versions/0001_initial_schema.py
├── src/sharetree/
│   ├── __main__.py         # CLI entry point; starts uvicorn on :8000
│   ├── app.py              # FastAPI app, middleware, router registration
│   ├── db.py               # SQLAlchemy engine, session factory, run_migrations()
│   ├── settings.py         # pydantic-settings config (SHARETREE_ prefix)
│   ├── models/all.py       # AccessCode ORM model
│   ├── api/
│   │   ├── health.py       # GET /api/v1/health
│   │   ├── access.py       # GET/POST /api/v1/access*
│   │   ├── browse.py       # GET /api/v1/browse[/{path}]
│   │   ├── download.py     # GET /download/{path}
│   │   └── admin/access.py # POST /api/v1/admin/access/create
│   └── services/
│       ├── access.py       # Business logic: create/validate access codes
│       ├── browse.py       # Business logic: directory listing, file path resolution
│       └── tests/
│           ├── test_browse.py        # Tests for list_directory_entries()
│           └── test_get_file_path.py # Tests for get_file_path()
├── static/                 # Built frontend output (served by FastAPI)
├── .dockerignore
├── alembic.ini
├── conftest.py             # Sets SHARETREE_SESSION_SECRET for test runs
├── Dockerfile              # Multi-stage build: frontend + Python + Caddy
├── Makefile
└── pyproject.toml
```

## Development Setup

```bash
make check   # installs .venv automatically, then runs ruff + ty + pytest
```

Or manually:

```bash
python3 -m venv .venv
.venv/bin/pip install uv
.venv/bin/uv sync
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
| Format + lint + type-check | `bin/verify` |
| Run full check suite | `make check` |
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
- **Pydantic:** Use `pydantic.BaseModel` for request/response bodies in route signatures.

## API Reference

Base prefix: `/api/v1`

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Returns `{"status": "ok"}` |
| GET | `/access` | Returns active access codes and accessible paths from session |
| POST | `/access/activate` | Validates and adds an access code to the session |
| GET | `/browse` | Lists root directory (filtered by session access codes) |
| GET | `/browse/{path}` | Lists a subdirectory |
| POST | `/admin/access/create` | Creates a new access code with given patterns |
| GET | `/download/{path}` | Downloads a file (access-controlled) |

Admin endpoints live under `/api/v1/admin/`. In Docker (Caddy mode), admin routes are protected by HTTP basic auth; Caddy forwards `Remote-Groups: admins` to the app on successful authentication.

## Database

- **Engine:** SQLite at `{DATA_PATH}/sharetree.db`
- **Schema management:** Alembic migrations, auto-applied on app startup via `run_migrations()` in `db.py`.

### AccessCode model

| Column | Type | Notes |
|---|---|---|
| `code` | `str` (PK) | URL-safe token (`secrets.token_urlsafe(16)`) |
| `_patterns_json` | `str` | JSON-encoded list of `fnmatch` glob patterns; exposed via `patterns` property |
| `nick` | `str \| None` | Optional human-readable label |

## Security Model

- Users activate access codes via `POST /api/v1/access/activate`. Active codes are stored in the encrypted server-side session (Starlette `SessionMiddleware`).
- Each code maps to a list of `fnmatch` patterns controlling which paths are visible and downloadable.
- Pattern examples: `/docs/*` (shallow), `/reports/**` (recursive — `*` matches `/` in fnmatch).
- **Path traversal protection:** `services/browse.py` resolves paths with `.resolve()` and verifies they remain under `SHARE_ROOT`. Symlink escapes are blocked.

## Testing

- Tests are **co-located** with the code they test in a `tests/` subdirectory.
- Use `pytest` with `tmp_path` for filesystem tests.
- Mock `SHARE_ROOT` by patching `sharetree.services.browse.SHARE_ROOT`.
- `conftest.py` at the repo root sets `SHARETREE_SESSION_SECRET` for all test runs.

## Code Style

- **Formatter/linter:** Ruff (`ruff format`, `ruff check --fix`)
- **Line length:** 120 characters
- **Type checker:** `ty check` (not Mypy)
- Run `bin/verify` before pushing; CI enforces `make check` on all PRs.

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

```bash
docker build -t sharetree .
```

The image supports two modes controlled by `SHARETREE_TRUST_HEADERS`:

- **Caddy mode** (default, `TRUST_HEADERS` falsy): Caddy listens on `:80`, applies HTTP basic auth to `/api/v1/admin/*` using `SHARETREE_ADMIN_PASSWORD`, and forwards `Remote-Groups: admins` to the app on success. The app process listens on `localhost:8000` internally with `TRUST_HEADERS=true` to validate the forwarded header.
- **Trusted-headers mode** (`TRUST_HEADERS=true`): App listens directly on `:8000`. An upstream reverse proxy is expected to handle auth and forward `Remote-Groups: admins` for admin access.

| Variable | Required | Default | Description |
|---|---|---|---|
| `SHARETREE_SESSION_SECRET` | yes | — | Secret key for encrypted session cookies |
| `SHARETREE_ADMIN_PASSWORD` | in Caddy mode | — | Password for Caddy basic auth on admin routes |
| `SHARETREE_TRUST_HEADERS` | no | `false` | Enable header trust; disables Caddy |
| `SHARETREE_SHARE_ROOT` | no | `/files` | Path to shared folder tree (mount a volume) |
| `SHARETREE_DATA_PATH` | no | `/data` | Path to SQLite database directory (mount a volume) |

Volumes: `/data` (database), `/files` (shared files). Health check: `GET /api/v1/health`.

## Not Yet Implemented

- Admin authentication (magic credentials, IP subnet)
- Forward-auth API endpoint (for reverse proxy integration)
- Redis support
