from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Application configuration."""

    # App settings
    app_name: str = "Car Index"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # CORS settings
    cors_origins: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=(".env.api", ".env"),
        env_file_encoding="utf-8",
        env_prefix="APP_",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_config() -> AppConfig:
    """Get the application configuration (cached)."""
    return AppConfig()
