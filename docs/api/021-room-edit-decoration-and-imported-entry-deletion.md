## Room edit decoration and imported-entry deletion

- POST /api/maps/{map_id}/room-edit-overlay: `{x,y,area_key}`. Requires map campaign
  management permission and CSRF; returns `{ok,area_key,png}` where png is a base64
  RGBA PNG at fog work resolution. It marks only that room's interior and validates
  the geometry key. Outside/wall/stale-room selections return 400. Read-only with
  respect to database/fog; this route exists only on the admin app.
- DELETE /api/maps/{map_id}/room-note-library/{entry_id}: requires management and
  CSRF. Under BEGIN IMMEDIATE, rechecks that the entry exists on this map and its
  normalized name is not assigned before deleting. Missing/wrong-map/assigned
  entries return 400 with no mutation. Success returns `{ok,entries}`. Saved map
  room records and fog are never deleted. There is no library deletion undo.
- Library list/import/delete entries now include `notes_match: boolean` as well
  as assigned: true if any matching-name saved room has equal Markdown after CRLF
  normalization. Assignment protection is name-based even when notes_match=false.

