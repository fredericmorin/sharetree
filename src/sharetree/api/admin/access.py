from api_exception import ResponseModel
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from sharetree.services import access as access_service

router = APIRouter(prefix="/access")

PAGE_SIZE = 200


class CreateAccessCodeRequest(BaseModel):
    patterns: list[str]
    nick: str | None


class CreateAccessCodeResponse(BaseModel):
    code: str
    patterns: list[str]
    nick: str | None


@router.post("/create", response_model=ResponseModel[CreateAccessCodeResponse])
async def create_access_code(body: CreateAccessCodeRequest) -> ResponseModel[CreateAccessCodeResponse]:
    code = access_service.create_access_code(body.patterns, body.nick)
    return ResponseModel(data=CreateAccessCodeResponse(code=code, patterns=body.patterns, nick=body.nick))


class SessionCodeEntry(BaseModel):
    code: str
    nick: str | None
    patterns: list[str]


class SessionGroup(BaseModel):
    session_id: str | None
    codes: list[SessionCodeEntry]


class SessionsPageResponse(BaseModel):
    sessions: list[SessionGroup]
    page: int
    total_sessions: int
    total_pages: int


class RevokeAccessCodeRequest(BaseModel):
    code: str


@router.delete("/revoke", response_model=ResponseModel[None])
async def revoke_access_code(body: RevokeAccessCodeRequest) -> ResponseModel[None]:
    found = access_service.revoke_access_code(body.code)
    if not found:
        raise HTTPException(status_code=404, detail="Access code not found")
    return ResponseModel(data=None)


class UpdateNickRequest(BaseModel):
    code: str
    nick: str | None


@router.post("/nick", response_model=ResponseModel[None])
async def update_nick(body: UpdateNickRequest) -> ResponseModel[None]:
    found = access_service.update_access_code_nick(body.code, body.nick)
    if not found:
        raise HTTPException(status_code=404, detail="Access code not found")
    return ResponseModel(data=None)


class ReleaseAccessCodeRequest(BaseModel):
    code: str


@router.post("/release", response_model=ResponseModel[None])
async def release_access_code(body: ReleaseAccessCodeRequest) -> ResponseModel[None]:
    found = access_service.release_access_code(body.code)
    if not found:
        raise HTTPException(status_code=404, detail="Access code not found")
    return ResponseModel(data=None)


@router.get("/sessions", response_model=ResponseModel[SessionsPageResponse])
async def list_sessions(page: int = Query(1, ge=1)) -> ResponseModel[SessionsPageResponse]:
    result = access_service.list_sessions_page(page=page, page_size=PAGE_SIZE)
    return ResponseModel(
        data=SessionsPageResponse(
            sessions=[
                SessionGroup(
                    session_id=g["session_id"],
                    codes=[
                        SessionCodeEntry(code=c["code"], nick=c["nick"], patterns=c["patterns"]) for c in g["codes"]
                    ],
                )
                for g in result["sessions"]
            ],
            page=result["page"],
            total_sessions=result["total_sessions"],
            total_pages=result["total_pages"],
        )
    )
