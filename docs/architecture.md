# Architecture

## Process model

`python/main.py` → `looking_glass.cli` → `looking_glass.server.serve()` runs
**two uvicorn servers in a single asyncio event loop**:

```
                 ┌──────────── one Python process ────────────┐
 DM browser ───► │ :5000  admin FastAPI app  ─┐               │
                 │                            ├─ AppContext ──┼─► SQLite (data/looking_glass.db)
 Player screen ─►│ :5100  viewer FastAPI app ─┘  (db, fog,     │   map images (data/maps/)
       ▲         │                               hub, settings)│   render cache (data/cache/)
       └── WS ───┤ EventHub: admin action → viewer WebSockets  │
                 └─────────────────────────────────────────────┘
```

Both apps share one `AppContext`, so an admin action can push a `refresh`
event to connected viewer WebSockets directly, with no broker. Signal handling
is centralised so Ctrl+C / SIGTERM stops both servers cleanly.

## Package layout (`python/looking_glass/`)

| Module | Responsibility |
|---|---|
| `config.py` | Defaults, then `config.yaml`, then env vars (`LG_ADMIN_PORT`, `LG_VIEWER_PORT`, `LG_HOST`, `LG_DATA_DIR`, `LG_CONFIG`) |
| `db.py` | SQLite connection helper (connection per unit of work, WAL) + ordered migrations |
| `rbac.py` | Roles and **every** permission decision |
| `security.py` | scrypt password hashing, session tokens, login throttle |
| `bootstrap.py` | Creates the first superadmin |
| `cli.py`, `server.py`, `__main__.py` | Entry points |
| `repositories/` | All SQL: `users`, `sessions`, `campaigns`, `maps`, `walls`, `fog_ops` |
| `services/wall_model.py` | Dataclasses: `WallSegment`, `Calibration`, `FogOp`, `WallSet` |
| `services/foundry_import.py` | Foundry / UVTT parsers → `WallSet` |
| `services/fog.py` | Area detection, fog masks, viewer image compositing (storage-agnostic) |
| `services/images.py` | Image validation and storage |
| `services/events.py` | In-process WebSocket pub/sub |
| `web/context.py` | `AppContext` shared by both apps |
| `web/app_factory.py` | Builds the admin and viewer apps |
| `web/deps.py` | Auth dependencies (session cookie per portal, CSRF) |
| `web/access.py` | Load-and-authorise helpers (`campaign_for_manage`, `campaign_for_view`, …) |
| `web/auth_routes.py` | Login / logout / account (mounted on both ports) |
| `web/admin/*` | Admin pages, form posts, users, JSON API for the fog editor |
| `web/viewer/*` | Campaign picker, display page, state/image API, WebSocket |

Dependencies point one way: `web → services/repositories → db/rbac`. Services
take plain data (no DB, no FastAPI), so they are easy to test and reuse.

## How area reveal works

1. Wall segments are stored **raw** (Foundry scene coordinates). A per-map
   calibration maps them onto the image: `image = (wall − offset) × scale`.
   On import the calibration comes from the scene (padding, background offset
   and image size versus scene size). You can fine-tune it in the editor.
2. `FogEngine.build_area_map` draws the blocking walls as thick lines on a
   "work" bitmap (≤ `fog.work_max_dim` px). It then labels the open pixels into
   4-connected components with `scipy.ndimage.label`. Each component is one
   area enclosed by walls. Doors block by default (toggle per map). Ethereal
   walls never block.
3. A click stores only a **fog operation** (`reveal`/`hide` + point,
   `reveal_all`, `hide_all`) in `fog_ops`. Replaying the ops gives the set of
   revealed labels. That makes undo trivial, and the fog stays correct after
   walls are re-aligned.
4. The revealed mask is dilated by the wall thickness, so the walls around a
   revealed room are visible too. It is then upscaled, feathered and composited
   over the (downscaled) map. The result is cached as
   `data/cache/viewer_<map>_<walls_v>_<fog_v>.webp`.
5. Viewers fetch `/api/c/<id>/state`, then the versioned image URL. Every fog
   change bumps `maps.fog_version` and pushes `{"type":"refresh"}` over the
   WebSocket.

Caches: area labels per `(map, walls_version)` and masks per `(map,
fog_version)` live in in-memory LRU caches. Composite images live on disk.
The heavy work runs in `asyncio.to_thread` behind per-map locks.

## Templates

Jinja2 uses a `ChoiceLoader` with `web_html/` first, then `templates/`.
Page templates (`web_html/admin/*.html`, `web_html/viewer/*.html`) extend
`templates/base.html` and include partials from `templates/partials/`.

