from fastapi import APIRouter, Request
from pydantic import BaseModel

from sharetree.services import access as access_service
from sharetree.services import browse as browse_service
from sharetree.services.browse import DirectoryEntry

router = APIRouter(prefix="/browse")


class BrowseResponse(BaseModel):
    path: str
    entries: list[DirectoryEntry]


@router.get("/{path:path}", response_model=BrowseResponse)
@router.get("", response_model=BrowseResponse)
async def list_directory(request: Request, path: str = "") -> BrowseResponse:
    session_id: str | None = request.session.get("session_id")
    patterns: list[str] = access_service.get_session_access_codes(session_id)["accessible_paths"] if session_id else []

    entries = browse_service.list_directory_entries(path, patterns)

    return BrowseResponse(path=path or "/", entries=entries)
