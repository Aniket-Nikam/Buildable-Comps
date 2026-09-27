import sys
from types import SimpleNamespace

import pytest
from buildable_core.config import Settings
from buildable_core.errors import AppError
from buildable_core.rate_limit import InMemoryRateLimiter, create_rate_limiter
from pydantic import ValidationError

from apps.demo_api.main import create_app


def test_in_memory_limiter_enforces_its_window() -> None:
    limiter = InMemoryRateLimiter(attempts=2, window_seconds=60)
    limiter.check("login:test")
    limiter.check("login:test")
    with pytest.raises(AppError, match="Too many authentication attempts"):
        limiter.check("login:test")


def test_redis_limiter_uses_shared_atomic_counter(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        def __init__(self) -> None:
            self.count = 0
            self.closed = False

        def eval(self, *_: object) -> int:
            self.count += 1
            return self.count

        def ping(self) -> bool:
            return True

        def close(self) -> None:
            self.closed = True

    client = FakeClient()

    class FakeRedis:
        @staticmethod
        def from_url(_: str, *, decode_responses: bool) -> FakeClient:
            assert decode_responses is True
            return client

    monkeypatch.setitem(sys.modules, "redis", SimpleNamespace(Redis=FakeRedis))
    limiter = create_rate_limiter("redis", "redis://test", attempts=1, window_seconds=60)
    limiter.healthcheck()
    limiter.check("login:test")
    with pytest.raises(AppError):
        limiter.check("login:test")
    limiter.close()
    assert client.closed is True


def test_production_rejects_local_only_security_adapters() -> None:
    with pytest.raises(ValidationError, match="Redis-backed rate limiting"):
        Settings(
            app_env="production",
            secret_key="production-secret-with-at-least-thirty-two-characters",
            cookie_secure=True,
            database_url="postgresql+psycopg://user:password@localhost/database",
            public_web_url="https://app.example.com",
            cors_origins=["https://app.example.com"],
        )

    settings = Settings(
        app_env="production",
        secret_key="production-secret-with-at-least-thirty-two-characters",
        cookie_secure=True,
        rate_limit_backend="redis",
        redis_url="redis://localhost:6379/0",
        require_verified_email=True,
        identity_notifier_backend="injected",
        database_url="postgresql+psycopg://user:password@localhost/database",
        public_web_url="https://app.example.com",
        cors_origins=["https://app.example.com"],
    )
    with pytest.raises(ValueError, match="IdentityNotifier"):
        create_app(settings)
