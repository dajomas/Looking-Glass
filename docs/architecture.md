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

Inspect destination refreshes and validates the saved source revision/link and
opens an admin-only destination tab. It never calls reveal-choice, active-map, fog,
runtime or travel APIs. Popup-blocked fallback asks before discarding pending edits
and navigates only the admin tab. Existing optional display-options/prompt fields
remain compatible but inspection no longer consumes them.

### Independent passage save scopes

The client stores separate canonical baselines for configuration and session
selections, ignoring the endpoint revision when comparing configuration dirtiness.
Configuration saves return the additive saved_endpoint_id in the existing listing
response, identifying new records without guessing from concurrent additions.
After acknowledgement, the client updates current identity/revision and only the
saved group's fields/baseline; the opposite group's draft/baseline stays intact.
Configuration uses server-normalized values and clears its one-shot return-link
selection. Runtime updates do not repopulate authored fields. Controls are disabled
during writes and re-enabled with current saved-record action availability.

Both saves stay open. Input/change events update independent live status indicators.
Close/Escape and navigation guard pending edits, while Travel warns that it uses
saved values. Successful writes are acknowledged before a subsequent map refresh;
a refresh error does not masquerade as an uncommitted write. Service authorization,
CSRF, serialized writes and stale-revision validation are unchanged.


### Portal Close and travel-return checkpoints

Portal configuration records a canonical snapshot of its local rows and sorted
route selections after opening and each successful Apply. Close/Escape compares
against that checkpoint, asking only when unapplied changes exist. The duplicate
Cancel handler/button is removed. Reset pairing confirms the affected sections
before changing popup state; no server mutation is added.

Travel confirmation stores source form scroll/focus without calling open(item) or
repopulating fields on return. Back/Escape restores the same DOM, dirty baselines
and saved revision, clears the cancelled preflight and uses a fresh preflight on
the next attempt. The listing used for travel preparation is held separately from
the source form's current saved record so previewing/cancelling cannot silently
rebase stale edits. In-flight request cancellation is blocked; server travel
transactions and idempotency are unchanged. Reset labels describe existing backend
effects rather than adding new reset behavior.

## Sidebar help presentation

`templates/partials/_admin_sidebar_help.html` contains the fog editor’s help copy
and native details/summary disclosures. `web_html/admin/map_editor.html` includes
it near the map selector. No help disclosure has an `open` or `name` attribute,
so all start closed and remain outside the control-panel accordion managed by
`sidebar_sections.js`. The five source-library help subsections nest inside the
Saved wall sources help topic. CSS is scoped to `#editor-help`.

The template hides the passage control wrapper for `siblings|length <= 1`, while
retaining DOM targets required by existing map-transition event bindings. The
passage help topic is conditionally omitted for single-map campaigns. No backend
behavior, schema or API changes are required.

## Room-note persistence and rendering

An appended SQLite migration creates room_notes with a cascading map foreign key,
a geometry key, selection anchor, name, Markdown and optimistic revision. No
existing migration is rewritten. The service hashes packed component membership
plus image/work dimensions and scale, caching keys in AreaMap.region_signatures.
This conservatively avoids assigning notes to the wrong room after relabeling.
Inactive records survive geometry edits and are discoverable in the admin list API.

Mistune renders escaped Markdown; Bleach applies an explicit HTML tag, attribute
and URL-protocol allowlist. Images and active HTML are not allowed. Only sanitized
server HTML is inserted into the preview; room names use textContent. The viewer
payload and viewer app do not include note content.

The standalone room_notes.js owns panel state, dirty protection and selection.
The editor refreshes named-room visibility on applied fog/wall state changes,
including managed-door reveals, undo and reveal-all. Explicit selection mode has
priority over map actions; outside it, existing delayed singles/doubles and door
hit-testing remain in place. Multiple newly revealed named rooms choose the first
alphabetically. Notes save without fog invalidation; other admins see updated
content when they reselect the room. There is no live collaborative note editor.

### Exclusive room-note read/edit modes

