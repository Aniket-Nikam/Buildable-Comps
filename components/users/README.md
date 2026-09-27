# Users and profiles

Provides the user aggregate, public profile contract, repository boundary, and self-service profile endpoints used by the first vertical slice.

## Public API

- `GET /api/v1/users/me`
- `PATCH /api/v1/users/me`
- Python exports from `buildable_identity`

The public response never includes password hashes or session tokens. It includes the non-sensitive `emailVerified` state for account-security UI. Application-specific profile fields belong in a separate module or extension table.

## Dependencies

This component is dependency-free at the Buildable Comps layer. The current implementation uses SQLAlchemy and the shared FastAPI core.

## Security

Email verification and password recovery are supplied by the required authentication component. Email changes and account deletion remain separate lifecycle capabilities so consumers can define retention and audit policy explicitly.
