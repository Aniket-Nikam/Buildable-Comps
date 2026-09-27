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
- Configure SMTP or inject a durable notification adapter; never log raw verification or reset tokens.
- Deny authorization by default and use exact permission checks at every protected boundary.
- Record administrative authorization changes without secrets in audit metadata.
- Apply least privilege to database and deployment credentials.
- Keep CORS origins explicit.
- Review logs for sensitive fields before adding new structured context.
- Validate upload type and size before adding file modules.
- Use parameterized ORM operations and reviewed migrations.

Production configuration rejects the in-memory authentication limiter, unverified-email access, and the in-memory notifier. The development adapters remain available only for local development and isolated tests. See the [Identity 1.0 review](docs/security-review-2026-09-27.md) and [deployment runbook](docs/deployment.md).
