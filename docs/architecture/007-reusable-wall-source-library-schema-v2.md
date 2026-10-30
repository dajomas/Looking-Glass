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