## Database schema (v1)

`users`, `sessions` (hashed tokens, per entry point, CSRF token),
`campaigns` (owner, active map), `campaign_viewers`, `maps` (image,
calibration, `doors_block`, `walls_version`, `fog_version`), `walls`,
`fog_ops`. Migrations are append-only in `db.MIGRATIONS`.

## Reusable wall source library (schema v2)

Migration 2 appends `wall_sources` without changing migration 1. Each row stores
an immutable upload (`raw` BLOB), display filename, SHA-256, parsed non-empty
scene count, and creation time. `campaign_id` is a cascading foreign key;
`UNIQUE(campaign_id, sha256)` deduplicates identical bytes only within a campaign.
IDs use AUTOINCREMENT to avoid reusing a deleted source's ID in stale clients.

`repositories/wall_sources.py` owns source SQL. `web/admin/wall_sources.py`
registers routes on the existing admin API router; campaign/map access helpers
are called before exposing metadata or looking up sources. Writes use the same
CSRF dependency as the existing map API. Source queries always include the
campaign ID; a manager cannot import a source from another campaign even when
able to manage both campaigns. Viewer routes and static asset permissions do
not grant access to source BLOBs.

The editor's `wall_source_library.js` manages independent source and scene
selectors. It clears old options on source changes, disables controls during
requests, requires an explicit wall-set choice, and inserts uploaded names as
text rather than HTML. Applying uses the existing `apply_walls` service path,
then notifies viewers and reloads the editor. Each target receives independent
wall rows and calibration; maps do not hold a live reference to a source.
Deleting the upload therefore cannot remove already-applied walls.

Saving and inspection parse outside an active DB transaction using
`asyncio.to_thread`. Application reuses the existing synchronous import path
inside its transaction. Source bytes are never replaced in place, keeping scene
indices stable for the selected source. No new third-party dependency or
configuration key is introduced. Existing one-off imports remain compatible.

Back up the application database along with map images. Source uploads increase
DB size; deleting rows frees reusable pages but does not necessarily shrink the
SQLite file. There is a per-file upload limit, not a total library quota.

## Map incarnation identity and display checkpoints (schema v3)

Migration 3 appends `maps.cache_token`, backfills existing maps with random
128-bit tokens, and installs an insert trigger for future maps. Numeric map IDs
may still be reused; cache identities cannot rely on those IDs alone.

`map_fog_snapshots` stores the ordered operation list last displayed for each
map, with an ON DELETE CASCADE foreign key. Existing operation lists are seeded
on upgrade. `services/map_display.py` coordinates checkpoint/restore/reset and
activation inside the caller's database transaction. Live fog operations refresh
the active map's checkpoint; inactive edits do not overwrite it. Restore replays
coordinates against current walls, not a historical wall geometry snapshot.

Fog-engine memory and disk keys include map incarnation/image identity, relevant
geometry and renderer configuration. Mask keys include both walls and fog
versions. Legacy filenames are never read by the new renderer. Invalidation is
serialised with render locks. Viewer URLs include the incarnation token; image
responses are not browser-cacheable. Viewer refresh requests use generation IDs
so an older asynchronous decode cannot overwrite newer display state or undo a
blank-screen update.


## Shared clickable door arrows

`services/door_arrows.py` shares midpoint/normal sampling, polygons, raster
rendering and server hit validation. Ordinary doors require distinct adjacent
labels with one revealed side. Secret-origin doors keep arrows after both sides
are revealed. Portal Entries resolve to the configured side of the paired element,
using verified open pixels, never a client-provided destination. Exit hints are
noninteractive, admin-only and may be drawn outside revealed areas.

The `MapSpec.arrow_audience` discriminator separates admin and viewer cache
identity. Viewer composition excludes undiscovered secrets and Exit-only hints;
locked/unlocked hints use ordinary appearance. The viewer API still contains no
wall graph, hidden routing coordinates or mutation endpoint.

## Locked and unlocked doors

Migration 8 and its existing runtime door table remain intact. Migration 10 adds
`walls.passage` JSON and `passage_runtime_states(wall_id, side, kind)` with a
cascading wall foreign key. Side -1 stores shared secret-door state; sides 0/1
store independent portal Entry overrides. Authored secrets use `kind=secret` and
an optional `after` property; authored portal elements use `kind=portal` with pair,
end and two side definitions. Exact pair/route validation precedes replacement.

