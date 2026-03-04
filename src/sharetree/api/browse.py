from fastapi import APIRouter, Request

from sharetree.services import access as access_service
from sharetree.services import browse as browse_service

router = APIRouter(prefix="/browse")


@router.get("/{path:path}")
@router.get("")
async def list_directory(request: Request, path: str = "") -> dict:
    codes: list[str] = request.session.get("access_codes", [])
    patterns: list[str] = access_service.resolve_access_code_paths(codes)["accessible_paths"]

    entries = browse_service.list_directory_entries(path, patterns)

    return {"path": path or "/", "entries": entries}
