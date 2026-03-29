"""Core configuration module for Procurely backend."""

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application environment: "development", "staging", "production"
    app_env: str = "development"

    # Database
    # NOTE: For production, migrate to PostgreSQL for proper concurrency and ACID compliance.
    database_url: str = "sqlite:///./procurely.db"

    # Redis
    # NOTE: For production, use Redis for rate limiting, caching, and session storage.
    redis_url: str = "redis://localhost:6379"

    # Security
    app_master_key: str = "dev-master-key-32-bytes-change!"
    jwt_secret_key: str = "dev-jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Default admin credentials — MUST override in .env for production
    default_admin_email: str = "admin@procurely.dev"
    default_admin_password: str = "change-me-in-dotenv"

    # CORS — override via BACKEND_CORS_ORIGINS env var in production
    backend_cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            if v.startswith("["):
                import json
                return json.loads(v)
            return [i.strip() for i in v.split(",")]
        return v

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
