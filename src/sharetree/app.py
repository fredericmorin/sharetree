from api_exception import register_exception_handlers
from fastapi import APIRouter, FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from sharetree import settings
from sharetree.api.access import router as access_router
from sharetree.api.health import router as health_router

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=settings.SESSION_SECRET)
register_exception_handlers(app)  # consistent error and success api responses

api = APIRouter(prefix="/api/v1")
api.include_router(health_router)
api.include_router(access_router)


@api.get("", include_in_schema=False)
async def api_root() -> RedirectResponse:
    return RedirectResponse(url="/redoc")


app.include_router(api)


@app.get("/")
async def root() -> str:
    return "sup"


app.mount("/", StaticFiles(directory="static"), name="static")
