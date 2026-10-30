## Admin room notes API

All routes require campaign management permission and exist only on the admin
app. POST requests require the existing X-CSRF-Token header. Responses carrying
room context use no-store.

- `POST /api/maps/{map_id}/room-at`: `{x,y}` in image coordinates. Returns the
  selected room's metadata and validation context, including `area_key`,
  `revision`, `cache_token`, `walls_version` and `room_notes_version`.
  Wall pixels and out-of-map coordinates return 400. An unnamed room has revision 0.
  Lookup can reconcile stale assignments; it does not automatically recover notes.
- `POST /api/maps/{map_id}/room-notes` requires `x,y,area_key,revision,cache_token,
  walls_version,room_notes_version`, with the name/Markdown edit fields. Use the
  context returned by the actual selection unchanged. All five validation fields
  are required: area_key is a 64-character string, cache_token is a strict string
  of 1-128 characters, and the three counters are strict nonnegative integers.
  Missing/invalid context uses 422; stale geometry, incarnation, generation or
  revision uses 400 without overwriting notes. Do not restamp an old draft.
  Names retain explicit-save trimming and may be empty (max 200 characters);
  Markdown max 100000. Revision is 0 for creation. Validation, reconciliation
  and save share SQLite's immediate transaction. Success returns refreshed room
  context. Saving does not mutate fog, activate maps or notify viewers.
- `GET /api/maps/{map_id}/room-notes` lists ordinary room associations. Detached
  retained content is managed through the separate archive API, not an inactive
  room-list record to be edited or automatically reassigned. No viewer route exists.
- `GET /api/maps/{map_id}/room-note-archives` lists retained entries with pagination.
- `POST /api/maps/{map_id}/room-note-archives/{archive_id}/recover` requires current
  selected-target context and explicit recovery. Replacing nonempty saved content
  additionally requires overwrite confirmation and archives that content first.
  The source archive remains; recovery changes notes only. See the complete
  [archive listing/recovery contract](../room-note-recovery.md) for payloads,
  limits, provenance and error handling, and [portability](../room-note-backup.md).

Room-note request validation uses HTTP 422 with the shared
`{ok:false,error:"field: message"}` envelope rather than a detail array. Existing
authorization and CSRF errors remain. Archives retain exact saved names/Markdown
before invalid active assignments and imported-name reservations are released.
They do not reattach automatically if old geometry returns.

Normal point reveal/hide requests return `changed:false` when the requested
state already holds; these requests do not add history, bump fog_version,
checkpoint display state or notify viewers. Existing response fields are retained.
This optimization does not change the managed-door gesture endpoints.

