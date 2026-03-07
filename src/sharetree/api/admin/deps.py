from fastapi import Header, HTTPException, Request

from sharetree.settings import settings

ADMIN_GROUP = "admins"
SESSION_ADMIN_KEY = "admin_authenticated"


def require_admin_group(request: Request, remote_groups: str | None = Header(default=None)) -> None:
    """Enforce admin access.

    When TRUST_HEADERS is True, the Remote-Groups header must be present and contain
    the "admins" group, otherwise HTTP 403 is raised.

    When TRUST_HEADERS is False, the session must contain the admin_authenticated flag
    set by the admin login endpoint.
    """
    if settings.TRUST_HEADERS:
        if remote_groups is None:
            raise HTTPException(status_code=403, detail="Forbidden")
        request_groups = {g.strip() for g in remote_groups.split(",") if g.strip()}
        if ADMIN_GROUP not in request_groups:
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        if not request.session.get(SESSION_ADMIN_KEY):
            raise HTTPException(status_code=403, detail="Forbidden")
