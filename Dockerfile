# Stage 1: Build the Vue.js frontend
FROM node:22-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# favicon.ico must be present before build (vite uses emptyOutDir: false)
COPY static/ ../static/
RUN npm run build

# Stage 2: Build the Python virtual environment
FROM python:3.13-slim AS python-builder
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
COPY src/ src/
RUN uv sync --no-dev --compile-bytecode

# Stage 3: Caddy binary
FROM caddy:2-alpine AS caddy

# Stage 4: Minimal runtime image
FROM python:3.13-slim
# Install curl for HEALTHCHECK
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Caddy binary
COPY --from=caddy /usr/bin/caddy /usr/bin/caddy

WORKDIR /app

# Python environment (includes installed sharetree package)
COPY --from=python-builder /app/.venv /app/.venv
# Source tree (needed for editable install path references and alembic.ini resolution)
COPY --from=python-builder /app/src /app/src
# Alembic
COPY migrations/ migrations/
COPY alembic.ini .
# Built frontend assets
COPY --from=frontend-builder /app/static/ static/

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    SHARETREE_DATA_PATH=/data \
    SHARETREE_SHARE_ROOT=/files

VOLUME ["/data", "/files"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

ENTRYPOINT ["/entrypoint.sh"]
