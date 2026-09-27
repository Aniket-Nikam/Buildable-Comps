# ADR-003: Use short access tokens and rotating refresh sessions

Status: accepted

Access tokens are short-lived bearer JWTs kept in browser memory. Refresh tokens are scoped HttpOnly cookies linked to revocable database sessions. Every refresh revokes the current session and issues a new token and row.

Pure stateless JWTs make logout and revocation weak. Server sessions alone are simpler for one web origin but less portable to API and mobile consumers. The selected hybrid keeps protected API calls straightforward while retaining session control.

Only token digests are persisted. Refresh sessions are linked into families, and replay of a rotated token revokes every active member of that family. Verification and recovery links are high-entropy, single-use tokens delivered through an injected notification boundary. Production requires verified email, secure cookies, HTTPS, a durable notification adapter, and Redis-backed rate limiting.
