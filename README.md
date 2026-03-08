# sharetree

File sharing via access codes. Administrators share server-side folder trees with external users using short-lived access codes that map to `fnmatch`-style glob patterns.

## Dev

Tech stack: Python / FastAPI / SQLAlchemy / SQLite / Vue.js 3 / Vite / Tailwind CSS v4 / shadcn-vue

```sh
make check       # installs .venv, runs ruff + ty + pytest
make frontend    # build Vue.js frontend
sharetree        # start dev server on :8000
```

See [CLAUDE.md](CLAUDE.md) for full developer documentation.

## Featureset

- [x] Share existing folder tree (read-only, no upload)
- [x] Access code system — trade code for session access
  - [x] fnmatch glob pattern-based file/folder visibility
  - [x] File download with access control
- [x] Vue.js frontend — browse files, activate access codes
  - [x] Tailwind CSS v4 + shadcn-vue design system
  - [x] Dark/light mode toggle
  - [x] Loading skeletons, file-type icons, search/filter, copy-to-clipboard
- [x] Admin API — create access codes with patterns and optional label
- [x] Admin authentication — session login page (password) or trusted headers (reverse proxy)
- [x] Session tracking — records which user session first claimed each access code
  - [x] Admin page to browse claims grouped by session with pagination
- [x] Admin file browser — browse the full server file tree and create access codes from any file or folder
- [ ] Custom forward-auth API endpoint
## Deploy

- [x] Docker — multi-stage image with frontend build
- [ ] Redis session store

### Docker

```sh
docker build -t sharetree .
```

The app always listens on **port 8000**. Admin authentication works in two modes:

#### Default mode (built-in admin login page)

Admin routes are protected by a session-based login page at `/admin/login`.
Set `SHARETREE_ADMIN_PASSWORD` to the desired admin password.

```yaml
services:
  sharetree:
    image: sharetree
    build: .
    ports:
      - "8000:8000"
    volumes:
      - sharetree-data:/data
      - sharetree-files:/files
    environment:
      SHARETREE_SESSION_SECRET: <random-secret>
      SHARETREE_ADMIN_PASSWORD: <admin-password>
    restart: unless-stopped

volumes:
  sharetree-data:
  sharetree-files:
```

#### Trusted-headers mode (behind an existing reverse proxy)

Admin access is controlled by the `Remote-Groups: admins` header forwarded by your upstream proxy.
Set `SHARETREE_TRUST_HEADERS=true` to enable header validation (disables the login page).

```yaml
services:
  sharetree:
    image: sharetree
    build: .
    ports:
      - "8000:8000"
    volumes:
      - sharetree-data:/data
      - sharetree-files:/files
    environment:
      SHARETREE_SESSION_SECRET: <random-secret>
      SHARETREE_TRUST_HEADERS: "true"
    restart: unless-stopped

volumes:
  sharetree-data:
  sharetree-files:
```

```sh
docker compose up -d
```

#### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SHARETREE_SESSION_SECRET` | yes | — | Secret key for encrypted session cookies (generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`) |
| `SHARETREE_ADMIN_PASSWORD` | when `TRUST_HEADERS` is falsy | — | Password for the built-in admin login page |
| `SHARETREE_TRUST_HEADERS` | no | `false` | Trust `Remote-Groups` header from upstream proxy; disables the admin login page |
| `SHARETREE_SHARE_ROOT` | no | `/files` | Path to the folder tree to share (mount a volume here) |
| `SHARETREE_DATA_PATH` | no | `/data` | Path where the SQLite database is stored (mount a volume here) |

## Refs

- https://medium.com/@aahana.khanal11/scaling-a-fastapi-application-handling-multiple-requests-at-once-e5c128720c95
