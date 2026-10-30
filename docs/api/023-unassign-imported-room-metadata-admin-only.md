## Unassign imported room metadata (admin only)

`POST /api/maps/{map_id}/room-note-library/{entry_id}/unassign`

Requires an authenticated campaign manager and the normal `X-CSRF-Token` header.
Send `{}` (no fields required). Within an IMMEDIATE database transaction, reconcile
stale room geometry, resolve the imported entry on this map, then clear `name`
and `markdown` for every saved room whose normalized name matches that entry.
Preserve room rows and increment their revisions so stale editor saves are rejected.
Preserve all imported records. No fog/wall version bump or viewer broadcast occurs.

Response: `{"ok":true,"unassigned":1,"area_keys":["..."],"entries":[...]}`.
`entries` uses the existing library-list shape. Repeating the operation with no
current matching assignments returns zero; a missing/wrong-map entry is rejected
with 400. Normal authorization/CSRF failures are 403. Confirmation is provided by
the UI; the endpoint clears all matching assignments at transaction time, including
changes another session saved since the list was opened. Other maps are never changed.

