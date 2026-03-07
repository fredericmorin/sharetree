from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SHARETREE_", env_file=".env")

    SESSION_SECRET: str
    SHARE_ROOT: Path = Path("files")
    DATA_PATH: Path = Path("data")
    TRUST_HEADERS: bool = False


@lru_cache
def _get_settings() -> Settings:
    return Settings()  # type: ignore


class _LazyProxy:
    """Defers Settings instantiation (and env-var reads) until first attribute access."""

    def __getattr__(self, name: str) -> object:
        return getattr(_get_settings(), name)


settings: Settings = _LazyProxy()  # type: ignore
