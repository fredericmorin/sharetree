"""Redis-backed session middleware for Starlette/FastAPI.

When REDIS_URL is configured, session data is stored server-side in Redis and
only a random session ID is kept in the browser cookie. When REDIS_URL is not
set, the app falls back to Starlette's built-in signed-cookie sessions.
"""

import json
import uuid
from collections.abc import Callable, MutableMapping
from typing import Any

from redis.asyncio import Redis
from starlette.datastructures import MutableHeaders
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Receive, Scope, Send

_SESSION_PREFIX = "sharetree:session:"
_DEFAULT_MAX_AGE = 14 * 24 * 60 * 60  # 14 days in seconds


class _RedisSession(MutableMapping):  # type: ignore[type-arg]
    """Dict-like object backed by a Redis hash. Mutations are tracked so the
    session is only written back to Redis when something actually changed."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data
        self.modified = False

    # MutableMapping interface ------------------------------------------------

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.modified = True

    def __delitem__(self, key: str) -> None:
        del self._data[key]
        self.modified = True

    def __iter__(self):  # type: ignore[override]
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:  # pragma: no cover
        return repr(self._data)


class RedisSessionMiddleware:
    """ASGI middleware that stores session data in Redis.

    A random UUID session-ID is placed in a browser cookie; the actual session
    dict is stored under ``sharetree:session:<id>`` in Redis with a rolling TTL.

    Interface-compatible with Starlette's ``SessionMiddleware``: handlers access
    the session via ``request.session``.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        redis_url: str,
        session_cookie: str = "session",
        max_age: int = _DEFAULT_MAX_AGE,
        https_only: bool = False,
        same_site: str = "lax",
    ) -> None:
        self.app = app
        self.redis: Redis = Redis.from_url(redis_url, decode_responses=True)
        self.session_cookie = session_cookie
        self.max_age = max_age
        self.https_only = https_only
        self.same_site = same_site

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)
        session_id = connection.cookies.get(self.session_cookie)

        if session_id:
            raw = await self.redis.get(f"{_SESSION_PREFIX}{session_id}")
            data: dict[str, Any] = json.loads(raw) if raw else {}
        else:
            session_id = str(uuid.uuid4())
            data = {}

        scope["session"] = _RedisSession(data)

        async def send_wrapper(message: Any) -> None:
            if message["type"] == "http.response.start":
                session: _RedisSession = scope["session"]
                if session.modified or not data:
                    # Persist the (potentially empty) session with a rolling TTL.
                    await self.redis.setex(
                        f"{_SESSION_PREFIX}{session_id}",
                        self.max_age,
                        json.dumps(dict(session)),
                    )
                elif data:
                    # Nothing changed — just refresh the TTL so active sessions don't expire.
                    await self.redis.expire(f"{_SESSION_PREFIX}{session_id}", self.max_age)

                cookie_attrs: list[str] = [
                    f"{self.session_cookie}={session_id}",
                    f"Max-Age={self.max_age}",
                    "HttpOnly",
                    f"SameSite={self.same_site}",
                    "Path=/",
                ]
                if self.https_only:
                    cookie_attrs.append("Secure")

                headers = MutableHeaders(scope=message)
                headers.append("Set-Cookie", "; ".join(cookie_attrs))

            await send(message)

        await self.app(scope, receive, send_wrapper)

    async def close(self) -> None:
        """Close the underlying Redis connection pool."""
        await self.redis.aclose()


def make_session_middleware(
    app: ASGIApp,
    *,
    secret_key: str,
    redis_url: str | None,
    https_only: bool = False,
) -> Callable[[Scope, Receive, Send], Any]:
    """Return the appropriate session middleware.

    - When *redis_url* is provided, returns :class:`RedisSessionMiddleware`.
    - Otherwise wraps the app with Starlette's built-in signed-cookie
      :class:`~starlette.middleware.sessions.SessionMiddleware`.
    """
    if redis_url:
        return RedisSessionMiddleware(app, redis_url=redis_url, https_only=https_only)

    from starlette.middleware.sessions import SessionMiddleware

    return SessionMiddleware(app, secret_key=secret_key, https_only=https_only)  # type: ignore[return-value]
