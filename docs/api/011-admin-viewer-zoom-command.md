## Admin viewer-zoom command

New admin-only, management-authorized and CSRF-protected `POST /api/maps/{map_id}/viewer-zoom` body:

```json
{"x":100,"y":100,"cache_token":"<map token>","walls_version":1,"fog_version":2}
```

Coordinates are source-map image pixels, finite and nonnegative. The endpoint requires that this map is the campaign's active map, validates incarnation/wall/fog versions, reads a consistent fog snapshot and checks that the point resolves to a revealed area. Management permission, active-map identity and versions are rechecked after the background lookup. Hidden/out-of-map points do not broadcast. Inactive/stale targets return the existing 400 error path; management permission failures follow normal authorization handling. It never activates a map, mutates fog/doors, creates checkpoints, bumps versions or writes camera records.

Responses: `{"ok":true,"sent":true,"viewers":2}` when sent to subscribed screens; `{"ok":true,"sent":false,"viewers":0}` when none are connected; hidden/ineligible targets additionally return `"reason":"not-revealed"`. Counts are subscriber counts, not delivery/application acknowledgments.

The existing campaign WebSocket can now carry:

```json
{"type":"viewer-zoom","command_id":"<unique hex id>","version":"1:token-1-2","point":{"x":100,"y":100}}
```

No hidden geometry or component IDs are sent. The viewer deduplicates recent command IDs, refreshes if needed, requires the command's map version to match its displayed map, and reuses the unchanged authorized GET area-bounds/local toggle path. Newer commands or local navigation supersede pending work. This does not introduce a viewer write endpoint; the local double-click read-only API and image/state shapes remain unchanged. Commands are live-only and not replayed on reconnect.


