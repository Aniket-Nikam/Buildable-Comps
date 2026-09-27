from functools import lru_cache
from typing import Literal, Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_SECRET = "development-only-secret-change-before-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_env: Literal["development", "test", "production"] = "development"
    app_name: str = "Buildable Comps Demo API"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite+pysqlite:///./buildable.db"
    secret_key: str = Field(default=DEVELOPMENT_SECRET, min_length=32)
    access_token_ttl_minutes: int = Field(default=15, ge=1, le=120)
    refresh_token_ttl_days: int = Field(default=30, ge=1, le=90)
    email_verification_ttl_hours: int = Field(default=24, ge=1, le=168)
    password_reset_ttl_hours: int = Field(default=1, ge=1, le=24)
    require_verified_email: bool = False
    cors_origins: list[str] = ["http://localhost:5173"]
    cookie_secure: bool = False
    auto_create_schema: bool = False
    auth_rate_limit_attempts: int = Field(default=10, ge=1, le=100)
    auth_rate_limit_window_seconds: int = Field(default=60, ge=10, le=3600)
    rate_limit_backend: Literal["memory", "redis"] = "memory"
    redis_url: str | None = None

    @model_validator(mode="after")
    def validate_production_security(self) -> Self:
        if self.app_env == "production":
            if self.secret_key == DEVELOPMENT_SECRET:
                raise ValueError("SECRET_KEY must be changed in production")
            if not self.cookie_secure:
                raise ValueError("COOKIE_SECURE must be true in production")
            if self.auto_create_schema:
                raise ValueError("AUTO_CREATE_SCHEMA must be false in production")
            if self.rate_limit_backend != "redis" or not self.redis_url:
                raise ValueError("Production requires Redis-backed rate limiting")
            if not self.require_verified_email:
                raise ValueError("REQUIRE_VERIFIED_EMAIL must be true in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
