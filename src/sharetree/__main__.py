import uvicorn

from sharetree.settings import settings


def main() -> int:
    if not settings.SHARE_ROOT.exists():
        settings.SHARE_ROOT.mkdir()

    uvicorn.run("sharetree.app:app", host="0.0.0.0", port=8000, reload=settings.DEV)
    return 0