LGRoomNotes tracks editMode separately from the map's room-selection checkbox.
Read and form containers use mutually exclusive hidden states (enforced in scoped
CSS). Edit mode suppresses automatic room switching, including pristine drafts.
Save disables editing controls until completion and blocks selection while pending;
errors preserve the draft, successful saves and Cancel restore read mode.
The toolbar inserts Markdown source with textarea selection APIs and updates dirty
tracking. Clipboard paste prefers text/markdown over text/plain; rich HTML is never
inserted into the preview. Clipboard-read completion is guarded against changed
room, edit mode and draft state. Server rendering, sanitization, permissions,
revision checks, endpoints and database schema are unchanged by this UI follow-up.

## Imported room-note library

An appended migration creates imported_room_notes, cascade-owned by a map, with
name/Markdown, monotonic ID and SHA-256 content digest unique per map. Import
parses and validates first, then appends in one immediate SQLite transaction;
identical records are ignored, modified records append without altering prior
assignments. Neither importing nor saving notes changes fog.

room_note_import subclasses the existing Mistune block parser to record offsets
of document-level ATX and Setext headings. It slices normalized source between
headings at the globally smallest level, preserving lower headings and Markdown
source. Nested/container/code headings do not delimit records. UTF-8 BOM and CRLF
are accepted; invalid UTF-8, NULs and validation failures reject the complete file.
Preamble is deliberately omitted. Cross-section reference definitions are not
rewritten or copied. The library is loaded by the room UI on page initialization;
imports refresh it in-session. A generation counter prevents stale library loads
from replacing a newer import response. Picker assignment fills an unsaved draft
for every selected room, including rooms with existing metadata. Existing sanitization and
optimistic-save checks apply; library choices do not bypass those checks.

### Optional room names and reversible draft controls

An appended migration rebuilds room_notes with a relaxed name-length constraint
(0–200), copying geometry anchors, Markdown and revision unchanged. No imported
library rows are modified. Clearing saves empty strings in the existing row and
increments revision rather than deleting/recreating it; this preserves optimistic
concurrency against old clients. Payloads still use “Unnamed room” as a UI-only
placeholder for an empty name. Notes-only metadata is supported.

Clear name and notes changes the draft, not the server, and Cancel restores saved
content. Imported choices are allowed for all selected rooms in edit mode.
The upload section uses a native details/summary initialized closed on load and
an explicit closed-details CSS rule to defeat author .stack display rules.

## One-shot room-import action and actual draft comparison

keep_select_values.js used to persist room-import-select and restore it after a
MutationObserver saw the options being rebuilt. Restoration dispatched a synthetic
change event, which invoked the import handler again. Rendering edit mode rebuilt
the options again, creating a feedback loop; Cancel resetting the value could also
be replayed on later observed mutations. Automatic imports could dirty an otherwise
untouched room. The old sticky dirty flag additionally stayed true after undo.

room-import-select is now excluded from both capture persistence and restoration,
including previously stored values. The handler consumes the selected value before
rendering/confirm, ignores reentrant invocations, and treats identical draft content
as a no-op. Dirty state is derived from the active edit fields versus saved room
values and recomputed at destructive-action/navigation checks. Name trimming and
newline normalization match editor/server behavior; Markdown whitespace remains
significant. show() resets clean state. The shared restoration policy for ordinary
selects is unchanged. No API, database or fog changes are involved.

### Imported notes picker inside the editor

room-import-choice is now a child of room-form, before the name field. Its
visibility follows editMode rather than read mode, and the action handler refuses
imports outside editing. Form save enable/disable handling now includes select
controls. Selection stays a one-shot, non-restored action; genuine draft-difference
confirmation, reentrancy guards and Cancel semantics are unchanged.

## Automatic editor entry for unnamed rooms

After room-at lookup passes existing selection generation/dirty checks, select()
shows the saved room, then enters editing only when the selection is explicit,
the selection-mode checkbox is currently checked, and the returned room name is
blank after trimming. Notes content is not part of this condition. No saved data
is altered, no dirty flag is set, and no additional HTTP request is made. Name
focus is only applied if the panel body is expanded. The generic show() function
is unchanged so Save, Cancel and background updates cannot accidentally auto-edit.

## Imported names already assigned to rooms

