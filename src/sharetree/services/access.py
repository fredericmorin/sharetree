import math
import secrets
from typing import TypedDict

from sharetree.db import get_session
from sharetree.models.all import AccessCode


class ActiveCodeDetail(TypedDict):
    code: str
    nick: str | None


class ActiveAccessCodes(TypedDict):
    valid_active_codes: list[str]
    accessible_paths: list[str]
    active_code_details: list[ActiveCodeDetail]


def resolve_access_code_paths(access_codes: list[str]) -> ActiveAccessCodes:
    with get_session() as session:
        rows = session.query(AccessCode).filter(AccessCode.code.in_(access_codes)).all()
    all_paths: set[str] = set()
    details: list[ActiveCodeDetail] = []
    for row in rows:
        all_paths.update(row.patterns)
        details.append(ActiveCodeDetail(code=row.code, nick=row.nick))
    return ActiveAccessCodes(
        valid_active_codes=[row.code for row in rows],
        accessible_paths=list(all_paths),
        active_code_details=details,
    )


def prune_invalid_access_codes(access_codes: list[str]) -> list[str]:
    with get_session() as session:
        rows = session.query(AccessCode.code).filter(AccessCode.code.in_(access_codes)).all()
    return [row.code for row in rows]


def is_access_code_unclaimed(code: str) -> bool:
    """Return True if the code exists and has not yet been claimed by any session."""
    with get_session() as session:
        return (
            session.query(AccessCode.code).filter(AccessCode.code == code, AccessCode.session_id.is_(None)).first()
            is not None
        )


def create_access_code(patterns: list[str], nick: str | None = None) -> str:
    code = secrets.token_urlsafe(16)
    with get_session() as session:
        entry = AccessCode(code=code, _patterns_json="", nick=nick)
        entry.patterns = patterns
        session.add(entry)
        session.commit()
    return code


def set_access_code_session(code: str, session_id: str) -> None:
    """Record which session first claimed this access code."""
    with get_session() as session:
        row = session.get(AccessCode, code)
        if row and row.session_id is None:
            row.session_id = session_id
            session.commit()


class SessionCodeEntry(TypedDict):
    code: str
    nick: str | None


class SessionGroup(TypedDict):
    session_id: str | None
    codes: list[SessionCodeEntry]


class SessionsPage(TypedDict):
    sessions: list[SessionGroup]
    page: int
    total_sessions: int
    total_pages: int


def list_sessions_page(page: int, page_size: int) -> SessionsPage:
    """Return access codes grouped by session_id, paginated by distinct session_id values."""
    with get_session() as session:
        # Collect all distinct session_id values (including None), ordered
        all_rows = session.query(AccessCode.session_id).distinct().order_by(AccessCode.session_id).all()
        distinct_session_ids = [row.session_id for row in all_rows]

        total_sessions = len(distinct_session_ids)
        total_pages = max(1, math.ceil(total_sessions / page_size))
        page = min(page, total_pages)

        offset = (page - 1) * page_size
        page_session_ids = distinct_session_ids[offset : offset + page_size]

        # Fetch all codes for this page's session_ids (handle None separately)
        non_null_ids = [sid for sid in page_session_ids if sid is not None]
        include_null = None in page_session_ids
        if non_null_ids and include_null:
            from sqlalchemy import or_

            codes_rows = (
                session.query(AccessCode)
                .filter(or_(AccessCode.session_id.in_(non_null_ids), AccessCode.session_id.is_(None)))
                .order_by(AccessCode.session_id, AccessCode.code)
                .all()
            )
        elif non_null_ids:
            codes_rows = (
                session.query(AccessCode)
                .filter(AccessCode.session_id.in_(non_null_ids))
                .order_by(AccessCode.session_id, AccessCode.code)
                .all()
            )
        elif include_null:
            codes_rows = (
                session.query(AccessCode).filter(AccessCode.session_id.is_(None)).order_by(AccessCode.code).all()
            )
        else:
            codes_rows = []

    # Group by session_id in Python
    groups: dict[str | None, list[SessionCodeEntry]] = {sid: [] for sid in page_session_ids}
    for row in codes_rows:
        groups[row.session_id].append(SessionCodeEntry(code=row.code, nick=row.nick))

    sessions: list[SessionGroup] = [SessionGroup(session_id=sid, codes=groups[sid]) for sid in page_session_ids]

    return SessionsPage(
        sessions=sessions,
        page=page,
        total_sessions=total_sessions,
        total_pages=total_pages,
    )
