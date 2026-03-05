from api_exception import APIException, BaseExceptionCode, ResponseModel
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from sharetree.services import access as access_service

router = APIRouter(prefix="/access")


class AccessCodesResponse(BaseModel):
    active_codes: list[str]
    paths: list[str]


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
        )
    )


class AccessCodeExceptionCode(BaseExceptionCode):
    ACCESS_CODE_NOT_FOUND = ("NOT_FOUND", "Access code not found.")


class AccessCodeRequest(BaseModel):
    code: str


@router.post("/activate")
async def activate_access_code(body: AccessCodeRequest, request: Request, response: Response) -> ResponseModel:
    previous_codes: list[str] = request.session.get("access_codes", [])

    valid_codes = access_service.prune_invalid_access_codes([body.code, *previous_codes])

    if body.code not in valid_codes:
        raise APIException(AccessCodeExceptionCode.ACCESS_CODE_NOT_FOUND, http_status_code=404)

    request.session["access_codes"] = valid_codes

    if body.code in previous_codes:
        return ResponseModel(error_code="ALREADY_ACTIVE")
    else:
        return ResponseModel()