room_note_import.list_entries adds assigned flags from all persisted room_notes
names in the same map (trimmed and casefolded). This recognizes assignments made
before the patch and manual matching names without introducing import-ID bindings
or a migration. All same-name import variants share availability. Preserved
inactive geometry records remain conservative reservations.

The editor filters flags for both rendering and action lookup. It refreshes the
library when entering edit mode, after successful saves and on import; the existing
load generation guard discards stale responses. A final render after re-enabling
save controls restores correct no-options/disabled state. Selection is still a
one-shot draft action excluded from dropdown remembering. This is not a uniqueness
constraint: simultaneous/manual duplicate saves remain possible as before.

## Admin-only room editing overlay

room_edit_marker.js requests a separate room-edit-overlay image using the selected
anchor and geometry key, then places it over the stage's real fog canvas. A solid
amber edge and translucent interior distinguish editing without writing fog_ops,
changing versions/checkpoints, modifying masks, or notifying players. A viewport
status label provides an explicit editing indication. Exiting edit mode clears
both immediately; request generations prevent late responses from restoring a
cancelled marker. Map geometry changes invalidate/refetch with the original key;
changed room shape is rejected rather than highlighting the wrong area. No edit
state is shared with other admins or viewers, and this is not a room-edit lock.

## Imported-note manager and guarded deletion

room_library_manager.js provides a native dialog, all-entry list, expanded Markdown
source details, assignment badges, Refresh and confirmed delete actions. Content
is placed via textContent, never unsanitized innerHTML. It uses the existing library
GET and a new DELETE route. Successful deletion replaces the owner's cached
library and rebuilds the assignment picker; errors refresh status without removing
protected entries. Request generations ignore results from closed dialogs.

The deletion service requires a caller-held IMMEDIATE transaction. The route holds
it across map permission, same-map entry lookup, current name-based assignment
validation and deletion, serializing against room-note saves. No schema change.
notes_match distinguishes exact source-note matches from assigned names with
modified notes; assignment protection still applies to both. Drafts do not reserve
entries. Simultaneous manual room assignment after deletion is still possible
because room notes are copied text rather than import-ID foreign keys.

## Room name coverage overlay

room_name_overlay.js owns a one-button name coverage overlay. It listens to the
selection-mode checkbox, shows its button only when checked, and clears/reset state
when unchecked. Template inserts it directly below the checkbox; those controls
remain accessible while editing. A separate stage image (z-index 2) paints green
and red below the amber room-edit marker (z-index 3), with a viewport text legend.
No map state is changed and pointer events pass through.

The GET service labels each current connected area using saved nonblank names
whose anchor resolves to the same geometry fingerprint. It builds a label palette
and renders one PNG, rather than hashing every unnamed area. Wall pixels are
transparent; empty/whitespace names and detached geometry records do not produce
false green regions. The client invalidates stale responses on hide, geometry
change and refresh. Successful note saves refresh enabled coverage; draft edits,
Cancel and import management do not change classification. Other sessions' note
changes are picked up by explicitly hiding/showing; no new polling loop is added.

## Imported library unassignment and dialog scrolling

The native imported-room dialog uses a flex column only while `[open]`, preserving
closed-dialog behavior. The header is nonshrinking; the list alone uses
`min-height:0; overflow-y:auto`. Modal height is bounded by viewport/dynamic viewport.

`room_library_manager.js` renders unassign controls for assigned entries and delete
controls for unassigned entries. Text continues to use textContent. Mutations are
confirmed, serialized, and guarded against stale async responses and unsaved drafts.
Successful unassignment updates library availability, re-fetches an affected selected
room, and refreshes the named/unnamed overlay without changing player state.

`room_note_import.unassign` matches the existing Python `strip().casefold()` name
policy and clears saved name/Markdown in place, incrementing revisions. The API
holds BEGIN IMMEDIATE around permission checks, geometry reconciliation and mutation.
Imported entries remain immutable; no migration, cache format or dependency change.

## Campaign backup and restore

