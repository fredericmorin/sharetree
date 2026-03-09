from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from sharetree.services import access as access_service
from sharetree.services import browse as browse_service

router = APIRouter(prefix="/download")


@router.get("/{path:path}")
async def download_file(request: Request, path: str) -> FileResponse:
    session_id: str | None = request.session.get("session_id")
    patterns: list[str] = access_service.get_session_access_codes(session_id)["accessible_paths"] if session_id else []

    file_path = browse_service.get_file_path(path, patterns)

    return FileResponse(file_path, filename=file_path.name)
