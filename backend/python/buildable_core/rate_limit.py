from collections import defaultdict, deque
from importlib import import_module
from threading import Lock
from time import monotonic
from typing import Protocol, cast

from .errors import AppError


class RateLimiter(Protocol):
    def check(self, key: str) -> None: ...

    def healthcheck(self) -> None: ...

    def close(self) -> None: ...


class _RedisClient(Protocol):
    def eval(self, script: str, numkeys: int, *keys_and_args: str | int) -> object: ...

    def ping(self) -> object: ...

    def close(self) -> None: ...


class _RedisFactory(Protocol):
    def from_url(self, url: str, *, decode_responses: bool) -> _RedisClient: ...


class InMemoryRateLimiter:
    """Single-process rate limiter. Replace with Redis for multi-worker deployments."""

    def __init__(self, attempts: int, window_seconds: int) -> None:
        self.attempts = attempts
        self.window_seconds = window_seconds
        self._attempts_by_key: defaultdict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> None:
        now = monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            entries = self._attempts_by_key[key]
            while entries and entries[0] < cutoff:
                entries.popleft()
            if len(entries) >= self.attempts:
                raise AppError(
                    "rate_limit_exceeded",
                    "Too many authentication attempts. Try again shortly.",
                    status_code=429,
                )
            entries.append(now)

    def healthcheck(self) -> None:
        return

    def close(self) -> None:
        return


class RedisRateLimiter:
    """Shared fixed-window limiter for multi-worker deployments."""

    _script = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
return current
"""

    def __init__(
        self,
        url: str,
        attempts: int,
        window_seconds: int,
        *,
        namespace: str = "buildable:auth:rate",
    ) -> None:
        self.attempts = attempts
        self.window_seconds = window_seconds
        self.namespace = namespace
        redis_factory = cast(_RedisFactory, import_module("redis").Redis)
        self._client = redis_factory.from_url(url, decode_responses=True)

    def check(self, key: str) -> None:
        count = cast(
            int,
            self._client.eval(
                self._script,
                1,
                f"{self.namespace}:{key}",
                self.window_seconds,
            ),
        )
        if count > self.attempts:
            raise AppError(
                "rate_limit_exceeded",
                "Too many authentication attempts. Try again shortly.",
                status_code=429,
            )

    def healthcheck(self) -> None:
        self._client.ping()

    def close(self) -> None:
        self._client.close()


def create_rate_limiter(
    backend: str, redis_url: str | None, attempts: int, window_seconds: int
) -> RateLimiter:
    if backend == "redis":
        if not redis_url:
            raise ValueError("REDIS_URL is required when RATE_LIMIT_BACKEND=redis")
        return RedisRateLimiter(redis_url, attempts, window_seconds)
    return InMemoryRateLimiter(attempts, window_seconds)
