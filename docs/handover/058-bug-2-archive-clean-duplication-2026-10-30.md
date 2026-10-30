## Bug 2: archive-aware clean duplication (2026-10-30)

Prepared against features/perplexity HEAD
5e9f3db3ab5c87c5b9e6573339838f365bfe9c22. The duplication AUTHORED allowlist
now includes room_note_archives. The existing generic copy loop regenerates the
local integer ID and replaces current map ownership, preserving exact text,
anchors, old area identity, reason, timestamp, origin UUID and all historical
source_* fields. The field is source_revision, not revision, so the active-note
revision reset does not alter archived provenance. No UUID deduplication or
automatic room assignment is introduced.

New maps initialize room_notes_version=0 rather than inheriting the source
counter. Existing note insert triggers advance it for copied active assignments.
The counter is local to the new map incarnation; archived source tokens and
revisions remain historical. Existing authored-note copying, image independence,
fog/runtime resets, connection remapping, ownership/viewer assignment rules and
nonactivation/source isolation behavior are unchanged. No new routes, schema,
permissions, CSRF behavior, viewer notifications, archive purge or recovery
changes are included. Existing caller transaction and image cleanup remain.

New service regressions use the existing real migrated database/PNG fixtures.
Map/campaign copies are each made twice to verify lineage UUID reuse without
local ID collision, exact historical metadata/content, source/unselected map
isolation, active-versus-detached content, independent counters/tokens/images
and clean fog/runtime state. Other-map archives must not leak into a single-map
copy. A separate map/campaign fault case raises after a real archive insert and
checks full database rollback plus caller-owned cleanup of only new image files.
The source fixture uses direct SQL identities/active notes, not geometry-driven
selection; do not present these service tests as geometry/HTTP/browser acceptance.
The previously committed portability HTTP cases exercise real geometry, pixels,
stale contexts and explicit recovery on copies; they remain unexecuted here.

Validation: actual HEAD, live duplication source, existing duplication tests,
backup guide, recovery template, README.md and HANDOVER.md were reviewed. No
application imports, pytest collection, service/HTTP/browser/Node tests, full
workflow or deployment tests were executed/verified for this increment. No pass
counts or Actions run/tested SHA are claimed. Run test_duplication.py,
test_room_note_duplication.py and test_room_note_archive_portability_web.py plus
all related suites. Implementation must not be confused with acceptance.

The existing focused portability guide now describes copying instead of claiming
archives are omitted. The workspace warning now distinguishes implemented
backup/restore/duplication from pending validation. README.md was reviewed; its
existing nonexclusive clean-copy summary remains compatible, with final retention
README/API/usage integration still pending closure. Historical records and both
reconstruction manifests remain unchanged; HANDOVER.md adds a short link only.
Keep bug 2 open. Remaining: expanded migration/reconciliation/strict-save/UI
regressions and execution, actual workflow evidence review, any necessary fixes,
final docs and deployment acceptance. Do not use valuable campaign data until
acceptance is complete. No Patch/ material is included.
