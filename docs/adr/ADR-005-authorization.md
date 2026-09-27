# ADR-005: Database-backed exact-match RBAC

## Status

Accepted.

## Decision

Authorization is a separate component that depends on Identity rather than expanding the authentication service. Users receive roles, roles receive exact-match permissions, and protected FastAPI routes use a dependency guard. React consumers receive the effective permission set through an optional provider and render with a permission guard.

Every administrative mutation writes an append-only authorization audit record in the same transaction. The reusable module supplies only its own management permissions. Consuming applications define domain permissions and seed them through the public service or API.

## Consequences

- Authentication can be reused without authorization.
- Permission names are explicit and searchable in manifests and code.
- Exact matching avoids surprising wildcard escalation.
- Effective-permission reads use relational joins and can later be cached behind the public service boundary.
- The first administrator requires an explicit, one-time bootstrap command to avoid an unauthenticated setup endpoint or implicit first-user elevation.
