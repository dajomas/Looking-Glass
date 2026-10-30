# HTTP API

All JSON endpoints need a session cookie. State-changing calls need the header
`X-CSRF-Token: <token>`; the token is in `<meta name="csrf-token">` on every
page. Application errors look like `{"ok": false, "error": "..."}`. Request-schema
validation errors use HTTP 422 with FastAPI's `detail` list.

