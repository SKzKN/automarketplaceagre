from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.domain.enums.logs import LogFormat, LogLevel


class LogConfig(BaseSettings):
    """Logging configuration."""

    log_level: LogLevel = LogLevel.INFO
    log_format: LogFormat = LogFormat.HUMAN
    log_include_timestamp: bool = True
    log_include_module: bool = True
    log_file: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        env_prefix="LOG_",
    )


@lru_cache
def get_log_config() -> LogConfig:
    """Get logging configuration (cached)."""
    return LogConfig()
