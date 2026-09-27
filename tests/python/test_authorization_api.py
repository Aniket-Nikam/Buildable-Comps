from buildable_authorization import bootstrap_administrator
from fastapi.testclient import TestClient


def register(client: TestClient, email: str, display_name: str) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "correct-horse-battery-staple",
            "displayName": display_name,
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


def auth(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_role_permission_assignment_and_audit_cycle(client: TestClient) -> None:
    admin = register(client, "admin@example.com", "Admin User")
    member = register(client, "member@example.com", "Member User")

    denied = client.post(
        "/api/v1/authorization/roles",
        headers=auth(admin["accessToken"]),
        json={"name": "support", "description": "Support operators"},
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "permission_denied"

    with client.app.state.session_factory() as session:
        bootstrap_administrator(session, admin["user"]["id"])

    snapshot = client.get("/api/v1/authorization/me", headers=auth(admin["accessToken"]))
    assert snapshot.status_code == 200
    assert snapshot.json()["data"]["roles"][0]["name"] == "platform-admin"
    assert {permission["name"] for permission in snapshot.json()["data"]["permissions"]} == {
        "authorization.assignments.write",
        "authorization.audit.read",
        "authorization.roles.read",
        "authorization.roles.write",
    }

    role_response = client.post(
        "/api/v1/authorization/roles",
        headers=auth(admin["accessToken"]),
        json={"name": "support", "description": "Support operators"},
    )
    assert role_response.status_code == 201
    role = role_response.json()["data"]

    permission_response = client.post(
        "/api/v1/authorization/permissions",
        headers=auth(admin["accessToken"]),
        json={"name": "tickets.read", "description": "Read support tickets"},
    )
    assert permission_response.status_code == 201
    permission = permission_response.json()["data"]

    grant = client.put(
        f"/api/v1/authorization/roles/{role['id']}/permissions/{permission['id']}",
        headers=auth(admin["accessToken"]),
    )
    assert grant.status_code == 200
    assert grant.json()["data"] == {"granted": True}

    role_detail = client.get(
        f"/api/v1/authorization/roles/{role['id']}",
        headers=auth(admin["accessToken"]),
    )
    assert role_detail.status_code == 200
    assert [item["name"] for item in role_detail.json()["data"]["permissions"]] == ["tickets.read"]

    assignment = client.put(
        f"/api/v1/authorization/users/{member['user']['id']}/roles/{role['id']}",
        headers=auth(admin["accessToken"]),
    )
    assert assignment.status_code == 200

    inspected_member = client.get(
        f"/api/v1/authorization/users/{member['user']['id']}",
        headers=auth(admin["accessToken"]),
    )
    assert inspected_member.status_code == 200
    assert inspected_member.json()["data"]["roles"][0]["name"] == "support"

    member_snapshot = client.get("/api/v1/authorization/me", headers=auth(member["accessToken"]))
    assert member_snapshot.status_code == 200
    assert [role["name"] for role in member_snapshot.json()["data"]["roles"]] == ["support"]
    assert [item["name"] for item in member_snapshot.json()["data"]["permissions"]] == [
        "tickets.read"
    ]

    audit = client.get("/api/v1/authorization/audit-logs", headers=auth(admin["accessToken"]))
    assert audit.status_code == 200
    actions = {entry["action"] for entry in audit.json()["data"]}
    assert {
        "authorization.bootstrapped",
        "role.created",
        "permission.created",
        "role.permission_granted",
        "user.role_assigned",
    } <= actions
    assert all(
        entry["requestId"]
        for entry in audit.json()["data"]
        if entry["action"] != "authorization.bootstrapped"
    )


def test_admin_cannot_remove_own_system_role(client: TestClient) -> None:
    admin = register(client, "lockout@example.com", "Lockout Test")
    with client.app.state.session_factory() as session:
        role = bootstrap_administrator(session, admin["user"]["id"])

    response = client.delete(
        f"/api/v1/authorization/users/{admin['user']['id']}/roles/{role.id}",
        headers=auth(admin["accessToken"]),
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "self_lockout_prevented"

    permissions = client.get(
        "/api/v1/authorization/permissions", headers=auth(admin["accessToken"])
    ).json()["data"]
    roles_write = next(
        permission
        for permission in permissions
        if permission["name"] == "authorization.roles.write"
    )
    protected_grant = client.delete(
        f"/api/v1/authorization/roles/{role.id}/permissions/{roles_write['id']}",
        headers=auth(admin["accessToken"]),
    )
    assert protected_grant.status_code == 409
    assert protected_grant.json()["error"]["code"] == "system_grant_protected"
