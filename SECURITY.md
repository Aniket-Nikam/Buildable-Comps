# Security policy

Do not report vulnerabilities in public issues. Contact the repository owner privately with the affected component, reproduction steps, impact, and any suggested mitigation.

## Baseline controls

- Never commit secrets or production credentials.
- Use a random 32-character or longer signing key in production.
- Require HTTPS and secure cookies in production.
- Keep access tokens in memory and refresh tokens in HttpOnly cookies.
- Store only password hashes and digests of refresh, verification, and reset tokens.
- Treat reuse of a rotated refresh token as compromise and revoke its session family.
- Keep verification and recovery responses resistant to account enumeration.
- Use Redis-backed rate limiting for every production deployment.
- Inject a durable notification adapter; never log raw verification or reset tokens.
- Apply least privilege to database and deployment credentials.
- Keep CORS origins explicit.
- Review logs for sensitive fields before adding new structured context.
- Validate upload type and size before adding file modules.
- Use parameterized ORM operations and reviewed migrations.

Production configuration rejects the in-memory authentication limiter and unverified-email access. The in-memory limiter and notifier remain available only for local development and isolated tests.
