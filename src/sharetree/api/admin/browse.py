from fastapi import APIRouter

from sharetree.api.browse import BrowseResponse
from sharetree.services import browse as browse_service

router = APIRouter(prefix="/browse")

# Pattern that grants access to every path under SHARE_ROOT.
# Python's fnmatch treats `*` as matching any character including `/`,
# so `/**` matches all absolute paths.
_ALL_PATTERNS: list[str] = ["/**"]


@router.get("/{path:path}", response_model=BrowseResponse)
@router.get("", response_model=BrowseResponse)
async def admin_list_directory(path: str = "") -> BrowseResponse:
    entries = browse_service.list_directory_entries(path, _ALL_PATTERNS)
    return BrowseResponse(path=path or "/", entries=entries)
