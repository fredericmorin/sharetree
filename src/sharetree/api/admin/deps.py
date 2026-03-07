from fastapi import Header, HTTPException

from sharetree.settings import settings


def require_admin_group(remote_groups: str | None = Header(default=None)) -> None:
    """Verify the request carries a Remote-Groups header containing at least one configured admin group.

    Raises HTTP 403 if the header is absent or none of its groups are in ADMIN_GROUPS.
    """
    if remote_groups is None:
        raise HTTPException(status_code=403, detail="Forbidden")
    request_groups = {g.strip() for g in remote_groups.split(",") if g.strip()}
    if not request_groups.intersection(settings.ADMIN_GROUPS):
        raise HTTPException(status_code=403, detail="Forbidden")
