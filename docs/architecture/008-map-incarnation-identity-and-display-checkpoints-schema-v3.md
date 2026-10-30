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


