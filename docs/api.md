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


## Door arrow settings and actions

Admin map payloads include `door_arrow_color` (`#RRGGBB`), `door_arrows_enabled` (boolean, default true) and `work_scale` (work pixels per source image pixel).

- `POST /api/maps/{map_id}/door-arrows`: authenticated campaign manager plus CSRF. Accepts partial JSON updates `{"enabled":false}`, `{"color":"#46c0ff"}`, or both. Omitted/null fields preserve current values. Enabled must be a strict JSON boolean; color is a six-digit hexadecimal string, normalized lower-case. Saves preferences, bumps fog version, broadcasts refresh and returns map state without adding a fog action/checkpoint.
- `GET /api/maps/{map_id}/door-arrows.png`: management-only, no-store RGBA overlay at work resolution; transparent when disabled.
- `POST /api/maps/{map_id}/door-arrows/reveal`: authenticated campaign manager plus CSRF. Body: `{"x":175.5,"y":100.5,"cache_token":"<map incarnation>","walls_version":1,"fog_version":1}`. Coordinates identify the clicked visible arrow pixel in image space, not a client-selected target room. The server recomputes the enabled arrow and resolves a verified open pixel in the opposite hidden area. A successful request appends one ordinary reveal operation, bumps fog version, checkpoints if active, broadcasts normal refresh and returns the updated map payload with `area_fraction` and `leak_warning`.

The click endpoint holds a SQLite write transaction across stamp validation and mutation. Stale incarnation/version stamps or a point with no enabled visible arrow return 400 without a fog write. Repeating the same click stamp is rejected after the first reveal. Management authorization is checked before topology use. Viewer endpoints remain unchanged and read-only: only composited imagery is delivered, never hidden target coordinates or wall geometry.


## Locked and unlocked doors

The existing management/CSRF-only `POST /api/maps/{id}/door-action` now also
handles secret doors and portal Entries. The body retains wall_id, x, y, gesture
(single/double), hit (arrow/wall), mode, tolerance, cache_token, walls_version and
fog_version, and adds `side` (default -1 for doors; 0/1 for portal Entries).
The server resolves destinations and rejects mismatched side IDs, stale stamps,
invalid hits, hidden/disabled arrows and Exit-only hints. No viewer route is added.

Response door_action is none, lock, unlock, discover, reveal or hide. Only arrow
doubles toggle/discover; segment doubles do not change state. Discovery does not
reveal. Lock/discovery bump versions, not fog history. Already revealed persistent
destinations return none without recording another reveal. Legacy arrow-reveal
rejects locked/undiscovered-secret targets. All actions retain existing transaction,
permission, CSRF and refresh handling. See Passages.md for reset semantics.

## Independent arrow visibility API

The management-only map payload adds `admin_door_arrows_enabled` and `viewer_door_arrows_enabled`. Existing `door_arrows_enabled` remains an alias for the admin flag and is still used to generate admin overlays/hit geometry.

`POST /api/maps/{map_id}/door-arrows` retains management authorization and CSRF, accepts strict optional booleans `admin_enabled` and `viewer_enabled`, and supports partial updates. Examples: `{"admin_enabled":false}` hides only admin arrows; `{"viewer_enabled":false}` hides only viewer arrows. Omitted/null fields preserve stored values. Existing `color` and `locked_color` behavior is unchanged.

For compatibility, legacy `enabled` still updates BOTH flags. Explicit per-screen fields take precedence over that legacy shared value if both are supplied. The write transaction preserves unrelated flags/colors, fog history, runtime locks and checkpoints. Viewer visibility or either shared color changing bumps fog version and publishes refresh; an admin-only visibility change does neither. The response always returns updated admin map state.

The admin PNG and arrow action endpoints honor admin visibility, never viewer visibility. Viewer images and exact image preview honor viewer visibility, never admin visibility. No viewer write endpoint or viewer-state schema change is needed. Hidden arrows cannot be used as admin click targets; direct wall-segment behavior is unchanged.


## Viewer revealed-area framing lookup

New read-only `GET /api/c/{campaign_id}/area-bounds?x=100&y=100&v=<viewer-version>` requires the existing viewer session and campaign-view authorization. Coordinates are source-map image pixels; `v` is the version returned with the currently displayed map. It returns no-store JSON:

```json
{"ok":true,"version":"1:token-1-2","bounds":{"x":10,"y":10,"width":190,"height":180}}
```