Repository `designed=True` reads omit runtime overrides for authoring/export.
Effective reads merge temporary kinds and retain designed_kind for boundary
filtering. Runtime changes bump wall/fog versions without changing topology or
fog history. Reset clears both runtime tables; fog hide_all triggers cover toolbar
Reset and explicit reset helpers cover map activation. Row replacement cascades
state deletion. Normal reveals use existing fog history/checkpoint/notifications.

`door_actions.perform` requires a current incarnation/version stamp and actual
raster hit. Double-click state changes require an arrow. Entry side IDs are checked
against server-resolved geometry, so the browser cannot choose another Entry.
The legacy arrow-reveal endpoint rejects locked and undiscovered-secret arrows.
Already revealed destinations are no-ops. Portal metadata is authored-only in
UVTT; runtime states never enter reusable sources.

## Independent arrow visibility

Migration 9 adds `maps.viewer_door_arrows_enabled INTEGER NOT NULL DEFAULT 1 CHECK (... IN (0,1))`, then initializes it from existing `door_arrows_enabled`. The existing column becomes the admin flag; migration history 1-8 is unchanged. New maps default both on. Existing map preferences, colors, lock states and fog history remain intact.

`arrow_visibility.resolve_visibility` merges legacy shared and explicit per-screen partial updates with strict boolean handling. Management payload exposes both explicit aliases; the UI sends only the changed screen's field. Admin images and action hit geometry continue using `door_arrows_enabled`.

`MapSpec` includes viewer visibility in render identity. `viewer_image` uses a dataclass copy whose overlay flag is derived from the viewer preference; the caller's admin spec is never mutated. Its normalized viewer cache identity is independent of admin-only visibility. Old manually constructed specs without a viewer flag retain the former shared behavior; database specs always have the explicit viewer flag after migration.

Admin state/mask keys now include admin visibility, and polling compares both visibility fields. This permits admin-only updates without bumping fog version (and therefore without refreshing/recentering viewers). Viewer visibility/color changes still use the existing version/notification pipeline. Both color pickers remain usable while either display is enabled. Viewer JS/templates/API, wall rendering and lock-action code remain unchanged.


## Read-only viewer room zoom

`services/viewer_area.revealed_area_bounds` maps a displayed source-image point to the work mask using actual dimensions (including ceil-rounding). It requires currently visible mask pixels and a currently revealed component label, permits boundary snapping only to revealed labels, expands that component by the existing wall thickness, intersects it with the current revealed mask and returns its source-space bounding box. Hidden labels never produce bounds. Computation runs in a worker thread; only a bounding box for the clicked revealed region is returned.

The authorized read-only viewer endpoint binds requests to the active map's existing version, reads one database snapshot and checks the current map/version/permission again after computation. No schema or fog/lock mutation is introduced. The client continues to receive server-composited imagery, not raw maps or wall topology.

`viewer_area_zoom.js` provides pure source-to-viewer-image fitting, pose comparison (1 screen-pixel position tolerance and small relative scale tolerance) and filtered double-tap pairing. Fitting uses the same 90% viewport margin and existing PanZoom scale limits. `viewer_display.js` receives stationary tap coordinates from PanZoom, resolves a double tap via the read-only endpoint, and compares the actual camera with the returned room pose. Matching poses toggle to the existing all-revealed overview; nonmatching poses fit the selected room.

Request generations, displayed versions and visibility checks prevent late results from affecting newer navigation, switched/blanked maps or refreshed images. After live image updates, newly visible component signatures clear focus and return to overview. Without new areas, focus is revalidated and cleared if hidden. Viewer resize is owned by the display code, replacing that instance's unconditional PanZoom resize fit so it can refit a focused room. Fit/F clears focus and restores overview. Wheel/drag clears focus tracking; admin PanZoom code is untouched.

No Center/Fit admin preferences, arrow visibility changes, lock changes, migrations or new dependencies are part of this feature. Camera changes are tab-local; the new endpoint has no viewer write permission.


## Admin-origin viewer camera commands

`admin_area_taps.js` provides a separate 400-ms/12-screen-pixel delayed-single/double recognizer. The admin tap wrapper first checks existing arrow/managed-door targets and secondary clicks, delegating them unchanged. Only ordinary primary area taps enter the new queue. Singles invoke the original fog handler after version/mode checks; doubles POST a versioned source coordinate to the admin camera endpoint without invoking any fog handler. Pending area work is cancelled by state changes, mutations, camera transforms and navigation gestures.

