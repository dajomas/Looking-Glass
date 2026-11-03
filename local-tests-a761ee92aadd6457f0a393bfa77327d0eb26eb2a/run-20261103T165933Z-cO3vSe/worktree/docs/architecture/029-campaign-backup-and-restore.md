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

