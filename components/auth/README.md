# Session authentication

Provides registration, login, email verification, password recovery, replay-safe refresh rotation, logout, a bearer-token guard, and React authenticated state.

## Integration

1. Configure `DATABASE_URL`, `REDIS_URL`, and a 32-character or longer `SECRET_KEY`.
2. Apply all Alembic migrations.
3. Inject an `IdentityNotifier` that durably queues verification and reset messages.
4. Include `buildable_identity.router` in a FastAPI application.
5. Wrap the React application in `AuthProvider`.

Use `RecoveryPanel` on the consumer's verification and password-reset routes, passing the opaque token parsed from the public link. The component never persists that token.

The access token is kept in memory. The refresh token is stored in an HttpOnly, SameSite cookie and rotated inside a tracked family. Reuse of an already-rotated token revokes the whole family.

## Security

Passwords use Argon2 through `pwdlib`. Only SHA-256 digests of refresh, verification, and reset tokens are stored. Recovery request responses do not disclose whether an email exists. Password reset increments an authentication version and revokes every refresh session, invalidating existing access tokens immediately. Production settings require verified emails, HTTPS cookies, and Redis-backed rate limiting.

## Delivery adapter

The included in-memory notifier exists only for development and tests. Production composition fails fast unless an `IdentityNotifier` is injected. The adapter must enqueue messages durably and construct public verification/reset links without logging raw tokens.
