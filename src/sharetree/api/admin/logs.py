from api_exception import ResponseModel
from fastapi import APIRouter, Query
from pydantic import BaseModel

from sharetree.services import logs as logs_service

router = APIRouter(prefix="/logs")


class DownloadLogEntryResponse(BaseModel):
    timestamp: str
    event: str
    path: str
    session_id: str | None
    nicks: list[str]
    codes: list[str]
    client_ip: str | None


class DownloadLogsPageResponse(BaseModel):
    entries: list[DownloadLogEntryResponse]
    page: int
    total_entries: int
    total_pages: int


@router.get("/downloads", response_model=ResponseModel[DownloadLogsPageResponse])
async def list_download_logs(page: int = Query(1, ge=1)) -> ResponseModel[DownloadLogsPageResponse]:
    result = logs_service.read_download_logs(page=page)
    return ResponseModel(
        data=DownloadLogsPageResponse(
            entries=[
                DownloadLogEntryResponse(
                    timestamp=e["timestamp"],
                    event=e["event"],
                    path=e["path"],
                    session_id=e["session_id"],
                    nicks=e["nicks"],
                    codes=e["codes"],
                    client_ip=e["client_ip"],
                )
                for e in result["entries"]
            ],
            page=result["page"],
            total_entries=result["total_entries"],
            total_pages=result["total_pages"],
        )
    )
