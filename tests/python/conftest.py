from collections.abc import Generator

import pytest
from buildable_core.config import Settings
from buildable_core.database import Base, create_engine_and_session_factory
from fastapi.testclient import TestClient

from apps.demo_api.main import create_app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    settings = Settings(
        app_env="test",
        database_url="sqlite+pysqlite:///:memory:",
        secret_key="test-secret-with-at-least-thirty-two-characters",
        cors_origins=["http://testserver"],
        auto_create_schema=False,
        auth_rate_limit_attempts=100,
    )
    engine, session_factory = create_engine_and_session_factory(settings.database_url)
    Base.metadata.create_all(engine)
    app = create_app(settings, engine=engine, session_factory=session_factory)
    with TestClient(app) as test_client:
        yield test_client