`admin/viewer_zoom.py` is mounted only on the admin app. The management/CSRF endpoint uses the existing revealed-area service for eligibility, checks current map/version/authorization before and after lookup and publishes a scoped point-only command through the existing EventHub. There is no storage write or schema change. The shared hub distributes the event to this campaign's currently connected viewer sockets; existing session revocation handling remains in force.

The viewer adds only a remote-command receiver around its existing local lookup/toggle path. Recent IDs are deduplicated in a bounded set of 64; a newer command supersedes older pending commands. The displayed version must match after any refresh, and a newer local interaction invalidates pending remote work. Each viewer then performs the unchanged authorized area-bounds lookup, with its existing out-of-order response guards, actual-pose comparison, focus/overview and resize/live-update behavior. This deliberately preserves the exact local lookup and onTap function bodies.

Admin camera transforms, fog/door/rendering services, arrow settings, viewer read-only permissions and schema are unchanged by camera commands. Multiple viewers evaluate the toggle independently against their own actual poses. Commands are ephemeral: no acknowledgment/replay/persistent camera state or external messaging broker is added.


## Newly revealed area -> viewer overview

`services/revealed_regions.py` fingerprints only current revealed components, using a cropped binary footprint plus source/work dimensions and location. Numeric label IDs and hidden components are never included in the response. `AreaMap` stores private component slices and digest caches; they share the geometry cache lifetime and are protected by the map's existing reentrant lock. These are in-memory caches only. Digesting the footprint rather than versions avoids false resets for style/visibility/runtime lock changes and tolerates stable components whose numeric labels are renumbered.

The viewer state handler reads map/fog inputs in one database snapshot and adds the signatures beside existing bounds/version data. On a successful image decode, `LGViewerHasNewAreas` compares set membership against the last displayed map. Any new signature on the same map causes `cancelLookup(true)`, clearing focus and invalidating old asynchronous area lookups before fitting the overview. The comparison occurs after the existing refresh-generation guard and before replacing currentMap, so late frames cannot overwrite/reset a newer one incorrectly.

Without new visible members, existing focus validation continues. This handles hidden-area additions inside unchanged overview bounds, hide/reveal exchanges with equal area counts, repeated reveals, hide-only updates, Reveal all and Undo. Actual topology edits can change component fingerprints and conservatively reset focus. Stable lock/unlock does not alter topology. New explicit remote/local camera commands issued after a reveal can focus again; commands/lookups bound to older map versions cannot restore old focus.

No schema migration, new dependency/configuration, extra camera preference or Center/Fit control is introduced. Admin gestures, remote zoom delivery, arrow behavior and viewer read-only permissions are unchanged. Fingerprints describe displayed snapshots; transient reveal/hide states coalesced before display are not replayed as camera events.

## Passage UI and interchange

`static/js/portal_editor.js` provides a separate modal, using atomic batch draft
changes in admin_wall_editor.js. Existing coordinate edits preserve metadata;
paired elements cannot be independently removed/retyped. Side labels correspond
to the directed segment normal. Both editor and fog overlays use per-side strokes
for portal type colors. `WallSegment` adds comparison-excluded keyword-only
passage/runtime dictionaries; positional six-field constructors remain valid.
Rows have an optional seventh authored-config object. UVTT extension v2 is emitted
when passage metadata is present; v1 ordinary sets remain readable/emittable.
Core fallback exports portals as opaque wall segments, not falsely linked doors.
The existing geometry checksum protects core/extension coordinate consistency.

## Portal presentation tools

services/portal_presentation.py joins already generated admin arrow polygons to
their authored opposite-element Exit references. It emits admin-only route IDs,
side/section/compass labels, effective Entry state and existing endpoint polygons.
It neither renders new server hints nor changes cache identity, fog topology,
hit resolution, runtime state or viewer payloads. Disabled/fogged sources have no
arrow object and hence no route item. Actual Exit geometry is required; shared
and Both endpoints are matched by wall ID and side.

static/js/floating_dialog.js moves native dialogs with captured pointer events or
keyboard arrows and clamps their positions on resize. portal_overview.js derives
a read-only grid from authored rows and optional popup links, using safe textContent
cells. portal_editor.js supplies pending versus current-draft snapshots.

portal_cycle.js separates a testable clock-driven Cycle from DOM rendering. The
admin editor holds it inactive until the matching raster arrow image has decoded;
new versions clear old highlights. The SVG overlay shares work coordinates and is
masked by the exact admin arrow alpha, with pointer-events:none. Viewport filtering,
busy/visibility changes, pause and page lifecycle events stop/restart the single
owned timer. Dwell is 1–15 s (default 5), pulse period one second. Reduced motion
uses steady polygons. Preferences are localStorage scoped by map, with validated
fallback defaults and graceful failure if storage is blocked. No schema migration
or new viewer capability is introduced.


