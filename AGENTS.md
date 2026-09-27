# Instructions for coding agents

Buildable Comps is optimized for reuse. Before generating a feature, inspect the registry and reuse a compatible module whenever possible.

## Required workflow

1. Read `registry/components.json` and search `provides`, `category`, and compatibility fields.
2. Read the selected component's `component.json`, `README.md`, and public exports before implementation files.
3. Resolve every item in `requires`; do not copy a component without its dependencies.
4. Treat contracts, public exports, HTTP paths, event names, and migrations as compatibility boundaries.
5. Keep project-specific rules in the consuming application. Change a shared module only when the behavior is genuinely reusable.
6. Do not create a second implementation when a compatible component already exists.
7. Validate new and changed manifests with `npm run registry:validate`.
8. Regenerate `registry/components.json` with `npm run registry:build` after manifest changes.
9. Run affected unit, contract, integration, and migration tests.
10. Preserve backward compatibility. If a public contract must break, use a major version and provide migration guidance.

## Module map

- `packages/contracts`: language-level public API contracts for frontend consumers
- `frontend/react`: public React components, auth state, and API client
- `backend/python/buildable_core`: shared FastAPI infrastructure with no identity-specific rules
- `backend/python/buildable_identity`: users and authentication domain
- `apps/demo_api`: dependency wiring only
- `apps/demo-web`: example consumer and visual integration proof
- `components`: discovery metadata and concise integration documentation
- `registry`: generated discovery index and its JSON Schema
- `database/migrations`: ordered, reversible database changes
- `tests`: cross-module API and contract verification

## Public and internal code

Exports from package `__init__.py` and `src/index.ts` files are public. Routes listed in manifests are public. Other implementation files are internal unless their component documentation says otherwise.

Do not import internal files from consuming applications. Add a deliberate public export when a reusable interface is needed.

## Database changes

Never edit an applied migration. Add a descriptively named migration, preserve data where practical, add justified constraints and indexes, and verify upgrade plus downgrade against PostgreSQL. Keep transaction boundaries in application services, not route handlers or repositories.

## Completion checks

Run the smallest affected test set while iterating. Before handing off a shared change, run:

```bash
npm run check
ruff check backend/python apps/demo_api tests/python
ruff format --check backend/python apps/demo_api tests/python
mypy
pytest
alembic upgrade head
```

Never suppress, delete, or weaken a failing test to report completion.
