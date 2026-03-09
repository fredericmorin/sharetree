from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from sharetree.logging import log_download
from sharetree.services import access as access_service
from sharetree.services import browse as browse_service

router = APIRouter(prefix="/download")


@router.get("/{path:path}")
async def download_file(request: Request, path: str) -> FileResponse:
    session_id: str | None = request.session.get("session_id")
    active = access_service.get_session_access_codes(session_id) if session_id else None
    patterns: list[str] = active["accessible_paths"] if active else []
    nicks: list[str] = [d["nick"] for d in active["active_code_details"] if d["nick"]] if active else []
    codes: list[str] = active["valid_active_codes"] if active else []

    file_path = browse_service.get_file_path(path, patterns)

    client_ip: str | None = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or request.headers.get("x-real-ip")
        or (request.client.host if request.client else None)
    )
    log_download(
        event="download",
        path=path,
        session_id=session_id,
        nicks=nicks,
        codes=codes,
        client_ip=client_ip,
    )

    return FileResponse(file_path, filename=file_path.name)
