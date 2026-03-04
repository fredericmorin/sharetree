from pathlib import Path

from fastapi import APIRouter, HTTPException

from sharetree.settings import SHARE_ROOT

router = APIRouter(prefix="/browse")

share_root = Path(SHARE_ROOT)


@router.get("/{path:path}")
@router.get("")
async def list_directory(path: str = "") -> dict:
    target = (share_root / path).resolve()

    if not target.is_relative_to(share_root.resolve()):
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
        }
        for entry in sorted(target.iterdir(), key=lambda e: (e.is_file(), e.name))
    ]

    return {"path": path or "/", "entries": entries}
