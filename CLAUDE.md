# CLAUDE.md — sharetree

## Project Overview

**sharetree** is a file-sharing web application that lets administrators share existing server-side folder trees with external users. Access is controlled via short-lived **access codes** that map to `fnmatch`-style glob patterns, allowing fine-grained control over which files and directories each recipient can browse.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| API framework | FastAPI |
| ASGI server | Uvicorn |
| Session middleware | Starlette |
| ORM | SQLAlchemy 2.0+ |
| Database | SQLite |
| Package manager | uv |
| Formatter / linter | Ruff (line length: 120) |
| Type checker | ty |
| Test runner | pytest |

## Directory Structure

```
sharetree/
├── bin/
│   ├── setup-dev-venv.sh   # Create + populate venv via uv
│   └── verify              # Run ruff format, ruff check --fix, ty check
├── src/sharetree/
│   ├── __main__.py         # CLI entry point; starts uvicorn on :8000
│   ├── app.py              # FastAPI app, middleware, router registration
│   ├── db.py               # SQLAlchemy engine, session factory, init_db()
│   ├── settings.py         # Env-var config (SHARETREE_ prefix)
│   ├── models/
│   │   └── all.py          # AccessCode ORM model
│   ├── api/
│   │   ├── health.py       # GET /api/v1/health
│   │   ├── access.py       # GET/POST /api/v1/access
│   │   ├── browse.py       # GET /api/v1/browse[/{path}]
│   │   └── admin/
│   │       └── access.py   # POST /api/v1/admin/access/create
│   └── services/
│       ├── access.py       # Business logic: create/validate access codes
│       ├── browse.py       # Business logic: directory listing + access checks
│       └── tests/
│           └── test_browse.py
├── static/
│   └── favicon.ico
├── Makefile
├── pyproject.toml
└── uv.lock
```

## Development Setup

### First-time setup

```bash
make venv          # creates venv/, installs uv, runs uv sync + editable install
```

Or manually:

```bash
python3 -m venv venv
venv/bin/pip install uv
venv/bin/uv sync
venv/bin/pip install -e ".[dev]"
```

### Environment variables

Create a `.env` file in the repo root (all vars use the `SHARETREE_` prefix):

```env
SHARETREE_SESSION_SECRET=<random-secret>   # required
SHARETREE_SHARE_ROOT=files                 # optional, default: files/
SHARETREE_DATA_PATH=data                   # optional, default: data/
```

`SESSION_SECRET` is the only required variable. The app will not start without it.

## Common Commands

| Task | Command |
|---|---|
| Run dev server | `python -m sharetree` or `sharetree` |
| Format + lint + type-check | `bin/verify` |
| Run full check suite | `make check` |
| Run tests | `pytest` |
| Upgrade dependencies | `make upgrade` |
| Install / sync deps | `uv sync` |

The dev server starts on `http://0.0.0.0:8000` with auto-reload enabled.

## Architecture & Conventions

### Layering

```
API route (api/) → Service function (services/) → Database (db.py / models/)
```

- **API layer** handles HTTP concerns (request parsing, response serialization, HTTP errors).
- **Service layer** contains all business logic. Functions raise `HTTPException` directly when appropriate.
- **No fat controllers** — keep route handlers thin; delegate to service functions.

### Response standardization

All API responses are normalized by the `apiexception` library (registered in `app.py`). Raise `HTTPException` with appropriate status codes; the library wraps them consistently.

### Type hints

Use Python 3.11+ union syntax everywhere:

```python
# correct
def foo(x: str | None) -> list[str]: ...

# avoid
from typing import Optional, List
def foo(x: Optional[str]) -> List[str]: ...
```

### SQLAlchemy 2.0 style

Use `Mapped` and `mapped_column` for model columns:

```python
from sqlalchemy.orm import Mapped, mapped_column

class MyModel(Base):
    __tablename__ = "my_table"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str | None]
```

Use the session context manager from `db.py`:

```python
from sharetree.db import get_session

with get_session() as session:
    session.add(obj)
    session.commit()
```

### Pydantic models

Use `pydantic.BaseModel` for request/response bodies in FastAPI route signatures.

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

Admin endpoints live under `/api/v1/admin/`. Authentication for admin routes is not yet implemented.

## Database

- **Engine:** SQLite at `{DATA_PATH}/sharetree.db`
- **Schema management:** Tables are created automatically on app startup via `init_db()` — no migration tool is configured.
- **Single model:** `AccessCode` (`src/sharetree/models/all.py`)

### AccessCode schema

| Column | Type | Notes |
|---|---|---|
| `code` | `str` (PK) | URL-safe token, 16 bytes (`secrets.token_urlsafe(16)`) |
| `patterns` | `str` (JSON) | List of `fnmatch` glob patterns; accessed via Python property |
| `nick` | `str \| None` | Optional human-readable label |

## Security Model

### Access codes

- Users activate access codes via `POST /api/v1/access/activate`.
- Active codes are stored in the encrypted server-side session (Starlette `SessionMiddleware`).
- Each code maps to a list of `fnmatch` patterns controlling which paths are visible.

### File access patterns

Patterns follow `fnmatch` syntax and are matched against the full path from `SHARE_ROOT`:

```
/docs/*          → everything directly inside /docs/
/docs/sub/deep.txt  → exact file
/reports/**      → fnmatch `*` matches across `/` so this is recursive
```

### Path traversal protection

`services/browse.py` resolves the requested path with `.resolve()` and checks that the result is relative to `SHARE_ROOT.resolve()` before proceeding. Symlink escapes are blocked.

## Testing

- Tests live **co-located** with the code they test, inside a `tests/` subdirectory:
  `src/sharetree/services/tests/test_browse.py`
- Use `pytest` with the `tmp_path` fixture for filesystem-based tests.
- Mock `SHARE_ROOT` by patching `sharetree.services.browse.SHARE_ROOT`.

Run all tests:

```bash
pytest
```

## Code Style

- **Formatter/linter:** Ruff (`ruff format`, `ruff check --fix`)
- **Line length:** 120 characters
- **Type checker:** `ty check` (not Mypy)
- **No pre-commit hooks** — run `bin/verify` manually before pushing
- Keep functions small and focused; avoid deep nesting

## Git Conventions

Commit messages follow the pattern `category: description`:

```
api: add health endpoint
browse: fix path traversal edge case
sql: add nick column to access_codes
dev: add ruff to verify script
tests: cover symlink escape scenarios
```

Categories seen in this repo: `api`, `sql`, `dev`, `admin`, `browse`, `access`, `tests`

## Not Yet Implemented

The following features are planned but not yet built (see README for the full checklist):

- File download / upload
- Admin authentication (trusted headers, magic credentials, IP subnet)
- Forward-auth API endpoint (for reverse proxy integration)
- Vue.js frontend (static files directory is a placeholder)
- Docker deployment
- Redis support
- CI/CD pipeline
