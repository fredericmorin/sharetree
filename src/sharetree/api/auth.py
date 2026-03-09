from urllib.parse import unquote

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

from sharetree.logging import log_download
from sharetree.services import access as access_service
from sharetree.services import browse as browse_service

router = APIRouter()

_DOWNLOAD_PREFIX = "/"


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
        raise HTTPException(status_code=400, detail=f"X-Forwarded-Uri must start with {_DOWNLOAD_PREFIX}")

    path = unquote(x_forwarded_uri[len(_DOWNLOAD_PREFIX) :])

    if not path:
        raise HTTPException(status_code=400, detail="Empty file path")

    session_id: str | None = request.session.get("session_id")
    active = access_service.get_session_access_codes(session_id) if session_id else None
    codes: list[str] = active["valid_active_codes"] if active else []
    patterns: list[str] = active["accessible_paths"] if active else []
    nicks: list[str] = [d["nick"] for d in active["active_code_details"] if d["nick"]] if active else []

    request.state.extras = dict(
        auth_codes=codes,
        auth_patterns=patterns,
        download_path=path,
    )

    browse_service.get_file_path(path, patterns)  # raises HTTPException 403/404 on denial

    client_ip: str | None = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or request.headers.get("x-real-ip")
        or (request.client.host if request.client else None)
    )
    log_download(
        event="forward_auth_allowed",
        path=path,
        session_id=session_id,
        nicks=nicks,
        codes=codes,
        client_ip=client_ip,
    )

    return AuthResponse(allowed=True)
