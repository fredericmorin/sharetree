# sharetree

File sharing via access codes. Administrators share server-side folder trees with external users using short-lived access codes that map to `fnmatch`-style glob patterns.

## Dev

Tech stack: Python / FastAPI / SQLAlchemy / SQLite / Vue.js 3 / Vite

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
- [x] Admin API — create access codes with patterns and optional label
- [ ] Admin authentication (trusted headers / magic credentials / IP subnet)
- [ ] Custom forward-auth API endpoint
## Deploy

- [x] Docker — multi-stage image with frontend build and optional Caddy reverse proxy
- [ ] Redis session store

### Docker

```sh
docker build -t sharetree .
```

#### Standalone mode (Caddy + basic auth on admin routes)

Listens on **port 80**. Admin routes (`/api/v1/admin/*`) require HTTP basic auth.
The authenticated user's groups are forwarded to the app as a trusted header.

```sh
docker run -d \
  -p 80:80 \
  -v sharetree-data:/data \
  -v sharetree-files:/files \
  -e SHARETREE_SESSION_SECRET=<random-secret> \
  -e SHARETREE_ADMIN_PASSWORD=<admin-password> \
  sharetree
```

#### Trusted-headers mode (behind an existing reverse proxy)

Listens on **port 8000**. Admin access is controlled by the `Remote-Groups: admins` header
forwarded by your upstream proxy. Set `SHARETREE_TRUST_HEADERS=true` to enable header validation.

```sh
docker run -d \
  -p 8000:8000 \
  -v sharetree-data:/data \
  -v sharetree-files:/files \
  -e SHARETREE_SESSION_SECRET=<random-secret> \
  -e SHARETREE_TRUST_HEADERS=true \
  sharetree
```

#### Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SHARETREE_SESSION_SECRET` | yes | — | Secret key for encrypted session cookies |
| `SHARETREE_ADMIN_PASSWORD` | when `TRUST_HEADERS` is falsy | — | Password for Caddy basic auth on admin routes |
| `SHARETREE_TRUST_HEADERS` | no | `false` | Trust `Remote-Groups` header from upstream proxy; disables Caddy |
| `SHARETREE_SHARE_ROOT` | no | `/files` | Path to the folder tree to share (mount a volume here) |
| `SHARETREE_DATA_PATH` | no | `/data` | Path where the SQLite database is stored (mount a volume here) |
| `SHARETREE_DEV` | no | `false` | Enable uvicorn auto-reload (development only) |

## Refs

- https://medium.com/@aahana.khanal11/scaling-a-fastapi-application-handling-multiple-requests-at-once-e5c128720c95
