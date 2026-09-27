# ADR-004: Generate the registry from component manifests

Status: accepted

Every component owns a validated `component.json`. A deterministic script discovers manifests and builds one registry. Dependencies use stable component IDs, which allows missing-dependency and cycle checks.

Hand-maintaining both manifests and a registry would create drift. A database or service would add deployment requirements to a repository-local discovery problem. JSON plus JSON Schema is portable for humans, CI, and coding agents.
