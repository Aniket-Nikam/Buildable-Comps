import os
import uuid

import pytest
from buildable_core.config import Settings
from buildable_core.database import create_engine_and_session_factory
from buildable_identity.models import User
from fastapi.testclient import TestClient
from sqlalchemy import delete

from apps.demo_api.main import create_app


@pytest.mark.postgres
def test_auth_lifecycle_against_migrated_postgres() -> None:
    database_url = os.getenv("TEST_POSTGRES_URL")
    if not database_url:
        pytest.skip("TEST_POSTGRES_URL is not configured")

    engine, session_factory = create_engine_and_session_factory(database_url)
    assert engine.dialect.name == "postgresql"
    email = f"postgres-{uuid.uuid4()}@example.com"
    settings = Settings(
        app_env="test",
        database_url=database_url,
        secret_key="postgres-test-secret-with-at-least-thirty-two-characters",
        cors_origins=["http://testserver"],
        auth_rate_limit_attempts=100,
    )
    app = create_app(settings, engine=engine, session_factory=session_factory)

    try:
        with TestClient(app) as client:
            registered = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "password": "correct-horse-battery-staple",
                    "displayName": "Postgres Test",
                },
            )
            assert registered.status_code == 201
            assert client.post("/api/v1/auth/refresh").status_code == 200
    finally:
        with session_factory() as session:
            session.execute(delete(User).where(User.email == email))
            session.commit()
        engine.dispose()
