## Bug 2: explicit archive listing and recovery (2026-10-30)

Prepared against features/perplexity HEAD
45ee4bf1a19de088a5b62b37800b3a95dd2b2eb2. This implements the drafted
management-only backend, not the recovery UI or completion of bug 2.

New service room_note_recovery lists bounded newest-first pages (default 50,
maximum 200) and explicitly restores stored names/Markdown without trimming.
Local ownership is scoped by map_id and archive ID. Nonempty target content,
including whitespace, requires overwrite=true and is archived before replacement
as recovery_replacement. A savepoint protects replacement/archival; the caller
owns final transaction commit. The source archive is retained, not consumed or
automatically reassigned. Target association uses current geometry/coordinates
and its revision increments rather than copying the source revision.

New admin routes use existing session, management and CSRF dependencies.
Recovery holds BEGIN IMMEDIATE across authorization, archive scoping, current
geometry/context validation and mutation, reusing _room_at and
_require_current_room. Missing/invalid body fields are 422, stale/conflicting
targets 400, missing/wrong-map archives 404; storage errors propagate after
rollback. Unknown recovery body fields are forbidden. No fog/active-map/artwork
changes, viewer publications, archive editing, automatic reattachment or purge
are introduced. Listing can perform existing retention-safe read reconciliation.

Wiring refinement from the illustrative draft: app_factory creates a fresh
APIRouter for each admin app and passes the existing resolver/validator into
registration. It does not mutate the shared admin_api router and does not mount
recovery on the viewer app. No circular import from the new routes into api.py
is needed. The ordinary-save implementation is unchanged.

A new HTTP regression module supplies pagination completeness/disjointness/map
isolation, invalid query, strict overwrite, forbidden content-substitution,
transaction-precondition and per-app registration cases. Existing 28 archive
HTTP cases cover core recovery/RBAC/CSRF/staleness/replacement/storage rollback.
Pagination setup creates replacement archives via real save/recovery endpoints.
These tests are supplied, not recorded as executed or passed.

Validation: current HEAD, live app factory, README.md and HANDOVER.md were read;
recovery design is reconciled with existing service/helpers and committed test
contracts. No application imports, pytest collection, migration runner, HTTP,
browser, Node or deployment tests were executed for this increment. No Actions
run/tested SHA or pass counts have been verified. Run test_room_note_archive_web.py
and test_room_note_recovery_web.py, existing room-note tests and full workflows.
The 13 portability cases remain expected to fail until portability is finished.

The new focused guide docs/room-note-recovery.md documents development API
behavior and limitations without replacing the previously truncated docs/api.md.
README.md was reviewed; it does not advertise a recovery UI or completed archive
portability and is unchanged. Final API/usage guide integration remains pending.

Remaining: recovery UI with pagination and draft-preserving confirmations,
archive-aware backup/restore/duplication including legacy normalization,
migration/reconciliation and strict-save regression expansion/execution, exact
workflow evidence review, full/browser/live/deployment acceptance and final
documentation. Do not deploy this intermediate branch against valuable campaign
data or rely on ZIPs to preserve archives. Keep bug 2 open. Existing historical
handover records and reconstruction manifests remain unchanged; only a short
index link is added. No Patch/ material is included.
