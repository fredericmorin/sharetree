from starlette.config import Config

config = Config(".env", env_prefix="SHARETREE_")

SESSION_SECRET = config("SESSION_SECRET")
SHARE_ROOT = config("SHARE_ROOT", default="data")
