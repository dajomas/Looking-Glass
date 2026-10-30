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

