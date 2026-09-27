# API conventions

HTTP endpoints are versioned under `/api/v1`. Health endpoints remain unversioned for infrastructure compatibility.

Success responses contain `success`, `data`, and `meta`. Errors contain a stable code, safe message, details, and request ID. Validation paths use request locations such as `body.email`.

Authentication uses bearer access tokens. Refresh and logout use a scoped HttpOnly cookie. Registration returns `201`; invalid credentials and sessions return `401`; unavailable accounts return `403`; duplicate unique resources return `409`; invalid input returns `422`; rate limits return `429`.

Clients should branch on error code rather than message text. Request IDs may be supplied through `X-Request-ID` and are always returned.
