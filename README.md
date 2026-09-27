# Buildable Comps

Buildable Comps is a monorepo for reusable, tested software capabilities that can be discovered and composed by developers and coding agents. It is an internal platform and SDK, not a snippet library.

The current release proves the architecture with users, hardened password authentication, replay-safe refresh sessions, provider-backed recovery delivery, database-backed authorization, PostgreSQL persistence, a FastAPI API, and a React interface.

## Why it exists

Application teams repeatedly implement the same identity, validation, data access, error, form, and infrastructure behavior. Buildable Comps gives those capabilities explicit contracts, machine-readable manifests, predictable locations, and integration tests. A future agent can inspect a manifest and public API before reading implementation details.

## Current capabilities

- Component manifests validated by JSON Schema
- Generated component registry and dependency-cycle detection
- Central API success, error, and validation envelopes
- Typed React and TypeScript contracts
- Environment validation with production security checks
- Structured JSON logging, request IDs, security headers, and health checks
- Users and editable basic profiles
- Argon2 password hashing
- Short-lived JWT access tokens
- Rotating, revocable refresh sessions stored as token digests
- Refresh-family reuse detection with whole-family revocation
- Single-use email verification and password recovery tokens
- Immediate access-token invalidation after password reset
- Redis-backed authentication rate limiting for multi-worker deployments
- SMTP identity notification adapter with validated production configuration
- Project-defined roles and exact-match permissions
- FastAPI permission guards and React permission-aware rendering
- Audited role, permission, and assignment administration
- React authenticated state, registration, login, logout, and profile UI
- Alembic migrations for PostgreSQL and SQLite
- PostgreSQL-backed authentication and live Redis integration coverage in CI
- Unit, API, component, tooling, and contract tests
- Docker Compose development stack and GitHub Actions CI

The password-authentication and users components are stable at `1.0.0`. Authorization is `beta` while its administration workflow gains broader integration use. OAuth is a separate planned capability, not a requirement of the password-authentication contract.

## Architecture

```text
apps/
  demo_api/             FastAPI composition root
  demo-web/             runnable React consumer
backend/python/
  buildable_core/       config, errors, events, database, observability, security
  buildable_identity/   user and authentication implementation
  buildable_authorization/ roles, permissions, guards, assignments, audit
components/
  auth/                 machine-readable manifest and integration guide
  authorization/        authorization manifest and integration guide
  users/                machine-readable manifest and integration guide
database/migrations/    Alembic migration history
frontend/react/         reusable React auth package
packages/contracts/     shared TypeScript API contracts
registry/               manifest schema and generated registry
scripts/                registry and dependency validation
tests/python/           API and contract tests
docs/                   architecture and decision records
devops/                 production-oriented container definitions
```

Framework code points inward to reusable application and domain behavior. The demo applications are composition roots; they do not contain duplicate identity implementations. See [the architecture overview](docs/architecture/README.md) and [module boundary rules](docs/architecture/module-boundaries.md).

## Supported technologies

The verified first slice supports:

- React 19 and TypeScript
- FastAPI and Python 3.12+
- PostgreSQL 16+ for deployment
- SQLite 3.40+ for lightweight development and isolated tests
- Node.js 22+

Next.js and Express are planned compatibility targets, not implemented components.

## Start with Docker

Docker is the shortest path to the PostgreSQL-backed example:

```bash
docker compose up --build
```

Open the web application at `http://localhost:8080`, the API documentation at `http://localhost:8000/docs`, and the liveness endpoint at `http://localhost:8000/health`.

The Compose credentials are development-only. Replace every secret before deploying. See the [production deployment runbook](docs/deployment.md) for the strict production Compose overlay and operator checklist.

## Local development

### Install

```bash
npm install
python -m venv .venv
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Start PostgreSQL and Redis through Docker, apply the migrations, then run both processes:

```powershell
docker compose up -d postgres redis
alembic upgrade head
npm run dev:api
```

In a second terminal:

```powershell
npm run dev:web
```

For a lightweight local setup, set `DATABASE_URL=sqlite+pysqlite:///./buildable.db` and `RATE_LIMIT_BACKEND=memory` in `.env` before applying the migrations. The in-memory limiter is intentionally rejected in production.

## Verification commands

```bash
npm run registry:build
npm run registry:validate
npm run format:check
npm run lint
npm run typecheck
npm test
npm run build
ruff check backend/python apps/demo_api tests/python
ruff format --check backend/python apps/demo_api tests/python
mypy
pytest
alembic upgrade head
```

`npm run check` runs the complete JavaScript and registry validation sequence.

## Component discovery

Start with [registry/components.json](registry/components.json). Each entry includes:

- capabilities provided
- required Buildable Comps modules
- framework and database compatibility
- public exports and HTTP endpoints
- environment variables and permissions
- events, migrations, tests, and documentation

The registry is generated from `components/*/component.json`:

```bash
npm run registry:build
npm run registry:validate
```

Do not edit the generated registry by hand.

## API conventions

Success responses use:

```json
{
  "success": true,
  "data": {},
  "meta": {}
}
```

Errors use a stable machine code, a safe human message, structured details, and the request ID in `meta`. Full conventions are documented in [API conventions](docs/architecture/api-conventions.md).

## Maturity and versioning

Components progress through `experimental`, `beta`, `stable`, and `deprecated`. Stable requires documentation, contract and integration tests, validated metadata, a security review appropriate to risk, and migration safety. Packages and components follow semantic versioning. See [component lifecycle](docs/architecture/component-lifecycle.md).

## Contribution rules

Read [AGENTS.md](AGENTS.md) before using a coding agent and [CONTRIBUTING.md](CONTRIBUTING.md) before changing shared modules. Public contracts require compatibility review. Application-specific behavior belongs in the consuming app, not in a reusable package.

## Roadmap

Authorization has started with roles, permissions, backend and frontend guards, typed administration APIs, explicit bootstrap, and transactionally written audit history. The next authorization increment is a reusable user-search and role-management UI, followed by policy composition for resource ownership. Files, caching, realtime, organizations, and AI adapters remain planned capabilities rather than placeholder implementations.
