# Testing strategy

Tests prioritize observable contracts:

- Node tests verify missing and circular dependency detection.
- React component tests verify session bootstrap, registration, and permission-aware rendering.
- FastAPI tests verify the complete auth/profile lifecycle and error envelopes.
- Contract tests verify that manifest-advertised identity and authorization paths remain in OpenAPI.
- CI verifies migration upgrade, downgrade, and re-upgrade on PostgreSQL.
- Marked integration tests run the authentication lifecycle against migrated PostgreSQL and the atomic limiter against live Redis.

SQLite keeps local API tests isolated and fast. PostgreSQL and Redis cases run when `TEST_POSTGRES_URL` and `TEST_REDIS_URL` are configured and otherwise skip locally without hiding the rest of the suite.

Factories should use realistic but non-sensitive data. Tests must not depend on execution order, external networks, wall-clock sleeps, or production secrets.
