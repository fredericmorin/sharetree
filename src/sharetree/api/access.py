import uuid

from api_exception import APIException, BaseExceptionCode, ResponseModel
from fastapi import APIRouter, Header, Request
from pydantic import BaseModel

from sharetree.api.admin.deps import check_is_admin
from sharetree.services import access as access_service

me_router = APIRouter(prefix="/me")
router = APIRouter(prefix="/access_code")


class ActiveCodeDetail(BaseModel):
    code: str
    nick: str | None
    patterns: list[str]


class MeResponse(BaseModel):
    active_codes: list[str]
    paths: list[str]
    active_code_details: list[ActiveCodeDetail]
    is_admin: bool


@me_router.get(
    "",
    response_model=ResponseModel[MeResponse],
)
async def get_me(request: Request, remote_groups: str | None = Header(default=None)) -> ResponseModel[MeResponse]:
    session_id: str | None = request.session.get("session_id")
    active_access_codes = (
        access_service.get_session_access_codes(session_id)
        if session_id
        else access_service.ActiveAccessCodes(valid_active_codes=[], accessible_paths=[], active_code_details=[])
    )
    is_admin = check_is_admin(request, remote_groups)
    return ResponseModel(
        data=MeResponse.model_construct(
            active_codes=active_access_codes["valid_active_codes"],
            paths=active_access_codes["accessible_paths"],
            active_code_details=[
                ActiveCodeDetail(code=d["code"], nick=d["nick"], patterns=d["patterns"])
                for d in active_access_codes["active_code_details"]
            ],
            is_admin=is_admin,
        )
    )


class AccessCodeExceptionCode(BaseExceptionCode):
    ACCESS_CODE_NOT_FOUND = ("NOT_FOUND", "Access code not found.")


def _get_or_create_session_id(request: Request) -> str:
    if "session_id" not in request.session:
        request.session["session_id"] = str(uuid.uuid4())
    return request.session["session_id"]


@router.post("/{code}/activate", response_model=ResponseModel[None])
async def activate_access_code(code: str, request: Request) -> ResponseModel[None]:
    session_id = _get_or_create_session_id(request)

    if access_service.is_access_code_active_for_session(code, session_id):
        return ResponseModel(error_code="ALREADY_ACTIVE")

    if not access_service.is_access_code_unclaimed(code):
        raise APIException(AccessCodeExceptionCode.ACCESS_CODE_NOT_FOUND, http_status_code=404)

    access_service.set_access_code_session(code, session_id)
    return ResponseModel()
