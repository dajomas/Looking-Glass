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

