from api_exception import ResponseModel
from fastapi import APIRouter
from pydantic import BaseModel

from sharetree.services import access as access_service

router = APIRouter(prefix="/access")


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