`bounds` is null for hidden/open pixels, fully hidden maps, invalid/out-of-map positions, or no eligible revealed area at that point. Visible boundary pixels can snap only to a revealed open component; unrevealed open labels are rejected even in a dilated wall fringe. Bounds cover the selected component's currently visible, wall-expanded mask. Responses contain no wall segments, component IDs, hidden room bounds or source artwork.

The endpoint checks active-map identity/version before and after its background framing computation, and rechecks campaign-view permission. A stale version/map change returns the existing 400 error path; blank maps return the existing not-found path. Normal authentication/forbidden behavior is retained. The client discards stale/out-of-order responses and refreshes state after stale/rejected lookups. This GET never adds fog operations, changes locks, checkpoints or versions, or broadcasts a map mutation. Existing state/image/WebSocket response shapes are unchanged.


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


## Revealed-area change metadata

Authorized `GET /api/c/{campaign_id}/state` map payloads add `revealed_area_signatures`, a sorted array of opaque SHA-256 strings for currently revealed components only. Hidden/empty maps produce an empty array (or existing map:null when blanked). No numeric component labels, hidden-area signatures, room count for hidden geometry, wall coordinates or additional bounds are exposed.

Signatures depend on each visible component's source/work dimensions, location and binary footprint, not on its numeric label, fog operation ID, wall/fog version, arrow preferences/colors or lock kind. They stay stable across cache invalidation/restart when raster geometry is unchanged. This field is snapshot metadata, not a persistent reveal-event log. Existing version/image/area-bounds and remote camera command protocols remain unchanged.

The viewer compares the newly displayed map's signatures to the previously displayed set. A new member clears room focus and uses current `revealed_bounds` for overview. Subsets/reordering/unchanged sets do not trigger a new-area reset. Missing metadata is tolerated for compatibility and retains previous focus behavior. No mutation endpoint or database change is added; normal campaign-view authorization still applies.

## Authored passage schema

Wall editor save/draft-export rows may have a seventh object:

```json
[200,70,200,130,"portal",true,{"pair":"p1","end":"a","sides":[{"role":"none"},{"role":"entry","kind":"secret","after":"locked_door","exit":0}]}]
```

The other element must have the same pair and end b; its side 0 must be Exit/Both.
Each pair has exactly two elements. Exit is always the 0/1 side index on the other
element: same-element/self routes cannot be encoded. Entry kinds are door,
locked_door, unlocked_door or secret; after is door/locked_door/unlocked_door.
Exit/None objects contain only role. Every Exit requires incoming routing, shared
Exits are valid, and at most one None is permitted per element. Invalid graphs
reject the entire save/export. Normal rows remain six fields; a secret door may
append `{"after":"locked_door"}`. Omission defaults to ordinary Door after discovery.

Admin map payload door_arrows add side, portal, exit_only and secret_origin;
portal_styles contains effective per-side appearance. No destination coordinates
are sent. These fields never enter viewer state. `portal` is accepted by wall-type
boundary settings. Looking Glass UVTT v2 round-trips the seventh field; v1 remains
supported. Downloaded/stored sources use authored configuration, never runtime.
Standard fallback represents portal elements as wall boundaries and loses routing.

Viewer default port is 5100; the older heading mentioning 6000 is superseded.

## Portal compass labels and selectable None targets

Portal authoring uses compass names with map-top North, not visible side numbers.
This is presentation only: saved side/destination indices remain 0/1 and the API,
UVTT extension version and schema do not change. Choosing Unconfigured/None as an
Exit target converts it to Exit in the local popup, committed atomically with the
route on Apply. Existing Both targets preserve their Entry role; Entry-only targets
are rejected. Server complete-graph validation and all permissions remain unchanged.
See Passages.md.

## Admin-only visible portal route associations

The existing authorized admin map payload additionally returns portal_routes:

```json
{"id":"8:0>10:1","state":"locked_door","entry":{"wall_id":8,"section":3,"side":0,"compass":"E","polygon":[[1,2],[3,2],[2,4]]},"exit":{"wall_id":10,"section":5,"side":1,"compass":"W","polygon":[[8,2],[10,2],[9,4]]}}
```

This is presentation metadata, one item per actual visible Entry with a displayed
paired Exit polygon. Polygons use the existing work-pixel coordinate space.
section is the 1-based position in the current map wall list, matching editor
labels; wall_id and side identify the actual endpoint. state is the effective
Entry kind. Shared Exits can occur in multiple route items. Both can supply an
existing double-headed arrow polygon instead of an Exit-only hint. No guessed
or client-selected target point is supplied.

