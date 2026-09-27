from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from buildable_core.config import Settings, get_settings
from buildable_core.database import Base, create_engine_and_session_factory
from buildable_core.errors import register_error_handlers
from buildable_core.events import InProcessEventPublisher
from buildable_core.health import router as health_router
from buildable_core.logging import configure_logging
from buildable_core.middleware import install_middleware
from buildable_core.rate_limit import create_rate_limiter
from buildable_identity import models as identity_models  # noqa: F401
from buildable_identity.notifications import IdentityNotifier, InMemoryIdentityNotifier
from buildable_identity.router import router as identity_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker


def create_app(
    settings: Settings | None = None,
    *,
    engine: Engine | None = None,
    session_factory: sessionmaker[Session] | None = None,
    identity_notifier: IdentityNotifier | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    if resolved_settings.app_env == "production" and identity_notifier is None:
        raise ValueError("Production requires an IdentityNotifier delivery adapter")
    if engine is None or session_factory is None:
        engine, session_factory = create_engine_and_session_factory(resolved_settings.database_url)

    rate_limiter = create_rate_limiter(
        resolved_settings.rate_limit_backend,
        resolved_settings.redis_url,
        resolved_settings.auth_rate_limit_attempts,
        resolved_settings.auth_rate_limit_window_seconds,
    )

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        configure_logging()
        if resolved_settings.auto_create_schema:
            Base.metadata.create_all(engine)
        try:
            yield
        finally:
            rate_limiter.close()
            engine.dispose()

    app = FastAPI(
        title=resolved_settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if resolved_settings.app_env != "production" else None,
        redoc_url=None,
    )
    app.state.settings = resolved_settings
    app.state.session_factory = session_factory
    app.state.events = InProcessEventPublisher()
    app.state.identity_notifier = identity_notifier or InMemoryIdentityNotifier()
    app.state.auth_rate_limiter = rate_limiter
    install_middleware(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
        allow_headers=["authorization", "content-type", "x-request-id"],
        expose_headers=["x-request-id", "x-response-time-ms"],
    )
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(identity_router, prefix=resolved_settings.api_prefix)
    return app


app = create_app()
