from buildable_core.config import Settings
from buildable_core.database import Base, create_engine_and_session_factory
from buildable_identity.notifications import IdentityNotification
from fastapi.testclient import TestClient

from apps.demo_api.main import create_app


def register(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "security@example.com",
            "password": "correct-horse-battery-staple",
            "displayName": "Security Test",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


def notifications(client: TestClient) -> list[IdentityNotification]:
    return client.app.state.identity_notifier.outbox


def test_email_verification_is_single_use_and_does_not_leak_accounts(
    client: TestClient,
) -> None:
    registered = register(client)
    assert registered["user"]["emailVerified"] is False
    assert "token" not in registered

    verification = notifications(client)[-1]
    assert verification.kind == "email_verification"
    confirmed = client.post(
        "/api/v1/auth/email-verification/confirm",
        json={"token": verification.token},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["data"]["emailVerified"] is True

    replay = client.post(
        "/api/v1/auth/email-verification/confirm",
        json={"token": verification.token},
    )
    assert replay.status_code == 400
    assert replay.json()["error"]["code"] == "invalid_token"

    count = len(notifications(client))
    unknown = client.post(
        "/api/v1/auth/email-verification/request",
        json={"email": "unknown@example.com"},
    )
    assert unknown.status_code == 200
    assert unknown.json()["data"] == {"accepted": True}
    assert len(notifications(client)) == count


def test_password_reset_revokes_sessions_and_invalidates_access_tokens(
    client: TestClient,
) -> None:
    registered = register(client)
    old_access = registered["accessToken"]

    accepted = client.post(
        "/api/v1/auth/password/forgot",
        json={"email": "security@example.com"},
    )
    assert accepted.status_code == 200
    reset_notification = notifications(client)[-1]
    assert reset_notification.kind == "password_reset"

    reset = client.post(
        "/api/v1/auth/password/reset",
        json={
            "token": reset_notification.token,
            "newPassword": "a-completely-new-password",
        },
    )
    assert reset.status_code == 200
    assert reset.json()["data"] == {"passwordReset": True}
    assert (
        client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {old_access}"}
        ).status_code
        == 401
    )
    assert client.post("/api/v1/auth/refresh").status_code == 401

    old_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "security@example.com",
            "password": "correct-horse-battery-staple",
        },
    )
    assert old_login.status_code == 401
    new_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "security@example.com",
            "password": "a-completely-new-password",
        },
    )
    assert new_login.status_code == 200


def test_replayed_rotated_token_revokes_the_entire_session_family(
    client: TestClient,
) -> None:
    register(client)
    original_refresh = client.cookies["buildable_refresh"]
    assert client.post("/api/v1/auth/refresh").status_code == 200
    rotated_refresh = client.cookies["buildable_refresh"]

    client.cookies.clear()
    client.cookies.set("buildable_refresh", original_refresh, path="/api/v1/auth")
    replay = client.post("/api/v1/auth/refresh")
    assert replay.status_code == 401

    client.cookies.clear()
    client.cookies.set("buildable_refresh", rotated_refresh, path="/api/v1/auth")
    assert client.post("/api/v1/auth/refresh").status_code == 401
    assert any(
        event.name == "RefreshTokenReuseDetected" for event in client.app.state.events.events
    )


def test_verified_email_gate_blocks_credentials_until_confirmation() -> None:
    settings = Settings(
        app_env="test",
        database_url="sqlite+pysqlite:///:memory:",
        secret_key="verification-gate-secret-at-least-thirty-two-characters",
        cors_origins=["http://testserver"],
        require_verified_email=True,
        auth_rate_limit_attempts=100,
    )
    engine, session_factory = create_engine_and_session_factory(settings.database_url)
    Base.metadata.create_all(engine)
    app = create_app(settings, engine=engine, session_factory=session_factory)

    with TestClient(app) as gated_client:
        registered = register(gated_client)
        access = registered["accessToken"]
        assert (
            gated_client.get(
                "/api/v1/users/me", headers={"Authorization": f"Bearer {access}"}
            ).status_code
            == 403
        )
        assert (
            gated_client.post(
                "/api/v1/auth/login",
                json={
                    "email": "security@example.com",
                    "password": "correct-horse-battery-staple",
                },
            ).status_code
            == 403
        )

        token = notifications(gated_client)[-1].token
        assert (
            gated_client.post(
                "/api/v1/auth/email-verification/confirm", json={"token": token}
            ).status_code
            == 200
        )
        assert (
            gated_client.get(
                "/api/v1/users/me", headers={"Authorization": f"Bearer {access}"}
            ).status_code
            == 200
        )
