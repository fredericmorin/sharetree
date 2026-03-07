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

- [ ] Docker (Python app)
  - [ ] Option to bundle Caddy with forward-auth
- [ ] Redis session store

## Refs

- https://medium.com/@aahana.khanal11/scaling-a-fastapi-application-handling-multiple-requests-at-once-e5c128720c95
