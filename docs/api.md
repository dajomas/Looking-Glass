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

## Viewer port (6000)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/c/{campaign}/state` | Active map name, size, version and versioned `image_url` (or `map: null`) |
| GET | `/api/c/{campaign}/image` | Fogged composite of the active map |
| WS | `/ws/c/{campaign}` | Pushes `{"type":"refresh","reason":...}`; send `ping` to keep alive |

Both ports also serve `GET /healthz`.

## Explicit map-display reveal policy

`POST /api/campaigns/{id}/active` now requires `fog_action` whenever `map_id`
is non-null:

```json
{"map_id": 3, "fog_action": "restore"}
```

Use `"reset"` to delete the target map's fog-operation history before activating
it. Missing policy returns 400; unsupported values return validation error 422.
`{"map_id": null}` blanks the screen without requiring a policy. The HTML form
endpoint `/campaigns/{id}/active` accepts the same `fog_action` values. Existing
API clients must be updated; there is intentionally no silent default.

The update is transactional: checkpoint the outgoing map, restore/reset the
target, bump its fog version, checkpoint it, then activate it. Existing campaign
ownership and CSRF checks still apply. Display reset is not undoable.

Admin map JSON adds `cache_token`, an opaque unique map-incarnation identifier.
Viewer state `version` is opaque; use the supplied `image_url` rather than
constructing one. Versioned viewer image requests reject an obsolete `v` with
400 so a URL for an old state cannot receive the current map. Viewer composites,
admin raw images and admin masks use `Cache-Control: no-store`.

## Dedicated wall editor and UVTT export (admin only)

All reads require manage access to the target map. Both POST routes require
CSRF, including draft export. None of these routes is mounted on the viewer app.

| Method | Path | Purpose |
|---|---|---|
| GET | `/maps/{id}/walls` | Separate HTML wall editor |
| GET | `/api/maps/{id}/wall-editor` | Full-precision walls in image pixels, dimensions, walls_version, cache_token and image_version; no-store |
| POST | `/api/maps/{id}/wall-editor` | Atomically replace map walls and save an immutable campaign UVTT source |
| POST | `/api/maps/{id}/wall-editor/export` | Download a draft without saving it |
| GET | `/api/maps/{id}/walls.uvtt` | Download the currently saved wall set |

Save JSON:
```json
{"walls_version": 3, "cache_token": "opaque-map-token", "pixels_per_grid": 70,
 "walls": [[10, 20, 100, 20, "door", true]]}
```

Each segment has exactly six values: x1, y1, x2, y2, kind, blocks. Supported kinds
are wall, door, secret, window, invisible and ethereal. Coordinates must be finite
numbers within +/-10000000, endpoints must differ, and blocks must be a JSON
boolean. Ethereal must have blocks=false. At most 100000 segments are allowed;
empty sets are supported. pixels_per_grid defaults to 70, must be finite,
positive and at most 10000000. Generated bytes obey storage.max_upload_mb.
Invalid geometry returns 400; missing/invalid model fields return 422.

Save takes an immediate SQLite transaction before rechecking walls_version and
cache_token. A mismatch returns 409 without saving a source or changing the map.
A successful response is the editor-state payload plus source_id. Geometry is
normalized to image pixels (identity alignment). Doors split areas, per-map
disabled types, fog histories/snapshots, artwork and active-map state are retained.
Wall/fog versions are bumped; fog caches are invalidated and viewers notified.

Draft export accepts the save JSON plus required width, height and image_version,
and optional include_image (false by default). Dimensions must be positive and
at most 1000000 each. It returns a JSON attachment named map-{id}-walls.uvtt.
A stale draft can still be downloaded without artwork. With artwork requested,
cache_token, image_version and dimensions must match the current map, otherwise
409 is returned. Draft export makes no persistent changes.

Saved-set GET export accepts include_image=true and pixels_per_grid=70 as query
parameters. Downloads use Cache-Control: no-store. Embedded artwork is the
canonical normalized PNG, base64 encoded. Size limits apply to complete exports.

The new exporter stores standard UVTT 0.2 geometry plus a looking_glass version-1
extension preserving kinds and blocking flags, including otherwise omitted
ethereal segments. A geometry checksum rejects a stale extension after another
program edits the standard fields; remove looking_glass to import only the
standard geometry. Ordinary UVTT and Foundry parsing remain unchanged.
Unlike empty Foundry scenes, an explicitly empty UVTT set is retained.
See [wall-editor.md](wall-editor.md) for fallback semantics and limitations.


## Door arrow settings

Admin map payloads include `door_arrow_color` (`#RRGGBB`) and `door_arrows_enabled` (boolean, default true).

`POST /api/maps/{map_id}/door-arrows` requires campaign-management permission and CSRF. It accepts partial JSON updates: `{"enabled":false}`, `{"color":"#46c0ff"}`, or both fields. Omitted/null fields preserve current values. Enabled must be a strict JSON boolean; color must be a six-digit hexadecimal string. Colors are normalized to lower case. The response is the updated map payload. Saving increments `fog_version` and broadcasts the existing viewer refresh without appending a fog action or modifying fog checkpoints.

`GET /api/maps/{map_id}/door-arrows.png` requires management permission and returns a no-store transparent RGBA PNG at work resolution; it is fully transparent when disabled. Viewer API payloads do not change: the authorized fogged image includes arrows when enabled. No wall or hidden-room geometry is exposed to players.