This field is produced only by the manage-authorized admin map payload. It is not
added to viewer state, image responses or websocket messages. Viewer rendering,
permissions, CSRF and all mutation endpoints are unchanged. Dwell/pause preferences
are browser-local, not an API or database setting. No migration is introduced.
See [testing](testing.md) for validation guidance and environment requirements.


## Viewer arrow category exceptions

`POST /api/maps/{map_id}/door-arrows` accepts two additional optional strict booleans:
`viewer_portal_enabled` and `viewer_secret_enabled`. Omitted/null fields preserve current values.
The admin map payload returns `viewer_portal_arrows_enabled` and `viewer_secret_arrows_enabled`.
Existing `enabled`, `admin_enabled`, `viewer_enabled` and color fields retain their meanings.
These settings require the existing map-management authorization and CSRF protection.
Actual changes bump the fog version and send the existing `appearance` notification.
No fog operations or passage runtime state are modified. Currently secret entries never render for viewers.


## Cross-map passage API (admin portal only)

All paths below are under `/api`. Reads require authenticated campaign-management
permission, not just campaign viewing. Writes additionally require the existing
`X-CSRF-Token`. All writes serialize with BEGIN IMMEDIATE. Unknown body fields are
rejected; boolean flags are strict booleans. Service validation/stale state is a
400 BadRequest; permission/CSRF failures use existing 401/403 behavior, and invalid
request schemas use FastAPI's 422 response. These routes do not exist on the viewer
application (404).

| Method | Path | Purpose |
|---|---|---|
| GET | `/campaigns/{cid}/transitions` | Admin-only endpoints and campaign maps/settings |
| POST | `/campaigns/{cid}/transitions` | Create endpoint |
| POST | `/campaigns/{cid}/transitions/{id}` | Update full authored record, with revision |
| DELETE | `/campaigns/{cid}/transitions/{id}?revision=N` | Delete with stale check |
| POST | `/campaigns/{cid}/transitions/{id}/runtime` | Set/clear session overrides |
| GET | `/campaigns/{cid}/transitions/{id}/preview` | Read-only saved arrival preflight |
| POST | `/campaigns/{cid}/travel` | Atomic reveal/checkpoint/switch |
| POST | `/maps/{mid}/transitions/reset` | Clear this map's endpoint runtime overrides |
| POST | `/maps/{mid}/transition-markers` | Save viewer marker/label booleans |

Create/update body:

```json
{
  "map_id": 12, "name": "West stairs", "player_label": "Up",
  "kind": "stairs", "x": 100, "y": 120,
  "visibility": "discovered", "availability": "usable",
  "destination_id": null, "arrival": "area", "notes": "DM-only notes",
  "revision": null, "return_link": false
}
```

Required: map_id, name, x, y. Other fields use the illustrated defaults except
player_label/notes (empty). Name/label max 120 chars; notes max 2000. Coordinates
must be finite and inside the referenced image. Update requires the current revision
and immutable map_id. It replaces authored configuration, rather than applying a
partial patch. `destination_id` is an endpoint UUID, not a map ID; null unlinks it.
`return_link` creates an explicit reverse link without overwriting an existing
outgoing destination. Kind: stairs/ladder/hole/portal/climb/custom; visibility:
secret/discovered/admin; availability: usable/blocked/approval; arrival: area/preserve.

Runtime body: `{"revision": 1, "visibility": "discovered", "availability": null}`.
Both override fields are replaced on each runtime request; omitted/null clears the
corresponding override. Null means inherit authored value. Reset uses an empty body.
Marker body: `{"enabled": true, "labels": true}`; both fields are required.

Configuration mutations return the same listing shape as GET: ok, active_map_id,
endpoints, maps. Endpoint listing fields include current_visibility,
current_availability, broken and admin-only destination metadata. Never forward this
payload to players. Endpoint edits preserve runtime overrides.

Preview response includes source_revision, destination_revision, destination_id,
destination_map_id/name, destination_name, destination_version (three-element array),
arrival, source_state/visibility, needs_override, fraction and warning. For preserve,
fraction=0 and warning=false. Area fraction is the full component, not the incremental
reveal. Preview does not change fog or active map.

```json
{
  "source_endpoint_id": "SOURCE_UUID", "expected_active_map_id": 12,
  "source_revision": 3, "destination_revision": 2,
  "destination_version": ["DESTINATION_CACHE_TOKEN", 4, 9],
  "request_id": "unique-client-travel-request",
  "override": false, "allow_large_reveal": false
}
```

