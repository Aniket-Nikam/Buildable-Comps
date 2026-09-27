from fastapi.testclient import TestClient


def register(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "rhea@example.com",
            "password": "correct-horse-battery-staple",
            "displayName": "Rhea Menon",
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


def test_complete_authentication_and_profile_cycle(client: TestClient) -> None:
    registered = register(client)
    assert registered["user"]["email"] == "rhea@example.com"
    assert registered["user"]["displayName"] == "Rhea Menon"
    assert "password" not in registered["user"]
    assert client.cookies.get("buildable_refresh")

    me = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {registered['accessToken']}"},
    )
    assert me.status_code == 200
    assert me.json()["data"]["displayName"] == "Rhea Menon"

    updated = client.patch(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {registered['accessToken']}"},
        json={"displayName": "Rhea M."},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["displayName"] == "Rhea M."

    previous_refresh = client.cookies.get("buildable_refresh")
    refreshed = client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200
    assert refreshed.json()["data"]["accessToken"] != registered["accessToken"]
    assert client.cookies.get("buildable_refresh") != previous_refresh

    logged_out = client.post("/api/v1/auth/logout")
    assert logged_out.status_code == 200
    assert logged_out.json()["data"] == {"loggedOut": True}
    assert client.post("/api/v1/auth/refresh").status_code == 401


def test_login_uses_a_generic_credentials_error(client: TestClient) -> None:
    register(client)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "rhea@example.com", "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["error"] == {
        "code": "invalid_credentials",
        "message": "Email or password is incorrect.",
        "details": [],
    }


def test_duplicate_registration_and_validation_use_error_contract(client: TestClient) -> None:
    register(client)
    duplicate = client.post(
        "/api/v1/auth/register",
        json={
            "email": "RHEA@example.com",
            "password": "correct-horse-battery-staple",
            "displayName": "Another Rhea",
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "email_unavailable"
    assert duplicate.headers["x-request-id"]

    invalid = client.post(
        "/api/v1/auth/register",
        json={"email": "bad", "password": "short", "displayName": "R"},
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "validation_error"
    assert len(invalid.json()["error"]["details"]) == 3


def test_protected_route_rejects_missing_token(client: TestClient) -> None:
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_required"


def test_health_and_readiness(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {
        "status": "ready",
        "checks": {"database": "ok", "rateLimiter": "ok"},
    }
