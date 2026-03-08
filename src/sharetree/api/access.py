import uuid

from api_exception import APIException, BaseExceptionCode, ResponseModel
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from sharetree.services import access as access_service

router = APIRouter(prefix="/access")


class ActiveCodeDetail(BaseModel):
    code: str
    nick: str | None


class AccessCodesResponse(BaseModel):
    active_codes: list[str]
    paths: list[str]
    active_code_details: list[ActiveCodeDetail]


@router.get(
    "",
    response_model=ResponseModel[AccessCodesResponse],
)
async def get_access_code(request: Request) -> ResponseModel[AccessCodesResponse]:
    codes: list[str] = request.session.get("access_codes", [])
    active_access_codes = access_service.resolve_access_code_paths(codes)
    return ResponseModel(
        data=AccessCodesResponse.model_construct(
            active_codes=active_access_codes["valid_active_codes"],
            paths=active_access_codes["accessible_paths"],
            active_code_details=[
                ActiveCodeDetail(code=d["code"], nick=d["nick"]) for d in active_access_codes["active_code_details"]
            ],
        )
    )


class AccessCodeExceptionCode(BaseExceptionCode):
    ACCESS_CODE_NOT_FOUND = ("NOT_FOUND", "Access code not found.")


class AccessCodeRequest(BaseModel):
    code: str


def _get_or_create_session_id(request: Request) -> str:
    if "session_id" not in request.session:
        request.session["session_id"] = str(uuid.uuid4())
    return request.session["session_id"]


@router.post("/activate", response_model=ResponseModel[None])
async def activate_access_code(body: AccessCodeRequest, request: Request, response: Response) -> ResponseModel[None]:
    previous_codes: list[str] = request.session.get("access_codes", [])

    if body.code not in previous_codes and not access_service.is_access_code_unclaimed(body.code):
        raise APIException(AccessCodeExceptionCode.ACCESS_CODE_NOT_FOUND, http_status_code=404)

    valid_codes = access_service.prune_invalid_access_codes([body.code, *previous_codes])

    if body.code in previous_codes:
        request.session["access_codes"] = valid_codes
        return ResponseModel(error_code="ALREADY_ACTIVE")

    request.session["access_codes"] = valid_codes

    session_id = _get_or_create_session_id(request)
    access_service.set_access_code_session(body.code, session_id)
    return ResponseModel()
