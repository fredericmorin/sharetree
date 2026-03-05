import secrets
from typing import TypedDict

from fastapi import APIRouter

from sharetree.db import get_session
from sharetree.models.all import AccessCode

router = APIRouter(prefix="/access")


class ActiveAccessCodes(TypedDict):
    valid_active_codes: list[str]
    accessible_paths: list[str]


def resolve_access_code_paths(access_codes: list[str]) -> ActiveAccessCodes:
    with get_session() as session:
        rows = session.query(AccessCode).filter(AccessCode.code.in_(access_codes)).all()
    valid_codes = {row.code: row.patterns for row in rows}
    paths = set().union(*list(valid_codes.values())) if valid_codes else set()
    return ActiveAccessCodes(valid_active_codes=list(valid_codes.keys()), accessible_paths=list(paths))


def prune_invalid_access_codes(access_codes: list[str]) -> list[str]:
    with get_session() as session:
        rows = session.query(AccessCode.code).filter(AccessCode.code.in_(access_codes)).all()
    return [row.code for row in rows]


def create_access_code(patterns: list[str], nick: str | None = None) -> str:
    code = secrets.token_urlsafe(16)
    with get_session() as session:
        entry = AccessCode(code=code, _patterns_json="", nick=nick)
        entry.patterns = patterns
        session.add(entry)
        session.commit()
    return code
