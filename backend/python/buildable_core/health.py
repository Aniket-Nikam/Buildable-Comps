from typing import Any

from fastapi import APIRouter, Request
from sqlalchemy import text

router = APIRouter()


@router.get("/health")
def health() -> dict[str, Any]:
    return {"status": "ok"}


@router.get("/ready")
def readiness(request: Request) -> dict[str, Any]:
    with request.app.state.session_factory() as session:
        session.execute(text("SELECT 1"))
    request.app.state.auth_rate_limiter.healthcheck()
    return {"status": "ready", "checks": {"database": "ok", "rateLimiter": "ok"}}
