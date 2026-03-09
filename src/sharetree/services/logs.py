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


def _count_lines(path: Path) -> int:
    """Count newline-terminated lines without loading the file into memory."""
    count = 0
    buf = bytearray(65536)
    with path.open("rb") as f:
        while n := f.readinto(buf):
            count += buf[:n].count(b"\n")
    return count


def _parse_entry(line: str) -> DownloadLogEntry | None:
    line = line.strip()
    if not line:
        return None
    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        return None
    return DownloadLogEntry(
        timestamp=data.get("timestamp", ""),
        event=data.get("event", ""),
        path=data.get("path", ""),
        session_id=data.get("session_id"),
        nicks=data.get("nicks", []),
        codes=data.get("codes", []),
        client_ip=data.get("client_ip"),
    )


def read_download_logs(page: int, page_size: int = PAGE_SIZE) -> DownloadLogsPage:
    """Return a paginated slice of download log entries, newest-first.

    Files are processed one at a time. Only the file(s) that overlap with the
    requested page window are read into memory (at most two 10 MB files).
    """
    log_files = _log_files()

    # Count lines per file with O(1) memory (scan for newlines only).
    file_line_counts: list[tuple[Path, int]] = []
    for log_file in log_files:
        try:
            file_line_counts.append((log_file, _count_lines(log_file)))
        except OSError:
            continue

    total_entries = sum(c for _, c in file_line_counts)
    total_pages = max(1, math.ceil(total_entries / page_size))
    page = min(max(1, page), total_pages)

    # How many entries to skip from the newest-first stream before collecting.
    to_skip = (page - 1) * page_size
    to_collect = page_size

    entries: list[DownloadLogEntry] = []
    global_offset = 0  # entries already consumed from the newest-first stream

    for log_file, file_count in file_line_counts:
        if to_collect == 0:
            break

        file_end = global_offset + file_count

        if file_end <= to_skip:
            # This entire file falls before our window — skip without reading.
            global_offset = file_end
            continue

        # This file overlaps the window: read it (one file at a time).
        try:
            with log_file.open(encoding="utf-8") as fh:
                raw_lines = fh.readlines()
        except OSError:
            global_offset = file_end
            continue

        # Lines within the file are oldest→newest; reverse for newest-first.
        reversed_lines = raw_lines[::-1]

        # How many lines from this file's reversed stream to skip?
        local_skip = max(0, to_skip - global_offset)
        for raw_line in reversed_lines[local_skip : local_skip + to_collect]:
            entry = _parse_entry(raw_line)
            if entry is not None:
                entries.append(entry)
                to_collect -= 1
                if to_collect == 0:
                    break

        global_offset = file_end

    return DownloadLogsPage(
        entries=entries,
        page=page,
        total_entries=total_entries,
        total_pages=total_pages,
    )
