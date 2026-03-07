from contextlib import asynccontextmanager
from typing import AsyncIterator

from api_exception import register_exception_handlers
from fastapi import APIRouter, Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from sharetree.settings import settings
from sharetree.api.access import router as access_router
from sharetree.api.admin.access import router as admin_access_router
from sharetree.api.admin.auth import router as admin_auth_router
from sharetree.api.admin.deps import require_admin_group
from sharetree.api.browse import router as browse_router
from sharetree.api.download import router as download_router
from sharetree.api.health import router as health_router
from sharetree.db import run_migrations


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    run_migrations()
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)  # type: ignore
register_exception_handlers(app)  # consistent error and success api responses

api = APIRouter(prefix="/api/v1")
api.include_router(health_router)
api.include_router(access_router)
api.include_router(browse_router)

api.include_router(admin_auth_router, prefix="/admin")

admin = APIRouter(prefix="/admin", dependencies=[Depends(require_admin_group)])
admin.include_router(admin_access_router)
api.include_router(admin)

app.include_router(api)
app.include_router(download_router)


app.mount("/", StaticFiles(directory="static", html=True), name="static")
