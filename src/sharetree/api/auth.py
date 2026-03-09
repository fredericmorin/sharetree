from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from sharetree.services import access as access_service
from sharetree.services import browse as browse_service

router = APIRouter()

_DOWNLOAD_PREFIX = "/download/"


class AuthResponse(BaseModel):
    allowed: bool


@router.get("/auth", response_model=AuthResponse)
async def forward_auth(
    request: Request,
    x_forwarded_uri: str | None = Header(default=None),
) -> AuthResponse:
    """Forward-auth endpoint for reverse proxy integration.

    The reverse proxy (e.g. Caddy forward_auth) calls this endpoint, forwarding the
    user's session cookie and the original request URI via X-Forwarded-Uri.
    Returns 200 if the user may access the file, or 403/404 otherwise.
    """
    if x_forwarded_uri is None:
        raise HTTPException(status_code=400, detail="X-Forwarded-Uri header is required")

    if not x_forwarded_uri.startswith(_DOWNLOAD_PREFIX):
        raise HTTPException(status_code=400, detail="X-Forwarded-Uri must start with /download/")

    path = x_forwarded_uri[len(_DOWNLOAD_PREFIX) :]

    if not path:
        raise HTTPException(status_code=400, detail="Empty file path")

    codes: list[str] = request.session.get("access_codes", [])
    patterns: list[str] = access_service.resolve_access_code_paths(codes)["accessible_paths"]

    browse_service.get_file_path(path, patterns)  # raises HTTPException 403/404 on denial

    return AuthResponse(allowed=True)
