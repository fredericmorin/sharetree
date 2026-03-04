from typing import TypedDict

from fastapi import APIRouter

router = APIRouter(prefix="/access")


MAGIC_CODES = {
    "abc": ["/*"],
}


class ActiveAccessCodes(TypedDict):
    valid_active_codes: list[str]
    accessible_paths: list[str]


def resolve_access_code_paths(access_codes: list[str]) -> ActiveAccessCodes:
    valid_codes = {code: MAGIC_CODES[code] for code in access_codes if code in MAGIC_CODES}
    paths = set().union(*list(valid_codes.values()))
    return ActiveAccessCodes(valid_active_codes=list(valid_codes.keys()), accessible_paths=list(paths))


def prune_invalid_access_codes(access_codes: list[str]) -> list[str]:
    valid_codes = set(access_codes) & MAGIC_CODES.keys()
    return list(valid_codes)
