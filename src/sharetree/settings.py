from pathlib import Path

from starlette.config import Config

config = Config(".env", env_prefix="SHARETREE_")

SESSION_SECRET: str = config("SESSION_SECRET")
SHARE_ROOT: Path = config("SHARE_ROOT", cast=Path, default=Path("files"))
DATA_PATH: Path = config("DATA_PATH", cast=Path, default=Path("data"))
