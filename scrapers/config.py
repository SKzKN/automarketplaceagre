from typing import Optional
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class ScraperConfig(BaseSettings):
    """Configuration for scrapers."""

    # MongoDB connection
    mongodb_uri: str = "mongodb://localhost:27017/car_index"
    database_name: str = "car_index"
    collection_name: str = "car_listings"

    # Scraping settings
    max_pages: Optional[int] = None
    request_delay: float = 1
    request_timeout: int = 30
    max_retries: int = 3
    
    # Async scraper settings
    batch_size: int = 10

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=(".env.scrapers", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

@lru_cache()
def get_config() -> ScraperConfig:
    """Load configuration from environment variables."""
    return ScraperConfig()
