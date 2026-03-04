import fnmatch
from typing import Any

from fastapi import HTTPException

from sharetree.settings import SHARE_ROOT


def _is_accessible(rel_path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel_path, p) for p in patterns)


def _dir_is_accessible(path: str, patterns: list[str]) -> bool:
    # A directory is reachable if any pattern matches something directly inside
    # it, or if any pattern goes deeper (starts with the dir prefix).
    # Note: fnmatch `*` matches across `/`, so patterns are recursive by default.
    prefix = ("/" + path).replace("//", "/").rstrip("/") + "/"
    return any(fnmatch.fnmatch(prefix + "x", p) or p.startswith(prefix) for p in patterns)


def list_directory_entries(path: str, patterns: list[str]) -> list[dict[str, Any]]:
    if not patterns:
        raise HTTPException(status_code=403, detail="Access denied")

    target = (SHARE_ROOT / path).resolve()

    if not target.is_relative_to(SHARE_ROOT.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")

    if not _dir_is_accessible(path, patterns):
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
    return entries
