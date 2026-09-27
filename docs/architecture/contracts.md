# Contract strategy

The HTTP API is the cross-language source of truth. TypeScript interfaces in `packages/contracts` model that wire format. FastAPI schemas generate OpenAPI for runtime and tooling consumers.

Contract tests verify that registered paths remain present. As additional backend implementations are introduced, the OpenAPI document and behavior fixtures should become implementation-neutral compatibility tests.

Changes to field names, required values, error codes, endpoint methods, or event names are public contract changes. Additive optional fields are normally minor versions. Removing or reinterpreting fields requires a major version and migration guidance.
