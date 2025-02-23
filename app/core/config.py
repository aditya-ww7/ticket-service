from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@db:5432/ticketdb"
    REDIS_URL: str = "redis://redis:6379/0"

    APP_NAME: str = "Ticket Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    CACHE_TTL: int = 3600  # 1 hour

    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    API_V1_PREFIX: str = "/api/v1"
    BOOKING_TIMEOUT: int = 300  # 5 minutes
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 1

    LOCK_TIMEOUT: int = 10  # seconds

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
