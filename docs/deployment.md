# Production deployment

`compose.production.yaml` is a hardened single-host baseline, not a hosting-provider account. It keeps PostgreSQL and Redis off public ports, binds the API and web containers to localhost for a host reverse proxy, requires secure cookies and verified email, persists both data services, and refuses to start without production secrets.

## Deploy

1. Provision a Linux host, DNS, and a reverse proxy or load balancer that terminates HTTPS.
2. Copy `.env.production.example` to a secret-managed location outside the repository and replace every example value.
3. Point `DATABASE_URL` and `REDIS_URL` at the Compose services or managed equivalents.
4. Configure an SMTP provider that durably queues accepted messages.
5. Start the stack with `docker compose --env-file /secure/path/buildable.env -f compose.production.yaml up -d --build`.
6. Register and verify the first operator, then run `docker compose --env-file /secure/path/buildable.env -f compose.production.yaml exec api python -m apps.demo_api.bootstrap --email owner@example.com` once.
7. Confirm `/health`, `/ready`, login, verification delivery, password reset delivery, and authorization access through the public HTTPS origins.

## Required operator controls

- Forward the original client IP only from a trusted proxy and overwrite untrusted forwarding headers.
- Rotate the JWT signing key through a planned global-session invalidation window. Current tokens use one symmetric key and do not yet support overlapping key IDs.
- Back up PostgreSQL on a tested schedule and perform restore drills. Treat the named Compose volume as persistence, not backup.
- Monitor API readiness, SMTP rejection rates, Redis memory/availability, PostgreSQL capacity, authentication failures, and authorization audit anomalies.
- Restrict host and provider access with least privilege. Do not expose PostgreSQL or Redis publicly.
- Apply image and dependency updates through CI, then rehearse Alembic upgrade and downgrade against a restored copy before production migration.
- Define audit retention and export policy for `authorization_audit_logs`.

The repository cannot supply DNS, certificates, cloud accounts, backup destinations, SMTP credentials, or monitoring destinations. Those values belong to the deployment environment and must never be committed.