`services/campaign_backup.py` implements versioned campaign-only ZIP serialization.
The campaign form router reuses `campaign_for_manage` and `CsrfUserDep` for all POST routes;
recovery GET downloads require authenticated campaign management permission.
Export reads campaign-scoped rows in one SQLite read transaction and adds map image files.
The database snapshot does not lock image files against concurrent replacements; avoid
editing the campaign during export or restore.

Restore uses a `BEGIN IMMEDIATE` database transaction. It checks format/schema, allowlisted
tables and exact columns, references, duplicate IDs, expanded size and image dimensions.
It never executes archive SQL or extracts archive paths. It generates fresh image paths,
map cache tokens and transition identities, and remaps map/wall foreign keys. Transition
links are populated after all endpoints exist. Fog operations precede runtime door state
restoration so hide-all triggers cannot erase restored runtime states.

The campaign row survives; name, description and active map are replaced and session_version
is incremented to invalidate stale restore previews, including on empty campaigns. Accounts,
ownership and viewer assignments are not imported. Travel replay records are cleared.
New image files are tracked for cleanup after rollback; old files are deleted after commit.
Existing fog caches are invalidated and a campaign refresh is broadcast after success.
Filesystem and SQLite are not one atomic resource: process termination or post-commit
cleanup failure may leave orphaned files. This does not replace a full data-directory backup.
No schema migration or new runtime dependency is introduced.

### Step 4 inspection and recovery

Inspection runs the real importer against a serialized private SQLite snapshot and a
TemporaryDirectory for imported images. The file-backed clone handles the source's WAL
mode and validates inserts, constraints, images and foreign keys without changing live
rows/files. Temporary files are removed on normal completion/failure; the snapshot contains
the full database, so protect the temporary filesystem and clear leftovers after crashes.

An HMAC-SHA256 token binds archive SHA-256, target portable rows plus campaign metadata,
user identity and issuance time. The signing key lives only in the application process;
previews expire at 900 seconds or restart. Tokens contain digests, not uploaded content.
This follows the supported single-process deployment; multi-process workers are unsupported.
The target digest detects database changes, not out-of-band modifications to image files.

Restore verifies the token inside BEGIN IMMEDIATE, repeats inspection, then exports the
current campaign using that same transaction. Recovery must itself pass inspection and
upload limits before it is written to data/recovery with an exclusive random filename,
mode 0600, file fsync and (on POSIX) directory fsync. Only then does replacement begin.
A failed restore may leave a valid recovery ZIP for manual download. No automatic pruning
occurs. Recovery is portable campaign content, not checkpoint history or instance state.
The live importer also rejects duplicate identities and unexpected/missing ZIP entries.

Inspection serializes the whole database and buffers archives, and restore validates both
the incoming archive and recovery snapshot. This trades extra memory, temporary disk and
latency for stronger preflight validation. Use trusted archives and idle campaigns. The
existing synchronous importer runs on the request path; large operations may delay other
requests. Filesystem and SQLite cannot commit atomically; retain full installation backups.

## Read-only campaign readiness

`services/campaign_readiness.py` owns campaign-scoped checks and structured findings
(severity, stable code, message, map identity and inspection URL). The admin pages router
checks authorization first, enables SQLite query-only mode, begins a read snapshot and
passes the campaign to the service. Filesystem checks are best-effort, not an atomic
snapshot with SQLite. No results are persisted and no viewer notifications are emitted.

Room-note validation compares anchor pixels and `area_key` signatures using the current
effective topology. It calls `build_area_map` directly, not reconciliation, fog replay or
viewer rendering. This uses transient memory but creates no fog cache files or changes
to saved notes. Only maps with notes/endpoints need topology construction. Each map is
processed separately; large campaigns may still take time and use image/geometry memory.

`campaign_backup.campaign_payload` is shared by export and readiness so JSON serialization
matches the backup format. Expanded size is the serialized JSON length plus stored image
sizes; no ZIP is generated. Backup exports retain their existing read transaction and
archive format. Compressed size and infrastructure limits are not calculated.

Inspection deliberately uses a separate page without the editor JavaScript or metadata
API, because the existing editor metadata loader reconciles stale room notes. It shows
the authenticated raw image, a report-position marker and stored anchor lists. Editors
are explicit onward links. Image paths outside storage are not embedded by inspection.
No schema migration, runtime dependency or port change is introduced.

