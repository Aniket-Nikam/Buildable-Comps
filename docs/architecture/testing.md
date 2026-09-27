# Testing strategy

Tests prioritize observable contracts:

- Node tests verify missing and circular dependency detection.
- React component tests verify session bootstrap and registration behavior.
- FastAPI tests verify the complete auth/profile lifecycle and error envelopes.
- Contract tests verify that manifest-advertised identity paths remain in OpenAPI.
- CI verifies migration upgrade, downgrade, and re-upgrade on PostgreSQL.
- A marked integration test runs the authentication lifecycle against that migrated PostgreSQL service.

SQLite keeps local API tests isolated and fast. The PostgreSQL case runs whenever `TEST_POSTGRES_URL` is configured and otherwise skips locally without hiding the rest of the suite.

Factories should use realistic but non-sensitive data. Tests must not depend on execution order, external networks, wall-clock sleeps, or production secrets.
