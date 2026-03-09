import json
import math
from pathlib import Path
from typing import TypedDict

from sharetree.settings import settings

PAGE_SIZE = 50


class DownloadLogEntry(TypedDict):
    timestamp: str
    event: str
    path: str
    session_id: str | None
    nicks: list[str]
    codes: list[str]
    client_ip: str | None


class DownloadLogsPage(TypedDict):
    entries: list[DownloadLogEntry]
    page: int
    total_entries: int
    total_pages: int


def _log_files() -> list[Path]:
    """Return existing download log files ordered newest-first (current, .1, .2, …)."""
    base = settings.DATA_PATH / "downloads.log"
    candidates = [base] + [Path(f"{base}.{i}") for i in range(1, settings.DOWNLOAD_LOG_BACKUP_COUNT + 1)]
    return [p for p in candidates if p.exists()]


def read_download_logs(page: int, page_size: int = PAGE_SIZE) -> DownloadLogsPage:
    """Read all rotated download log files and return a paginated slice, newest-first."""
    lines: list[str] = []
    for log_file in _log_files():
        try:
            file_lines = log_file.read_text(encoding="utf-8").splitlines()
            # Current log file: lines are oldest→newest; reverse so newest come first
            lines.extend(reversed(file_lines))
        except OSError:
            continue

    total_entries = len(lines)
    total_pages = max(1, math.ceil(total_entries / page_size))
    page = min(max(1, page), total_pages)

    offset = (page - 1) * page_size
    page_lines = lines[offset : offset + page_size]

    entries: list[DownloadLogEntry] = []
    for line in page_lines:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        entries.append(
            DownloadLogEntry(
                timestamp=data.get("timestamp", ""),
                event=data.get("event", ""),
                path=data.get("path", ""),
                session_id=data.get("session_id"),
                nicks=data.get("nicks", []),
                codes=data.get("codes", []),
                client_ip=data.get("client_ip"),
            )
        )

    return DownloadLogsPage(
        entries=entries,
        page=page,
        total_entries=total_entries,
        total_pages=total_pages,
    )
