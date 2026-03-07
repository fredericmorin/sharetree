import fnmatch
from pathlib import Path
from typing import Literal

from fastapi import HTTPException
from pydantic import BaseModel

from sharetree.settings import settings


class DirectoryEntry(BaseModel):
    name: str
    type: Literal["file", "directory"]
    size: int | None
    path: str


def _is_accessible(rel_path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(rel_path, p) for p in patterns)


def _dir_is_accessible(path: str, patterns: list[str]) -> bool:
    # A directory is reachable if any pattern matches something directly inside
    # it, or if any pattern goes deeper (starts with the dir prefix).
    # Note: fnmatch `*` matches across `/`, so patterns are recursive by default.
    prefix = ("/" + path).replace("//", "/").rstrip("/") + "/"
    return any(fnmatch.fnmatch(prefix + "x", p) or p.startswith(prefix) for p in patterns)


def _entry_is_visible(entry_path: str, is_dir: bool, patterns: list[str]) -> bool:
    if _is_accessible(entry_path, patterns):
        return True
    if is_dir:
        return _dir_is_accessible(entry_path.lstrip("/"), patterns)
    return False


def _resolve_path(path: str, patterns: list[str]) -> tuple[Path, str]:
    if not patterns:
        raise HTTPException(status_code=403, detail="Access denied")

    target = (settings.SHARE_ROOT / path).resolve()

    if not target.is_relative_to(settings.SHARE_ROOT.resolve()):
        raise HTTPException(status_code=403, detail="Access denied")

    norm_path = ("/" + path).replace("//", "/")
    return target, norm_path


def get_file_path(path: str, patterns: list[str]) -> Path:
    target, norm_path = _resolve_path(path, patterns)

    if not _is_accessible(norm_path, patterns):
        raise HTTPException(status_code=403, detail="Access denied")

    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found")

    if not target.is_file():
        raise HTTPException(status_code=400, detail="Path is not a file")

    return target


def list_directory_entries(path: str, patterns: list[str]) -> list[DirectoryEntry]:
    target, norm_path = _resolve_path(path, patterns)

    folder_matched = _is_accessible(norm_path, patterns)

    if not folder_matched and not _dir_is_accessible(path, patterns):
        raise HTTPException(status_code=403, detail="Access denied")

    if not target.exists():
        raise HTTPException(status_code=404, detail="Path not found")

    if not target.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    entries = [
        DirectoryEntry(
            name=entry.name,
            type="directory" if entry.is_dir() else "file",
            size=entry.stat().st_size if entry.is_file() else None,
            path=f"/{path}/{entry.name}".replace("//", "/"),
        )
        for entry in sorted(target.iterdir(), key=lambda e: (e.is_file(), e.name))
        if folder_matched or _entry_is_visible(f"/{path}/{entry.name}".replace("//", "/"), entry.is_dir(), patterns)
    ]
    return entries
