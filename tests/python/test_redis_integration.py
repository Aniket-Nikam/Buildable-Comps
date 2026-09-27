import os
import uuid
from importlib import import_module

import pytest
from buildable_core.errors import AppError
from buildable_core.rate_limit import RedisRateLimiter


@pytest.mark.redis
def test_rate_limiter_against_live_redis() -> None:
    redis_url = os.getenv("TEST_REDIS_URL")
    if not redis_url:
        pytest.skip("TEST_REDIS_URL is not configured")

    namespace = f"buildable:test:{uuid.uuid4()}"
    key = "login:integration"
    limiter = RedisRateLimiter(redis_url, attempts=2, window_seconds=60, namespace=namespace)
    Redis = import_module("redis").Redis
    client = Redis.from_url(redis_url, decode_responses=True)
    try:
        limiter.healthcheck()
        limiter.check(key)
        limiter.check(key)
        with pytest.raises(AppError, match="Too many authentication attempts"):
            limiter.check(key)
    finally:
        client.delete(f"{namespace}:{key}")
        client.close()
        limiter.close()
