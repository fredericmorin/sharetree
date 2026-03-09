from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from api_exception import register_exception_handlers
from fastapi import APIRouter, Depends, FastAPI
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware

from sharetree.api.access import me_router
from sharetree.api.access import router as access_router
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
from sharetree.logging import LoggingMiddleware, configure_logging
from sharetree.settings import settings

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    run_migrations()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(LoggingMiddleware)  # type: ignore[arg-type]
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)  # type: ignore[arg-type]
register_exception_handlers(app)  # consistent error and success api responses

api = APIRouter(prefix="/api/v1")
api.include_router(health_router)
api.include_router(headers_router)
api.include_router(me_router)
api.include_router(access_router)
api.include_router(browse_router)
api.include_router(auth_router)

if not settings.TRUST_HEADERS:
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
