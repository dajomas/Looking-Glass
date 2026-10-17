# HTTP API

All JSON endpoints need a session cookie. State-changing calls need the header
`X-CSRF-Token: <token>`; the token is in `<meta name="csrf-token">` on every
page. Errors look like `{"ok": false, "error": "..."}`.

## Admin port (5000)

| Method | Path | Body | Purpose |
|---|---|---|---|
| GET | `/api/maps/{id}` | | Map info, calibration, walls (image coords), counts, live state |
| GET | `/api/maps/{id}/image` | | Raw battle map |
| GET | `/api/maps/{id}/fog.png` | | RGBA mask (alpha = revealed) at work resolution |
| GET | `/api/maps/{id}/viewer-preview` | | Exactly the image players receive |
| POST | `/api/maps/{id}/reveal` | `{"x":..,"y":..}` (image px) | Reveal the area at the point; returns `area_fraction`, `leak_warning` |
| POST | `/api/maps/{id}/hide` | `{"x":..,"y":..}` | Hide the area at the point |
| POST | `/api/maps/{id}/reveal-all` | | Reveal everything |
| POST | `/api/maps/{id}/reset` | | Fog everything (undoable) |
| POST | `/api/maps/{id}/undo` | | Undo the last fog operation |
| POST | `/api/maps/{id}/calibration` | `{"offset_x","offset_y","scale_x","scale_y","doors_block"}` | Wall alignment |
| POST | `/api/maps/{id}/walls/inspect` | multipart `file` | List scenes in a wall file |
| POST | `/api/maps/{id}/walls` | multipart `file`, `scene_index`, `use_scene_calibration` | Import / replace walls |
| DELETE | `/api/maps/{id}/walls` | | Remove walls |
| POST | `/api/campaigns/{id}/active` | `{"map_id": 3}` or `{"map_id": null}` | Show a map to players / blank the screen |

HTML form posts (redirect with `?ok=` / `?err=`) cover campaigns
(`/campaigns`, `/campaigns/{id}/update|delete|active`), viewers
(`/campaigns/{id}/viewers/add|create`, `/campaigns/{id}/viewers/{uid}/remove`),
maps (`/campaigns/{id}/maps`, `/maps/{id}/rename|move|image|delete`) and users
(`/users`, `/users/{id}/update|password|delete`, superadmin only).

## Reusable wall sources (admin port only)

All routes below require manage permission for the campaign or map, including
read-only source inspection. Writes require CSRF. Raw source bytes are never
returned; these routes are not registered on the viewer application.

| Method | Path | Body | Result |
|---|---|---|---|
| GET | `/api/campaigns/{id}/wall-sources` | none | `{"ok":true,"sources":[...]}` |
| POST | `/api/campaigns/{id}/wall-sources` | multipart `file` | Validate and save; `{"ok":true,"source":{...}}` |
| GET | `/api/maps/{map_id}/wall-sources/{source_id}` | none | Source summary and `scenes[]`, with map-specific suggested calibration |
| POST | `/api/maps/{map_id}/walls/from-source` | JSON below | Existing map payload plus `imported`, `scene`, and `source_id` |
| DELETE | `/api/campaigns/{id}/wall-sources/{source_id}` | none | `{"ok":true}`; does not remove map walls |

```json
{"source_id": 1, "scene_index": 0, "use_scene_calibration": true}
```

`source_id` and `scene_index` are required. Source IDs are positive; scene indices
are zero-based, non-negative, and must be in range. `use_scene_calibration`
defaults to true. Missing/invalid fields use FastAPI validation errors (422);
unknown or cross-campaign sources and out-of-range indices return 400. Campaign
and map authorization follows the existing access helpers.

Source summaries contain `id`, `filename`, `scene_count`, and `created_at`.
Scene entries contain `index`, `name`, `format`, `walls`, `doors`, `scene_width`,
`scene_height`, and `calibration` (`offset_x/y`, `scale_x/y`). Empty scenes are
filtered by the existing parser; indices refer to this returned list. Duplicate
scene names remain separate choices, distinguished by index.

Uploads obey `storage.max_upload_mb`. Identical bytes in the same campaign
return the same source and retain its original filename. Sources are immutable:
uploading changed bytes creates a new source. Source inspection and saving do
not modify map walls, fog, or calibration. Applying copies walls to the target
map only, invalidates its fog cache, and notifies viewers. Existing fog actions
are preserved and replayed against the new geometry.

The existing one-off `/walls/inspect` and `/walls` APIs remain compatible and
do not save their files automatically. The HTML map upload saves valid wall
sources; a multi-set upload waits for selection instead of choosing index 0.

## Viewer port (5100)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/c/{campaign}/state` | Active map name, size, version and versioned `image_url` (or `map: null`) |
| GET | `/api/c/{campaign}/image` | Fogged composite of the active map |
| WS | `/ws/c/{campaign}` | Pushes `{"type":"refresh","reason":...}`; send `ping` to keep alive |

Both ports also serve `GET /healthz`.

## Pack images and wall-type filters

`GET /api/maps/{map_id}/wall-sources/{source_id}` scene objects additionally
contain `image_available`, `image_is_thumbnail`, and `image_reference`.
Only the authorized campaign manager can inspect these fields.
`POST /api/maps/{map_id}/walls/from-source` accepts `use_pack_image` (boolean,
default false) in addition to source_id, scene_index and use_scene_calibration.
True requires valid embedded artwork; missing/invalid images return 400 without
changing map walls/artwork. The selected artwork applies to both portals.

`POST /api/maps/{map_id}/wall-types` accepts JSON `{"disabled":["door","secret"]}`.
Allowed values are wall, door, secret, window, invisible, ethereal. Unknown
values return 400; invalid body types return 422. Requires campaign-management
permission and CSRF. Returns the ordinary updated map payload, now including
`disabled_wall_types` and a versioned admin-only `image_url`. Existing direct
one-off import endpoints are unchanged; use the saved-source flow for the
optional pack image. No new source/image endpoint is registered on the viewer.
