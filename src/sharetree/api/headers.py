from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()


class HeadersResponse(BaseModel):
    headers: dict[str, str]


@router.get("/headers", response_model=HeadersResponse)
async def get_headers(request: Request) -> HeadersResponse:
    return HeadersResponse(headers=dict(request.headers))
