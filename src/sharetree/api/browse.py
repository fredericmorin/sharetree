import fnmatch

from fastapi import APIRouter, HTTPException, Request

from sharetree.services import access as access_service
from sharetree.settings import SHARE_ROOT

router = APIRouter(prefix="/browse")


def _is_accessible(rel_path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel_path, p) for p in patterns)


@router.get("/{path:path}")
@router.get("")
async def list_directory(request: Request, path: str = "") -> dict:
    codes: list[str] = request.session.get("access_codes", [])
    patterns: list[str] = access_service.resolve_access_code_paths(codes)["accessible_paths"]

    if not patterns:
        raise HTTPException(status_code=403, detail="Access denied")

    # if not path.startswith("/"):
    #     path = f"/{path}"
    target = (SHARE_ROOT / path).resolve()

    print(target)

    if not target.is_relative_to(SHARE_ROOT.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")

    if not target.exists():
        raise HTTPException(status_code=404, detail="Path not found")

    if not target.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    entries = [
        {
            "name": entry.name,
            "type": "directory" if entry.is_dir() else "file",
            "size": entry.stat().st_size if entry.is_file() else None,
            "path": f"/{path}/{entry.name}".replace("//", "/"),
        }
        for entry in sorted(target.iterdir(), key=lambda e: (e.is_file(), e.name))
        if _is_accessible(f"/{path}/{entry.name}".replace("//", "/"), patterns)
    ]

    return {"path": path or "/", "entries": entries}
