# HTTP API

All JSON endpoints need a session cookie. State-changing calls need the header
`X-CSRF-Token: <token>`; the token is in `<meta name="csrf-token">` on every
page. Application errors use `{"ok": false, "error": "..."}`. Room-note
request validation errors use HTTP 422 with the shared
`{"ok": false, "error": "field: message"}` envelope, not a FastAPI `detail`
list. Consult each endpoint's contract for its status codes and validation rules.
See [room-note recovery](../room-note-recovery.md).

