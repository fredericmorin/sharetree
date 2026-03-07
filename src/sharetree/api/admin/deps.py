from fastapi import Header, HTTPException

from sharetree.settings import settings

ADMIN_GROUP = "admins"


def require_admin_group(remote_groups: str | None = Header(default=None)) -> None:
    """Enforce admin access via the Remote-Groups header when TRUST_HEADERS is enabled.

    When TRUST_HEADERS is False, all requests are allowed through (header is ignored).
    When TRUST_HEADERS is True, the Remote-Groups header must be present and contain
    the "admins" group, otherwise HTTP 403 is raised.
    """
    if not settings.TRUST_HEADERS:
        return
    if remote_groups is None:
        raise HTTPException(status_code=403, detail="Forbidden")
    request_groups = {g.strip() for g in remote_groups.split(",") if g.strip()}
    if ADMIN_GROUP not in request_groups:
        raise HTTPException(status_code=403, detail="Forbidden")
