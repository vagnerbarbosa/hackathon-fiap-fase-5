"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import List

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="FIAP STRIDE API", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")

    # Database
    database_url: str = Field(
        description="PostgreSQL connection URL (postgresql+asyncpg://...)"
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )

    # Storage
    storage_path: str = Field(
        default="./storage",
        description="Path for file uploads",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
        description="Logging level",
    )

    # Security
    api_rate_limit: int = Field(
        default=60,
        ge=1,
        description="Rate limit per minute per IP",
    )
    api_key: str = Field(
        description="API Key for authentication",
    )
    cors_origins: List[str] = Field(
        default_factory=list,
        description="CORS allowed origins (comma-separated)",
    )

    def __init__(self, **kwargs):
        # Parse CORS origins from comma-separated string before validation
        if "cors_origins" in kwargs and isinstance(kwargs["cors_origins"], str):
            origins = kwargs["cors_origins"]
            kwargs["cors_origins"] = [o.strip() for o in origins.split(",") if o.strip()]
        super().__init__(**kwargs)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application settings instance.

    Raises:
        SystemExit: If settings validation fails.
    """
    try:
        return Settings()
    except ValidationError as e:
        print("Configuration Error:")
        for error in e.errors():
            field = ".".join(str(x) for x in error["loc"])
            print(f"  - {field}: {error['msg']}")
        raise SystemExit(1)


# Global settings instance for import
settings = get_settings()