## Campaign search and navigation targets

`services/campaign_search.py` streams campaign-filtered rows using parameterized SQL.
The table/column choices come from fixed internal definitions. Python casefold matching
supports Unicode and literal tokens without a database schema/index migration. At most
51 ranked matches are retained for a 50-result response plus a truncation indicator;
campaign rows/text are still scanned for each nonblank request. This is not an indexed
full-text engine; very large note collections may warrant indexing later.

The admin page router checks management authorization before invoking search in an
explicit query-only read snapshot. Search never calls room-note reconciliation, map
activation, geometry mutation or viewer events. Current stored associations are returned
without silently repairing stale data. A generic inspection URL reuses the readiness
inspection handler and template while resolving selected objects by map-scoped identity.

The base template includes the quick-navigation partial only for signed-in admin pages
with a campaign context. The native dialog uses debounced GET requests, aborts superseded
requests, ignores stale responses, inserts results with textContent, and restores focus
on close. Ctrl/Command+K respects other text fields and open dialogs. The full GET-form
page is the no-JavaScript fallback. No persistent search cache/local storage is used.
Selected Markdown is escaped plain text in inspection, not active HTML.

## Named campaign session checkpoints

Migration 16 appends `campaign_checkpoints` (campaign-scoped immutable JSON payload,
name/notes, creator, timestamp and automatic flag) and a monotonic `campaigns.session_version`.
`services/session_checkpoints.py` owns capture, compatibility, preview tokens and restore;
a dedicated admin router owns permissions, CSRF, transactions and post-commit notifications.
No schema history was rewritten. Checkpoint format is version 1; payloads are capped at
64 MiB. History has no automatic retention policy and the list paginates 50 rows at a time.

Capture hashes each stored map image and canonical authored geometry/behavior: map identity,
dimensions, alignment, door-boundary flag, disabled wall types, authored wall/passage rows,
and endpoint positions/default states/destinations. Runtime overrides, names, notes and
appearance settings do not enter those authored fingerprints. Fog configuration is compared
as a whole. File hashes detect in-place image replacements as well as normal new image paths.
Files and SQLite are not one atomic snapshot; avoid concurrent external image modifications.

Payloads store current fog operations, optional last-displayed operations, runtime door/
entry overrides and endpoint overrides for every map, plus active-map choice. Capture is
read-only apart from inserting the named record. Restore does not reconstruct authored rows
or call activation/reconciliation helpers. Fog history is inserted before runtime overrides
so existing hide-all triggers cannot erase restored door states. Last-displayed snapshot
presence/operations are restored separately from current fog.

Compatibility and stale-preview checks run again under a write lock. The token hashes both
the selected payload and captured current state/version; a campaign session generation
increments on restore, including empty campaigns. A savepoint wraps automatic safety
capture and all replacement writes. Malformed runtime references cannot target walls or
endpoints on another map. Restore clears travel replay records and increments map versions/
endpoint revisions, preserving cache identity monotonicity. Caches are invalidated and a
refresh is published only after commit. Publication failure cannot roll back a committed
restore; its safety checkpoint remains available.

Named histories are deliberately excluded from portable campaign ZIPs: they bind local
identities and authored image fingerprints. Full instance/database backups preserve them.
Migration 16 changes no exported content-table columns, so schema-15 portable backups
remain accepted on schema 16 via a narrow compatibility check. Full backup restore normally
leaves prior local checkpoint records incompatible with remapped image/map identities.

## Viewer synchronization diagnostics (step 5)

`services/viewer_sync.py` owns the pure-Python per-connection tracker and shared display
version formatter. EventHub registers a record at subscribe and marks it disconnected on
unsubscribe, including failed publish/kick paths. Viewer sockets bind usernames/user IDs
from authenticated server state, not incoming JSON. Only validated loading/ready/failed
reports or keepalive pings advance contact freshness. No new database tables are created.

