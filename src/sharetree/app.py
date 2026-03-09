import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import structlog
from api_exception import register_exception_handlers
from fastapi import APIRouter, Depends, FastAPI
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from sharetree.settings import settings
from sharetree.api.access import me_router, router as access_router
from sharetree.api.admin.access import router as admin_access_router
from sharetree.api.admin.auth import router as admin_auth_router
from sharetree.api.admin.browse import router as admin_browse_router
from sharetree.api.admin.deps import require_admin_group
from sharetree.api.auth import router as auth_router
from sharetree.api.browse import router as browse_router
from sharetree.api.download import router as download_router
from sharetree.api.headers import router as headers_router
from sharetree.api.health import router as health_router
from sharetree.db import run_migrations
from sharetree.logging import configure_logging

configure_logging()

log = structlog.get_logger()

_LOGGED_REQUEST_HEADERS = {"user-agent", "content-type", "content-length", "referer", "origin"}
_LOGGED_RESPONSE_HEADERS = {"content-type", "content-length"}


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()

        req_headers = {k: v for k, v in request.headers.items() if k.lower() in _LOGGED_REQUEST_HEADERS}

        # Best-effort client IP: prefer forwarded headers set by a reverse proxy.
        client_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or request.headers.get("x-real-ip")
            or (request.client.host if request.client else None)
        )

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        resp_headers = {k: v for k, v in response.headers.items() if k.lower() in _LOGGED_RESPONSE_HEADERS}

        log.info(
            "request",
            method=request.method,
            path=request.url.path,
            query=str(request.url.query) or None,
            status=response.status_code,
            duration_ms=duration_ms,
            client_ip=client_ip,
            **{f"req_{k.replace('-', '_')}": v for k, v in req_headers.items()},
            **{f"res_{k.replace('-', '_')}": v for k, v in resp_headers.items()},
        )

        return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    run_migrations()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(LoggingMiddleware)  # type: ignore[arg-type]
if settings.REDIS_URL:
    from sharetree.session import RedisSessionMiddleware

    app.add_middleware(RedisSessionMiddleware, redis_url=settings.REDIS_URL)  # type: ignore[arg-type]
else:
    from starlette.middleware.sessions import SessionMiddleware

    app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)  # type: ignore[arg-type]
register_exception_handlers(app)  # consistent error and success api responses

api = APIRouter(prefix="/api/v1")
api.include_router(health_router)
api.include_router(headers_router)
api.include_router(me_router)
api.include_router(access_router)
api.include_router(browse_router)
api.include_router(auth_router)

api.include_router(admin_auth_router, prefix="/admin")

admin = APIRouter(prefix="/admin", dependencies=[Depends(require_admin_group)])
admin.include_router(admin_access_router)
admin.include_router(admin_browse_router)
api.include_router(admin)

app.include_router(api)
app.include_router(download_router)

_STATIC_DIR = Path("static")


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str) -> FileResponse:
    # Serve real static files (favicon, etc.) directly; fall back to index.html for SPA routes.
    candidate = _STATIC_DIR / full_path
    if candidate.is_file():
        return FileResponse(candidate)
    return FileResponse(_STATIC_DIR / "index.html")
