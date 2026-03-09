import logging
import sys
import time

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


def configure_logging() -> None:
    """Configure structlog with a human-readable console renderer for development."""
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


log = structlog.get_logger()

_LOGGED_REQUEST_HEADERS = {
    "user-agent",
    "content-type",
    "content-length",
    "referer",
    "origin",
    "remote-groups",
}
_LOGGED_RESPONSE_HEADERS = {
    "content-type",
    "content-length",
}


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start = time.perf_counter()

        req_headers = {k: v for k, v in request.headers.items() if k.lower() in _LOGGED_REQUEST_HEADERS}

        # Best-effort client IP: prefer forwarded headers set by a reverse proxy.
        client_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or request.headers.get("x-real-ip")
            or (request.client.host if request.client else None)
        )

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        resp_headers = {k: v for k, v in response.headers.items() if k.lower() in _LOGGED_RESPONSE_HEADERS}

        extras: dict = {}
        if hasattr(request.state, "extras"):
            extras = request.state.extras

        log.info(
            "request",
            method=request.method,
            path=request.url.path,
            query=str(request.url.query) or None,
            status=response.status_code,
            duration_ms=duration_ms,
            client_ip=client_ip,
            **{f"req_{k.replace('-', '_')}": v for k, v in req_headers.items()},
            **{f"res_{k.replace('-', '_')}": v for k, v in resp_headers.items()},
            **extras,
        )

        return response
