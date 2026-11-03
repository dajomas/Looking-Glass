## Imported room-note library (admin only)

- `GET /api/maps/{map_id}/room-note-library` returns
  `{ok,entries:[{id,name,markdown}]}` in name/ID order.
- `POST /api/maps/{map_id}/room-note-library/import` accepts a multipart `file`
  (UTF-8 Markdown; 1 MiB maximum). Returns `{ok,added,sections,heading_level,
  ignored_preamble,entries}`. The entire input validates before the append transaction.
  Unparseable/no-heading/oversize/invalid sections return 400; POST requires CSRF.

Both require management permission on the map's campaign. Library entries are
map-scoped and not exposed by the viewer app. Selecting an entry is client-side
and creates a draft; assignment uses the existing room-notes save API with its
geometry and revision validation. There is no implicit save, import overwrite,
assignment lock or consumption of entries. Duplicate name/content pairs are ignored.

### Clearing room metadata

POST /api/maps/{map_id}/room-notes now accepts empty `name` and/or `markdown`.
Both default to empty strings if omitted. Sending both empty clears the metadata
while retaining the room_notes row and incrementing its revision, preventing
stale clients from recreating cleared text using an old revision. Existing
campaign-management, CSRF, geometry and revision checks still apply. There is no
new delete route. The imported-note picker can fill replacement drafts for any
room; it uses the same save route and never implicitly overwrites server data.

