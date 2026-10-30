## Bug 2: strict transactional ordinary-save validation (2026-10-30)

Prepared against features/perplexity HEAD
e70ab265dff6e92d9b25a151cf8e375cf3ca30d2. This activates the server half
of the ordinary-save context contract after payload and editor increments.
It is implementation, not verified acceptance or closure of bug 2.

POST /api/maps/{map_id}/room-notes requires x/y, a 64-character area_key,
revision, cache_token (1-128 characters), walls_version and room_notes_version.
All five validation fields are required without defaults; strings are strict
strings and counters are strict nonnegative integers. Missing/invalid fields
use FastAPI's 422 response. Existing name/Markdown defaults and length limits
remain unchanged. Old clients must reload and select a room again; the server
does not supply new stamps for an old draft.

The route starts BEGIN IMMEDIATE before management authorization, reconciles
and resolves the target through _room_at, then compares all five fields inside
the same transaction. Mismatch returns 400. The upsert also predicates updates
on the submitted target revision and checks that exactly one row was written.
A successful response returns refreshed note revision/generation and no-store.
Fog version is deliberately not part of note validation: ordinary fog edits
that do not change effective boundaries need not invalidate a note draft.

Names retain existing explicit-save trimming; Markdown is stored unchanged.
Updating does not move the existing anchor. Explicit clearing remains supported.
No fog writes, active-map changes or viewer notifications are added. Exceptions
escaping the database context roll back the whole request, including any
reconciliation performed while rejecting a stale save. This can defer archival
until a subsequent successful reconciliation; it cannot commit the old draft.

The inspected legacy room-note import and library-unassign HTTP tests now carry
selection stamps on legitimate requests. Subsequent edits use the preceding
successful response context; stale-save assertions still use deliberately old
context and still expect 400. They also check generation advancement/no-store
where relevant. The earlier 41 integration contracts already construct saves
with all context fields. No request auto-stamping, exclusions, skips, xfails,
status-code tolerances or workflow changes are introduced.

Validation: current HEAD, live api.py, README.md, HANDOVER.md, docs/api.md's
returned excerpt and six candidate legacy test modules were reviewed. No
application imports, migration runner, pytest collection, HTTP/browser tests or
Actions results were executed/verified for this increment. This is not an
exhaustive audit of every save caller; full-suite execution may identify more
legacy test/request adapters. Strict-type cases, independent stale-field cases,
storage-failure/rollback, successful clearing and fog-only changes still need
explicit execution/expanded regression coverage. No pass counts are claimed.

Run the two adapted tests and test_room_notes.py, the new/existing editor Node
regressions, and test_room_note_archive_web.py through CI. Recovery-dependent
cases still fail until recovery is implemented. Record exact tested SHAs and
results rather than inferring success from this commit or workflow definition.

Remaining: archive listing, explicit management-only revision-safe recovery/UI,
archive-aware backup/restore/duplication with schemas 15-17 normalization,
migration/reconciliation regressions, full browser/live/deployment acceptance
and final API/usage documentation. The oversized docs/api.md was returned
truncated; it was not replaced from that incomplete content. This focused record
provides the current save contract pending final guide integration. README.md
was reviewed; it does not document the request schema or advertise completed
recovery. The branch remains non-deployable against valuable campaign data;
portability warnings in records 050-053 remain relevant. Keep bug 2 open.
Historical handover text and reconstruction manifests remain unchanged, with
only a short index link added. No Patch/ material is included.
