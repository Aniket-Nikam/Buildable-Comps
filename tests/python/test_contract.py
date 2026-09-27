from fastapi.testclient import TestClient


def test_openapi_exposes_registered_identity_contract(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    expected = {
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/logout",
        "/api/v1/auth/email-verification/request",
        "/api/v1/auth/email-verification/confirm",
        "/api/v1/auth/password/forgot",
        "/api/v1/auth/password/reset",
        "/api/v1/users/me",
    }
    assert expected <= set(paths)
