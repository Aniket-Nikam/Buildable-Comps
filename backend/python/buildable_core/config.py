from functools import lru_cache
from typing import Literal, Self
from urllib.parse import urlparse

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
    identity_notifier_backend: Literal["memory", "smtp", "injected"] = "memory"
    public_web_url: str = "http://localhost:5173"
    smtp_host: str | None = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_security: Literal["starttls", "tls", "none"] = "starttls"
    smtp_timeout_seconds: float = Field(default=10, gt=0, le=60)

    @model_validator(mode="after")
    def validate_production_security(self) -> Self:
        if self.app_env == "production":
            if self.secret_key == DEVELOPMENT_SECRET:
                raise ValueError("SECRET_KEY must be changed in production")
            if not self.cookie_secure:
                raise ValueError("COOKIE_SECURE must be true in production")
            if self.auto_create_schema:
                raise ValueError("AUTO_CREATE_SCHEMA must be false in production")
            if self.database_url.startswith("sqlite"):
                raise ValueError("Production requires PostgreSQL")
            if self.rate_limit_backend != "redis" or not self.redis_url:
                raise ValueError("Production requires Redis-backed rate limiting")
            if urlparse(self.redis_url).password is None:
                raise ValueError("Production Redis requires authentication")
            if not self.require_verified_email:
                raise ValueError("REQUIRE_VERIFIED_EMAIL must be true in production")
            if self.identity_notifier_backend == "memory":
                raise ValueError("Production requires an SMTP or injected identity notifier")
            if not self.public_web_url.startswith("https://"):
                raise ValueError("PUBLIC_WEB_URL must use HTTPS in production")
            if "*" in self.cors_origins or any(
                not origin.startswith("https://") for origin in self.cors_origins
            ):
                raise ValueError("Production CORS origins must be explicit HTTPS origins")
            if self.identity_notifier_backend == "smtp" and self.smtp_security == "none":
                raise ValueError("SMTP transport security is required in production")
        if self.identity_notifier_backend == "smtp":
            if not self.smtp_host or not self.smtp_from_email:
                raise ValueError("SMTP_HOST and SMTP_FROM_EMAIL are required for SMTP delivery")
            if bool(self.smtp_username) != bool(self.smtp_password):
                raise ValueError("SMTP_USERNAME and SMTP_PASSWORD must be configured together")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
