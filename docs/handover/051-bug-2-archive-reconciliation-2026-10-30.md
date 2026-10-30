## Bug 2: archive-before-detach reconciliation (2026-10-30)

Prepared against features/perplexity HEAD
572b2f6db950146439cd5f51319fb5cd8cd36415. This increment implements the
previously drafted reconciliation logic in services/room_notes.py. Migration
18 is required. It is not completion or deployment acceptance of bug 2.

archive_assignment copies complete stored names/Markdown, area key, anchors,
source revision and detection-time map/campaign provenance with INSERT SELECT.
There is no trimming, Markdown normalization, imported-library substitution or
INSERT OR IGNORE. A new origin UUID identifies each archival event. The helper
requires a caller-owned transaction and does not commit or detach by itself.

remove_stale preserves the existing exact anchored geometry identity rule. It
creates a local savepoint, archives every stale assignment before any deletion,
checks insert/delete row counts, and rolls back local work on failure. If SQLite
has already aborted the whole transaction, local savepoint cleanup is skipped.
The caller owns final commit/rollback. Nested caller transactions are retained.
An exception caught by a caller must not leave partial archive/detach work.

reconcile_map starts BEGIN IMMEDIATE when no transaction exists, before note
queries and geometry loading. Existing transactions are not replaced; lock
upgrade failures propagate. Production geometry must be loaded inside this
transaction, not reused from an earlier snapshot. Calls can hold a write
reservation while computing geometry, including read-time reconciliation and
calls where no notes need detachment. Contention/performance is unmeasured.

Imported-name release remains derived from active room_notes rows. Library
content, unaffected rooms and other maps are not rewritten. Component identity
still uses the existing area_key implementation. Archives are never used for
automatic reassignment, even if old geometry returns. New generation triggers
advance only for detached active assignments; rollback also reverses them.
There are no added fog operations, viewer notifications, active-map changes,
archive purge operations or artwork changes. Authorization remains at existing
management routes; these internal services do not perform permission checks.

Validation: live HEAD, README.md, HANDOVER.md and room_notes.py were reviewed.
No application tests, migration runner, HTTP/browser suite, pytest collection
or deployment tests were executed for this increment. No Actions run/tested
SHA has been verified. Earlier minimal SQL checks do not validate this final
service implementation. Existing integration tests still require context
fields and recovery routes that are absent. No skips/exclusions are introduced.

Remaining: validate this increment with migration/service regressions, add
revision-safe save context and payload fields, management-only explicit recovery
and UI, and archive-aware backup/restore/duplication with legacy normalization.
The portability warning in record 050 still applies: archives are not exported
or duplicated yet, schema-17 backups are rejected and older map columns need
normalization. Do not deploy this intermediate branch against valuable campaign
data or rely on campaign ZIPs to retain archives. Keep bug 2 open.

README.md was reviewed; normal user-facing workflows remain unchanged and
recovery is not advertised as available. The incomplete-branch retention and
portability limitations are recorded here and linked from HANDOVER.md. Existing
historical records and reconstruction manifests remain unchanged. No Patch/
material is included.
