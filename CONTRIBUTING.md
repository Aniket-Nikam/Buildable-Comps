# Contributing

Changes should improve a reusable contract or its verified implementation. A new component needs a real consumer or integration test; a directory tree of placeholders is not a component.

## Change process

1. Search the generated registry for an existing capability.
2. Write or update the public contract first.
3. Keep framework adapters outside domain logic.
4. Add a component manifest and concise integration documentation.
5. Add behavior-focused tests, including failure paths.
6. Regenerate and validate the registry.
7. Run formatting, linting, type checking, tests, and builds.
8. Record an ADR only for a decision with meaningful, long-lived tradeoffs.

Commit messages should describe the behavior changed. Pull requests should identify affected public contracts, migrations, security considerations, and commands executed.