## Viewer arrow category filtering

Schema migration 11 adds `maps.viewer_portal_arrows_enabled` and
`maps.viewer_secret_arrows_enabled` as checked boolean integers, default zero.
MapSpec loads both with backward-compatible defaults and includes them in cache identity.
The viewer compositor retains the main viewer flag as the primary visibility switch.
When that switch is off, door_arrows.arrows permits generation for category exceptions,
then filters entries by portal/secret-origin union. Current-secret checks and admin-only
exit-hint restrictions precede filtering. Admin rendering and validated hit testing remain
controlled only by the admin switch. API updates preserve omitted fields, invalidate via
fog-version changes, and notify connected viewers through the appearance event.


## Cross-map endpoints and atomic travel (schema 12)

`services/map_transitions.py` owns endpoint validation, authored/runtime state,
arrival preflight, travel and viewer-marker drawing. Endpoints have stable UUID-text
IDs and a map foreign key; their optional outgoing destination references another
endpoint. The service rejects same-map/cross-campaign destinations and coordinates
outside the image. SQL triggers additionally reject cross-campaign links.

`map_transitions` stores authored name/label/type/coordinates/visibility/availability,
arrival policy, private notes, runtime overrides, destination, link_defined and
revision. NULL runtime fields inherit authored values. Deleting a destination sets
its reference NULL while link_defined retains the broken-link distinction. Foreign
keys cascade endpoint deletion with map deletion. Triggers bump map fog versions
on endpoint insert/update/delete and invalidate incoming endpoint revisions on delete.
Two checked map booleans persist viewer marker/label settings, both default on.

Admin routes are included in the existing `/api` router only, reuse campaign/map
management checks and CSRF dependencies, and serialize writes with BEGIN IMMEDIATE.
Travel validates authorization before looking up replay records. Preflight returns
endpoint revisions and destination [cache_token,walls_version,fog_version]; travel
recomputes these in its write transaction. It checks active source and explicit DM
approval/warning acceptance before writing. It checkpoints source fog, optionally
adds one destination reveal, bumps destination fog version, checkpoints destination,
sets the shared active map and records the result in one transaction. It does not
call restore/reset activation: that could overwrite the destination's current fog.
Viewers are notified after commit using the existing active-map refresh event.

`map_transition_travel` has a composite (campaign,user,request_id) primary key and
stores canonical request/result JSON. An identical retry returns the stored result;
a mismatched payload for a reused ID is rejected. Records live until their campaign
or user is deleted; there is no automatic pruning. A replay returns the original
result, not a new navigation instruction applied to the current campaign state.

`web/access.fog_inputs` attaches only (x,y,type,player_label) tuples for discovered
endpoints to MapSpec. Its identity includes markers and marker/label flags, avoiding
stale viewer/preview images. The server compositor checks the endpoint's open-region
label against revealed labels, draws a letter badge and optional label, then clips
all marker pixels to the revealed mask. Private endpoint configuration is not added
to the viewer state API. Raw maps/walls remain admin-only. The existing viewer image
preload/generation guard handles swaps; no new viewer navigation or raw-image path
is introduced. The exact player-image preview includes the same markers.

`map_transitions.js` mounts the editor panel and dialogs; original fog gestures defer
to endpoint selection/placement first. Both overlays use original image coordinates.
The endpoint list refreshes on focus/15-second polling when no dialog or placement is
active. The campaign overview is read-only except for links back to map editors.


### Passage footer, destination activation and fog-editor accordion

The endpoint dialog has a flex-column form with one overflow body and one
non-scrolling actions footer. Closed dialogs retain native display semantics.
The sidebar's peer details share a name for native exclusive opening, with a
small toggle-listener fallback. Legend and nested Alignment are outside the group;
the legend is never programmatically forced open after manual closure.

Destination-open freshly resolves the saved source revision/link and destination
from the authorized endpoint listing. It reserves an opener-detached blank admin
tab synchronously, invokes LGChooseFog with includeCurrentReveals, then calls the
existing active-map API only after a restore/reset decision. It closes the reserved
tab on cancellation/error and uses current-tab navigation if a popup is blocked.
The additive has_current_reveals display-options field leaves default restore
callers unchanged. Existing post-commit viewer refresh handles viewer activation.
This is intentionally separate from travel/preflight and does not execute an
arrival reveal or change endpoint runtime state.
