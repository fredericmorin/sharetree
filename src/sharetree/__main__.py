import uvicorn


def main() -> int:


    uvicorn.run("sharetree.app:app", host="0.0.0.0", port=8000, reload=True)
    return 0
