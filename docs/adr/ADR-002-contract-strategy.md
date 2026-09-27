# ADR-002: Use HTTP and OpenAPI as the cross-language contract

Status: accepted

The first slice uses FastAPI schemas to produce OpenAPI and maintains small TypeScript wire types for the React client. Behavioral contract tests protect semantics that a schema alone cannot express.

Generating every language model immediately would add tooling before a second backend exists. When Express support begins, OpenAPI generation for clients and shared behavior fixtures should replace manual duplication.
