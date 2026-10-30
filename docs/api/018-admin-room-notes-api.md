## Admin room notes API

All routes require campaign management permission and exist only on the admin
app. POST requests require the existing X-CSRF-Token header.

- `POST /api/maps/{map_id}/room-at`: `{x,y}` in image coordinates. Read-only
  lookup returning `ok,area_key,revealed,name,markdown,html,revision`.
  Wall pixels and out-of-map coordinates return 400. An unnamed room has revision 0.
- `POST /api/maps/{map_id}/room-notes`: `{x,y,area_key,name,markdown,revision}`.
  Saves or renames the room and returns the same shape. `name` is trimmed and
  may be empty (max 200); Markdown max 100000. Revision is 0 for creation.
  Geometry/revision mismatches return 400 without overwriting data. SQLite's
  immediate transaction serializes validation and save. Saving does not mutate fog.
- `GET /api/maps/{map_id}/room-notes`: `{ok,rooms:[{area_key,name,x,y,active,revealed}]}`.
  Includes inactive, preserved records after geometry changes. No viewer route exists.

Normal point reveal/hide requests now return `changed:false` when the requested
state already holds; these requests do not add history, bump fog_version,
checkpoint display state or notify viewers. Existing response fields are retained.
This optimization does not change the managed-door gesture endpoints.