Populate revision/version fields from a fresh preview, and expected_active_map_id
from the listing. The source must be the active map. Use a new request_id for a new
trip; retry exactly the same payload after a transport failure. A successful retry
never reapplies the trip. Success returns `{ok:true,active_map_id:N,admin_url:"/maps/N"}`.
Explicit override is required for a source that is secret, blocked or approval-only;
it does not modify that state. Destination visibility/availability is not an arrival
gate. A large/leaking arrival requires allow_large_reveal=true as a separate consent.
An endpoint on a wall cannot use area reveal. No small-zone/radius arrival policy
exists in this version.


### Destination display availability

The existing admin `GET /api/maps/{map_id}/display-options` response now adds
`has_current_reveals`, a boolean evaluated from live fog operations. Existing
`can_restore` retains its meaning: effective active-map operations or, for an
inactive map, its saved checkpoint. Inspect destination does not consume these flags or show a reveal-choice prompt;
it uses authorized reads and admin navigation only. Existing display-option callers
retain their default behavior.
The existing CSRF-protected `POST /api/campaigns/{campaign_id}/active` performs
activation with map_id and fog_action (restore/reset); the endpoint, permissions
and response contract are unchanged. A cancelled choice issues no mutation request.
No new passage-travel operation or schema migration is introduced by this UI change.


### Passage save identity and independent scopes

Successful `POST /api/campaigns/{cid}/transitions` and
`POST /api/campaigns/{cid}/transitions/{id}` responses now include
`saved_endpoint_id` alongside the existing listing fields. It identifies the saved
endpoint, especially on create when several admins might add endpoints concurrently.
This is an additive response field; the request schema is unchanged.

The configuration request replaces authored configuration and preserves runtime
overrides. The runtime request replaces its two override fields only and preserves
configuration. Null/omitted override fields inherit authored settings. Clients must
use the returned endpoint revision for subsequent writes in either scope. UI dirty
tracking does not change server permissions, CSRF or stale-write validation.


### Modal-action clarification (no API changes)

The single portal Close/discard confirmation and Reset pairing confirmation are
client-side popup/draft operations. Back to passage and Escape from travel send no
mutation request. Entering travel preflight no longer replaces the source editor's
saved revision/baselines: cancelling cannot silently acknowledge another tab's
configuration changes. A later save still undergoes the existing stale-write check.
Travel and active-map request schemas, action values (restore/reset/cancel) and
backend effects are unchanged; only user-facing labels and return behavior change.

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

## Imported-name availability

Library list/import response entries now include `assigned: boolean` alongside
id/name/markdown. All entries remain present in the API; the editor filters out
assigned ones. The flag matches saved room_notes names in the same map using
Python strip().casefold(), including the current room, manual assignments and
preserved inactive geometry records. It does not inspect note content or reserve
drafts. Clearing/renaming a saved name changes availability on the next fetch.
No schema, route or permission changes; existing saves are not uniqueness-locked.

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

## Named / unnamed area overview API

GET /api/maps/{map_id}/room-name-overlay requires admin map-management access.
It returns `{ok,png,named,unnamed}` with a base64 RGBA PNG at fog work resolution
and named/unnamed current area counts. Response has Cache-Control: no-store.
It is read-only and does not update versions, checkpoints, notes or fog operations.
Only nonblank saved names with a valid current area_key/anchor make an area green;
other open areas are red, walls transparent. No viewer route is registered.

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

## Campaign backup and restore form routes

These are admin-portal form routes, not JSON API routes. Both require an authenticated
campaign manager (owning admin or superadmin) and valid CSRF token, supplied as
`csrf_token` or `X-CSRF-Token`.

| Method / route | Form fields | Success |
|---|---|---|
| `POST /campaigns/{campaign_id}/backup` | `csrf_token` | ZIP attachment, `application/zip`, `Cache-Control: no-store` |
| `POST /campaigns/{campaign_id}/restore` | multipart `backup` ZIP, `confirm` current campaign name, `csrf_token` | 303 redirect to campaign with `ok` message |

Backup uses filename `campaign-{campaign_id}-backup.zip`. Restore replaces campaign
content but preserves target ownership and viewer assignments. Validation failures
redirect with `err`; missing/invalid CSRF is forbidden. Oversized uploads use the
existing upload error handler. Missing or inaccessible campaigns use existing access checks.
The archive includes `campaign.json` (format `looking-glass-campaign`, version 1,
current schema version, campaign details and allowlisted table rows) plus `images/{id}.png`.
Raw wall source BLOBs use base64. No accounts, sessions or SQL are accepted from archives.
