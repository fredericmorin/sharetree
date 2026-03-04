import uvicorn

from sharetree.settings import SHARE_ROOT


def main() -> int:
    if not SHARE_ROOT.exists():
        SHARE_ROOT.mkdir()

    uvicorn.run("sharetree.app:app", host="0.0.0.0", port=8000, reload=True)
    return 0
