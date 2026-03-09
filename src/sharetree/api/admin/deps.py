import logging

from fastapi import Header, HTTPException, Request

from sharetree.settings import settings

ADMIN_GROUP = "admins"
SESSION_ADMIN_KEY = "admin_authenticated"


logger = logging.getLogger(__name__)


def check_is_admin(request: Request, remote_groups: str | None = None) -> bool:
    """Return True if the current request has admin access, without raising."""
    if settings.TRUST_HEADERS:
        if remote_groups is None:
            return False
        request_groups = {g.strip() for g in remote_groups.split(",") if g.strip()}
        return ADMIN_GROUP in request_groups
    else:
        return bool(request.session.get(SESSION_ADMIN_KEY))


def require_admin_group(request: Request, remote_groups: str | None = Header(default=None)) -> None:
    """Enforce admin access.

    When TRUST_HEADERS is True, the Remote-Groups header must be present and contain
    the "admins" group, otherwise HTTP 403 is raised.

    When TRUST_HEADERS is False, the session must contain the admin_authenticated flag
    set by the admin login endpoint.
    """
    print(f"check_is_admin {settings.TRUST_HEADERS=} {remote_groups=}")

    if not check_is_admin(request, remote_groups):
        raise HTTPException(status_code=403, detail="Forbidden")
