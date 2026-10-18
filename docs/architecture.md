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
