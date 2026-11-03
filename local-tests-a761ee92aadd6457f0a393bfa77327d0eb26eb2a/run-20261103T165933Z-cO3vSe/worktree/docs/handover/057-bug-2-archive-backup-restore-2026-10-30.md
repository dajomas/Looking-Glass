## Bug 2: archive-aware backup and restore (2026-10-30)

Prepared against features/perplexity HEAD
2cf52a3461db993e687ae148885ad7df9a7d6c59. room_note_archives is added to
MAP_TABLES, so campaign export, inspection clones, restore, target digests and
durable pre-restore safety ZIPs include retained content. Generic restore remaps
only current map_id, regenerates the local integer archive ID and preserves
all source_* metadata, source revision, origin UUID, timestamp and exact text.
No automatic assignment, filtering/deduplication, purge or reconciliation is
introduced by export/restore. Existing explicit full-campaign restore play-state
semantics/notifications and authorization/CSRF/preview/name confirmation remain.

A separate compatibility helper accepts explicit integer schemas 15-18 and
format version 1. Legacy schemas 15-17 must omit archive table/generation fields
and receive empty archives/initial generation zero; schemas 15/16 also receive
the existing empty double-reveal tables. Unexpected new legacy fields and
missing current-schema tables/columns are rejected, not silently discarded.
After exact column checks, archive integer/text/finite-coordinate/reason types
and map note generations are validated before target replacement. Historical
identifiers/anchors are not constrained to current geometry or foreign keys.
Inspection reports normalized content counts. Future schema compatibility must
be extended deliberately, not inferred from len(MIGRATIONS).

The old compatibility fixture now constructs genuine legacy shapes, adding
schema-17 acceptance while retaining schema-14 rejection. New service regressions
use migrated SQLite and real PNG storage for detached-content roundtrip into
another campaign, historical IDs outside the backup, archive-only preview
invalidation, and failure at real archive insertion with full DB rollback and
caller-owned created-image cleanup. The earlier portability HTTP contracts cover
current/legacy restore, malformed archive validation, safety ZIP retention and
stale contexts; their clean-duplication cases remain intentionally unresolved.

Validation: actual HEAD, live backup service, README.md, HANDOVER.md, existing
backup/inspection tests and the committed portability module were read. No
application imports, pytest collection, migration runner, HTTP/browser, full-suite
or deployment tests were executed for this increment. No Actions run/tested SHA
has been verified and no pass counts are claimed. Run test_campaign_backup.py,
test_campaign_backup_inspection.py, test_room_note_backup.py and all portability
HTTP cases through the workflows; do not hide duplication failures.

README.md was reviewed; its existing backup summary remains compatible. The new
focused docs/room-note-backup.md records archive behavior, compatibility and
validation caveats. Final README/API/usage integration and recovery UI warning
wording can be finalized after duplication and acceptance, not by claiming ZIP
acceptance now. Existing UI/guide warnings remain conservative because acceptance
and complete portability are unfinished.

Next: archive-aware clean duplication, regression expansion/execution, exact CI
evidence review and final documentation/acceptance. Do not deploy this intermediate
branch against valuable campaign data. Keep bug 2 open. Historical handover
records and reconstruction manifests remain unchanged, with one short index
link added. No Patch/ material is included.
