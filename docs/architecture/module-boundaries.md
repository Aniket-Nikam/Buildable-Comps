# Module boundaries

Dependencies point toward contracts and domain behavior:

```text
apps/demo-web -> frontend/react -> packages/contracts
apps/demo_api -> buildable_identity -> buildable_core
                                     -> SQLAlchemy adapters
```

`buildable_core` cannot import identity. `buildable_identity` cannot import either demo application. Demo applications may select concrete adapters and configuration but must not contain reusable domain rules.

Repositories isolate persistence queries. Application services own use-case orchestration and commits. FastAPI routes translate HTTP input and output only. React components use the exported API client and contract types rather than redefining response shapes.

Public APIs are exports from `__init__.py`, `src/index.ts`, and HTTP endpoints listed in manifests. Everything else is internal and may change within a compatible release.
