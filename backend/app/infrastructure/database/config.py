from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import computed_field


class MongoDBConfig(BaseSettings):
    """MongoDB configuration."""

    host: str = "mongodb"
    port: int = 27017
    username: Optional[str] = None
    password: Optional[str] = None
    database_name: str = "car_index"

    

    @computed_field
    def uri(self) -> str:
        """Construct MongoDB URI."""
        if self.username and self.password:
            return f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_name}"
        return f"mongodb://{self.host}:{self.port}/{self.database_name}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        env_prefix="MONGODB_",
    )


@lru_cache
def get_mongodb_config() -> MongoDBConfig:
    """Get MongoDB configuration (cached)."""
    return MongoDBConfig()
