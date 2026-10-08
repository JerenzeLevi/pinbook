"""Runtime configuration, loaded from ``PINBOOK_*`` environment variables or a ``.env`` file."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PINBOOK_", env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./pinbook.db"
    log_level: str = "INFO"
    max_page_size: int = 100
    max_search_radius_km: float = 2000.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
