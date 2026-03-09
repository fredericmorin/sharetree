import secrets

from api_exception import ResponseModel
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from sharetree.api.admin.deps import SESSION_ADMIN_KEY
from sharetree.settings import settings

router = APIRouter()


class AdminLoginRequest(BaseModel):
    password: str


class AdminStatusResponse(BaseModel):
    authenticated: bool


@router.post("/login", response_model=ResponseModel[AdminStatusResponse])
async def admin_login(body: AdminLoginRequest, request: Request) -> ResponseModel[AdminStatusResponse]:
    """Authenticate as admin using the configured ADMIN_PASSWORD.

    Only active when TRUST_HEADERS is False. When TRUST_HEADERS is True,
    admin access is controlled by the upstream proxy via Remote-Groups header.
    """
    if settings.TRUST_HEADERS:
        raise HTTPException(status_code=404, detail="Not found")

    admin_password = settings.ADMIN_PASSWORD
    if not admin_password:
        raise HTTPException(status_code=503, detail="Admin login is not configured")

    if not secrets.compare_digest(body.password, admin_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    request.session[SESSION_ADMIN_KEY] = True
    return ResponseModel(data=AdminStatusResponse(authenticated=True))


@router.post("/logout", response_model=ResponseModel[AdminStatusResponse])
async def admin_logout(request: Request) -> ResponseModel[AdminStatusResponse]:
    """Clear the admin session.

    Only active when TRUST_HEADERS is False. When TRUST_HEADERS is True,
    admin access is controlled by the upstream proxy via Remote-Groups header.
    """
    if settings.TRUST_HEADERS:
        raise HTTPException(status_code=404, detail="Not found")

    request.session.pop(SESSION_ADMIN_KEY, None)
    return ResponseModel(data=AdminStatusResponse(authenticated=False))
