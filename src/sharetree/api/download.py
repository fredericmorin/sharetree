from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from sharetree.services import access as access_service
from sharetree.services import browse as browse_service

router = APIRouter(prefix="/download")


@router.get("/{path:path}")
async def download_file(request: Request, path: str) -> FileResponse:
    codes: list[str] = request.session.get("access_codes", [])
    patterns: list[str] = access_service.resolve_access_code_paths(codes)["accessible_paths"]

    file_path = browse_service.get_file_path(path, patterns)

    return FileResponse(file_path, filename=file_path.name)