The manager-only async status route reads the campaign's active target under a SQLite read
transaction and computes diagnostics on the shared event loop. Active map identity/cache
UUID/wall/fog versions use the same formatter as the viewer API; blank is an explicit target.
An old acknowledgement becomes Loading immediately when compared against a new target.
Readiness is not inferred from publish success, image generation, socket count or HTTP 200.
Failed reports take precedence over mismatched versions; closed/stale transport takes
precedence over all rendering states. No play-state changes, caches or events are emitted.

The viewer preserves the existing refresh-generation checks. It reports Loading before
decode, Ready after successful decode and image installation, and Ready/blank after hiding
the stage. Superseded completions/errors cannot report readiness or failure for a later
refresh. Failed state/image requests and decode errors/timeouts report Failed without
exposing exception text. Existing 40-second fallback refresh permits recovery. Reports are
repeated every 25 seconds with keepalives; a 65-second missing-server-message watchdog is
checked at those intervals. No arbitrary image URLs or authored content enter diagnostics.

Manager panels use non-overlapping five-second polls and textContent-only rendering. On
poll failure old rows are cleared; 401/403/404 stops further polling. Page exit stops polls.
Connection records are in-memory, use monotonic time, and expire 90 seconds after disconnect.
Disconnected history is globally capped at 1024 records; oldest entries can disappear earlier.
Open records follow actual sockets; no unique-player or stable cross-reconnect identity is
claimed. Snapshot/report/connect/disconnect calls run on the one shared application loop.
Process restart clears history, matching the application's supported single-process model.

A client report is diagnostic evidence, not trusted proof of physical display visibility.
Browser sleep, timer throttling or a broken transport can lag classification by the heartbeat,
65-second threshold and manager polling interval. It does not provide durable telemetry,
transport delivery guarantees, screenshots, monitoring of the campaign picker or automatic
repairs. Keep complete backup/restore and viewer authorization behavior unchanged.

## Clean map/campaign duplication (step 6)

On the campaign page, use Settings → Duplicate campaign to create an independently
owned clean campaign, or the Duplicate map disclosure beside a map to copy it into
the same campaign. Enter a copy name (1–120 non-whitespace characters).

Copies preserve authored map images (independent stored files), calibration, wall
and passage definitions, arrow/marker appearance settings, boundary settings,
room names/notes and imported room-library entries. Campaign copies also preserve
map order, description and saved wall sources. Passage endpoint IDs are regenerated;
connections among copied endpoints are remapped. A single-map copy detaches links
to endpoints outside that map; reconnect them explicitly if desired.

Copies start fully fogged, with no reveal history, last-display fog snapshots,
runtime door/passage/endpoint overrides, travel replay records, or session checkpoints.
A campaign copy belongs to the requesting DM, has no viewer assignments and no
active map. A map copy is appended in its existing campaign and never made active.
The source campaign, its viewer display and its runtime state are unchanged.

The operation requires campaign-management permission and CSRF validation; campaign
copy also requires campaign-creation permission. Database writes share one immediate
transaction. Images created before an error are removed after rollback. No migration,
new dependency, configuration change or port change is required. Large copies hold
the SQLite write transaction while validating and copying images; allow adequate disk
space and avoid concurrent bulk writes. Process termination can leave orphan image
files (as with other multi-resource operations); database commit is still transactional.

## HTTP access-log noise (item 8)

By default, the built-in dual-portal server filters successful/informational HTTP
access records (100–399, including redirects and 304 responses) from
`uvicorn.access`. HTTP 400–599 access records remain visible at the configured
log level. Warnings/errors, unknown access-record formats and the separate
`uvicorn.error` / application loggers are not suppressed by this filter.
This affects logging output regardless of whether your deployment routes it to
stdout, stderr or a file; reverse-proxy access logs are unaffected.

For temporary full HTTP access logging, set in config.yaml and restart:

```yaml
server:
  access_log_success: true
```

The default is `false`; use actual YAML booleans, not quoted strings. Existing
configurations need no edit. `server.log_level` still applies: 4xx access records
normally have INFO severity, so choosing a WARNING log level can hide those too.
The filter targets Uvicorn's HTTP access tuples; WebSocket lifecycle messages on
other loggers remain unchanged. External Uvicorn launchers that bypass
`looking_glass.server.build` must configure their own logging policy.
