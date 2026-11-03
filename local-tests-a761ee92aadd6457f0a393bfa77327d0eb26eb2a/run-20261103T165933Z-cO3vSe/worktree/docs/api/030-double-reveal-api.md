## Double-reveal API

All paths below are on the admin app, under `/api/maps/{map_id}/double-reveal`.
Ownership/superadmin authorization applies to every route. Every write requires the existing
CSRF header and executes under a write transaction. These routes are not installed on the
viewer app. Artwork and masks have `Cache-Control: no-store`.

| Method | Suffix | Behavior |
|---|---|---|
| GET | (empty) | Read configuration, geometry validity, visibility, revisions, active map and destination choices |
| GET | `/room?x=...&y=...` | Read selected room and current configuration without changing fog |
| GET | `/room-mask?x=...&y=...` | DM-only PNG selection highlight |
| GET | `/artwork?appearance=current|initial|true` | DM-only current composite, original, or full alternate artwork |
| POST | `/image` | Multipart `file` plus concurrency stamp; upload/replace aligned alternate image |
| POST | `/room` | Enable/update/disable a room and optional destination |
| POST | `/appearance` | Explicit initial/true change, recorded in appearance history |
| POST | `/undo` | Reverse latest appearance action, not fog history |
| DELETE | `/rooms/{area_key}` | Remove a configuration/history, including stale geometry |
| POST | `/travel` | Explicit state-preserving switch to configured destination |

The concurrency stamp is `cache_token`, `walls_version`, `fog_version`, `image_revision`.
GET responses include those fields. Use the latest values, including after each successful
write. JSON inputs reject extra fields; booleans are strict. Stale state and invalid geometry
return 400 and must be re-read, not blindly retried. Missing/invalid CSRF returns 403.

`/room` JSON adds `x`, `y`, `revision` (0 if not configured), `enabled`, and
`destination_map_id` (another same-campaign map ID or null). `/appearance` adds `area_key`,
`revision`, `true_active`. `/undo` and DELETE accept only the stamp. `/travel` adds
`area_key`, `revision`, `expected_active_map_id`; success returns `map_id` and `editor_url`.
Upload uses the same stamp as multipart form fields and rejects mismatched normalized image
dimensions. Replacing artwork retains runtime room state. Returned room rows include
`true_active`, `revision`, `revealed`, `valid_geometry`, optional room name and destination.
The existing admin map metadata adds `double_reveal_image`; viewer state has no alternate URL.

