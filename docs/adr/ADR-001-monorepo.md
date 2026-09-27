# ADR-001: Use a monorepo

Status: accepted

Buildable Comps keeps contracts, framework adapters, migrations, metadata, tests, and examples in one repository. This makes cross-language compatibility changes reviewable in one commit and lets CI verify consumers with producers.

Separate repositories could grant independent release cadence, but would add version skew and discovery overhead before boundaries are proven. Packages can be published independently later without moving their source.
