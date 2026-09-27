# Identity 1.0 security review

Date: 2026-09-27  
Scope: `identity.users`, `identity.auth`, shared security/configuration, migrations `0001`–`0002`, SMTP delivery, Redis limiting, and the demo composition root.

## Outcome

The password-authentication and user-profile contracts meet the repository's stable-component criteria. The review found no unresolved high-severity repository defect. Production safety depends on the deployment controls listed below and in the deployment runbook. This was an internal engineering review, not an independent penetration test.

## Evidence reviewed

- Argon2 password hashing and generic credential failures.
- Short-lived signed access tokens with per-user authentication-version invalidation.
- Digest-only storage, rotation, family tracking, revocation, and reuse detection for refresh tokens.
- High-entropy, expiring, single-use verification and reset tokens with enumeration-resistant request responses.
- Redis-backed atomic rate limiting and a live Redis integration test in CI.
- HttpOnly refresh cookies, production-only secure cookies, explicit CORS origins, security headers, and disabled production API docs.
- SMTP or injected provider delivery required in production; the in-memory adapter is rejected.
- PostgreSQL migration upgrade, downgrade, and integration behavior in CI.

## Threat decisions

| Threat                          | Control                                                                    | Residual risk / owner                                                                   |
| ------------------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Credential theft                | Argon2, generic failures, rate limiting, verified-email gate               | MFA and breached-password screening are future independent capabilities.                |
| Refresh-token theft or replay   | HttpOnly cookie, digest storage, rotation, family revocation               | The host application must enforce HTTPS and protect endpoints against script injection. |
| Recovery-token disclosure       | Digest-only database storage, single use, short lifetime, no token logging | SMTP provider and destination mailbox security are operator/provider responsibilities.  |
| Horizontal privilege escalation | User-scoped routes derive identity from bearer token                       | New routes require explicit object-level authorization review.                          |
| Dependency outage               | Readiness checks cover PostgreSQL and Redis                                | Monitoring, redundancy, capacity, and recovery are deployment responsibilities.         |
| Secret disclosure               | Environment-based secrets and committed examples only                      | Use a secret manager and rotate credentials after suspected exposure.                   |

## Required production acceptance

- Valid public HTTPS origins and trusted proxy configuration.
- Random signing key and provider credentials held outside source control.
- Successful email verification and password-reset delivery tests.
- Tested database backups and restore procedure.
- Alerts for readiness failures, authentication abuse, and SMTP rejection.
- Dependency/image scanning and a separate penetration test when risk or compliance requires it.
