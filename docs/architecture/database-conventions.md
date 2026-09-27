# Database conventions

PostgreSQL is the deployment database. SQLite is supported for local demonstrations and deterministic unit/API tests where PostgreSQL-specific behavior is not under test.

- Tables and columns use `snake_case`.
- IDs are application-generated UUID strings for database portability.
- Timestamps are UTC and timezone-aware.
- Foreign keys define intended delete behavior.
- Indexes require a query or constraint justification.
- Repositories own queries; application services own transactions.
- Migration names describe behavior and are never silently destructive.
- Applied migrations are immutable.

CI applies, downgrades, and reapplies the migration against PostgreSQL. Future migrations containing data transforms must include explicit rollback and production-size performance notes.
