# Architecture overview

Buildable Comps separates discovery, contracts, implementations, and composition roots.

```text
component manifest -> generated registry -> developer or coding agent
        |                                      |
        v                                      v
 public contracts -> reusable adapters -> thin example application
        |                    |
        +---------- tests ---+
```

## Principles

- The manifest is the discovery entry point, not the implementation.
- Public contracts are small and explicit.
- Framework adapters implement domain-facing interfaces.
- Composition roots own configuration and dependency wiring.
- Transaction boundaries sit in application services.
- Database migrations are reviewed public integration requirements.
- Example apps consume shared modules and prove integration without duplicating them.

## Reusable vertical slices

The React client calls a standardized FastAPI contract. The API delegates authentication behavior to `AuthenticationService`, which coordinates repositories, password hashing, token creation, refresh-session rotation, and events. SQLAlchemy supports PostgreSQL in deployment and SQLite in isolated tests.

Authorization remains a separate component over the public Identity boundary. `AuthorizationService` coordinates roles, permissions, assignments, and audit records. FastAPI dependencies and React providers adapt that service into backend and frontend guards without coupling authentication to application-specific roles.

The in-process event publisher is intentionally small. A transactional outbox can replace it without moving domain behavior into a message broker.

## Cross-cutting behavior

Configuration, errors, database setup, logging, request IDs, health checks, security headers, and rate limiting live in `buildable_core`. Identity imports those facilities, while core never imports identity.

Related documents:

- [Module boundaries](module-boundaries.md)
- [Contracts](contracts.md)
- [Database conventions](database-conventions.md)
- [API conventions](api-conventions.md)
- [Security architecture](security.md)
- [Testing strategy](testing.md)
- [Component lifecycle](component-lifecycle.md)
- [Production deployment](../deployment.md)
