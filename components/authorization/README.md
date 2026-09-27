# Role-based authorization

Provides project-defined roles and permissions without hardcoded `ADMIN` or `USER` behavior. Grants are exact-match and deny by default. Administrative mutations create audit rows in the same database transaction as the change.

## Integration

1. Install the `identity.users` and `identity.auth` requirements.
2. Apply `0003_authorization` after the identity migrations.
3. Include the authorization router after authentication wiring.
4. Bootstrap exactly one existing user with `python -m apps.demo_api.bootstrap --email owner@example.com`.
5. Use `require_permission("your.permission")` for FastAPI routes.
6. Wrap authorized React areas in `AuthorizationProvider` and render permission-aware content with `Can` or `PermissionGuard`.

The bootstrap operation is idempotent. It creates the system `platform-admin` role and the four permissions used by the administrative HTTP API. Remove one-time production shell access after bootstrapping; do not run bootstrap from every application startup.

## Public HTTP API

- `GET /api/v1/authorization/me` returns the caller's roles and effective permissions.
- Role, permission, and user-authorization reads require `authorization.roles.read`; role detail includes its current permission grants.
- Assignment routes require `authorization.assignments.write`.
- `GET /api/v1/authorization/audit-logs` requires `authorization.audit.read` and supports bounded pagination.

Assignment and grant `PUT`/`DELETE` operations are idempotent. The service prevents an administrator from removing their own system administrator role. Application permissions such as `invoices.approve` remain consumer-owned configuration.

## Audit boundary

The audit record captures the actor, action, target, request ID, source IP, timestamp, and non-sensitive metadata. It intentionally excludes bearer tokens, cookies, passwords, and recovery tokens. Centralized retention and export are deployment policy, not reusable module behavior.
