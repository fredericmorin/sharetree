from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter(prefix="/access")


MAGIC_CODES = {
    "abc": ["/"],
}


class AccessCodes(BaseModel):
    active_codes: list[str]
    paths: list[str]


@router.get("/")
async def get_access_code(request: Request) -> AccessCodes:
    codes: list[str] = request.session.get("access_codes", [])
    valid_codes = {code: MAGIC_CODES[code] for code in codes if code in MAGIC_CODES}
    paths = set().union(*list(valid_codes.values()))
    return AccessCodes.model_construct(active_codes=list(valid_codes.keys()), paths=list(paths))


class AccessCodeRequest(BaseModel):
    code: str


@router.post("/activate")
async def activate_access_code(body: AccessCodeRequest, request: Request) -> dict:
    codes: list[str] = request.session.get("access_codes", [])
    if body.code in MAGIC_CODES:
        codes.append(body.code)
    request.session["access_codes"] = codes
    return {"status": "ok"}
