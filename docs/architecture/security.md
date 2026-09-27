# Security architecture

Passwords use the current recommended Argon2 configuration from `pwdlib`. Access tokens are short-lived JWTs carrying an authentication version. Refresh tokens are JWTs tied to server-side session rows; only SHA-256 token digests are stored. Successful refresh revokes the previous row before issuing its successor. Reuse of a rotated token is treated as compromise and revokes the entire session family.

Email verification and password recovery use high-entropy, single-use opaque tokens whose SHA-256 digests are stored. Recovery request responses are identical for known and unknown accounts. Password reset increments the authentication version and revokes all refresh sessions, so both access and refresh credentials issued before the reset stop working.

The API uses explicit CORS origins, HttpOnly refresh cookies, generic credential errors, request IDs, rate limiting across every unauthenticated identity mutation, and defensive response headers. Pydantic rejects unknown input fields. SQLAlchemy parameterizes queries.

Production settings fail fast when the development signing key, insecure cookies, unverified-email access, automatic schema creation, in-memory rate limiting, or a missing notification adapter would be used. HTTPS termination, signing-key rotation, trusted proxy configuration, durable notification delivery, database backup, Redis availability, and external monitoring remain deployment responsibilities.
