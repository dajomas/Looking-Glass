# Bug 27: regression-first notes-only editor refresh

## Scope and decision

The user requested a failing test first and a commit containing [skip ci].
Target: dajomas/Looking-Glass, features/perplexity. No production fix, migration,
bug closure, workflow exclusion, archive or Patch/ material is included.

Added python/tests/test_room_notes_sync.js, using the actual LGRoomNotes class
with isolated DOM/API doubles, following existing room-note test conventions.
Two regression cases simulate a remote save and a remote unassign by changing
only room_notes_version while cache_token, walls_version and fog_version remain
unchanged. They require clean selected content to refresh; the unassign case
also requires imported-name assignment availability to refresh. A safety case
requires dirty text, selected room identity and original save context to survive
a notes-only refresh, without a background save or discard confirmation.

Run from the repository root:

```bash
node --test python/tests/test_room_notes_sync.js
```

## Existing coverage reviewed

Reviewed test_room_notes.js, test_room_note_save_context.js,
test_admin_editor_ordering.js, test_room_library_manager.js,
test_room_name_overlay.js, test_room_note_archive_web.py and
test_room_note_import_web.py before preparing this test-only change. Existing
stale-save rejection, local-unassign and delayed-selection contracts are retained.

## Validation and limitations

The live room_notes.js refresh stamp omits room_notes_version and returns early
when only that revision changes. Source review therefore predicts failure of
the remote-save and remote-unassign assertions, while the draft-preservation
case is expected to pass. These are expectations, not executed results.
No Node, application, HTTP, browser, live, recovery, full-suite or CI tests were
executed during preparation. [skip ci] requests skipped CI; it is not evidence
that a workflow was actually skipped or that any checks passed.

This is an isolated client regression, not a two-browser reproduction. It injects
the notes revision directly into refresh and does not cover exposing that field
in the admin API, the editor polling comparison, stale-context feedback, overlay
refresh, or delayed notes/library response ordering. Those remain follow-up work
for the bug-27 implementation. Bug 27 remains open.

README.md and HANDOVER.md were read from the live target branch. README.md needs
no change because this commit adds no implemented behavior or new test runner.
HANDOVER.md receives only a navigation link to this focused record. Existing
historical records and split manifests are unchanged. New files and the updated
handover index remain below the 25,000-byte limit; no size-driven split is needed.
Delivery remains pending exact approval and a successful GitHub write.

## User-reported red baseline and implementation increment 1

The user ran node --test python/tests/test_room_notes_sync.js on 2026-11-05:
3 tests, 1 pass, 2 failures, no skips. Remote-save failed because Crypt remained
instead of Renamed crypt. Remote-unassign failed because Crypt remained instead
of an empty name. Dirty-draft preservation passed. The unassign test stopped at
the name assertion, before library/picker assertions. This is user-reported
isolated Node evidence, not an assistant execution or browser/HTTP validation.

Increment 1 changes only static/js/room_notes.js and this already-indexed record.
The client accepts an explicit room_notes_version and separately tracks fog and
notes stamps. Notes-only revisions fetch assignment availability and clean
selected content, retaining pristine edit mode. Dirty drafts retain their text
and original room/save context and receive a warning. Selection, draft, save and
refresh generations fence asynchronous installation. Save and Cancel invalidate
the cached refresh stamp; errors and superseded work remain retryable. The old
fog/reveal path remains available for payloads without a notes revision. Notes-only
unassignment does not run the hidden-room cleanup path. Server stale-save checks
and all existing regression assertions are unchanged.

This is deliberately an incomplete integration increment: _map_payload still
needs to expose room_notes_version, readState must detect it and retry failed
notes refreshes on unchanged polls, and the named-room overlay/open library
manager require coordinated invalidation. Real cross-editor application polling
is NOT fixed by this increment alone. Do not close bug 27 or advertise full
convergence based on isolated tests. Follow with API/polling integration, overlay
and manager ordering work, and API/polling/delayed-response regression coverage.

Validation during candidate preparation: source review only. No candidate Node,
Python, HTTP, browser, live, recovery, full-suite or CI tests were executed; no
passing candidate result is claimed. The three existing sync cases are expected
to exercise this client change, but must be rerun. README.md and HANDOVER.md were
reviewed again; README advertises no new sync guarantee and needs no change for
this incomplete increment. HANDOVER already links this focused record. No new
script asset or template integration is introduced. The edited JavaScript remains
below 25,000 bytes; no split is required. No migrations, other branches, archives,
Patch/ material, or [skip ci] marker are included in the implementation increment.
The earlier skip request was scoped to the regression-only commit. Delivery is
pending exact approval and successful write; report its SHA only after success.

## Increment 1 local evidence and admin payload increment

Increment 1 was delivered as dfcc91b31653491c03410ee311e90b997269ff85.
The user subsequently reported test_room_notes_sync.js: 3 passes, 0 failures,
0 skips; test_room_note_save_context.js: all 6 cases passed; test_room_notes.js:
its UI, confirmation, auto-edit and assigned-name filtering checks passed. The
unassign case now reached its assignment/picker assertions. These are user-run
local Node results, not assistant-run tests, CI, HTTP or two-browser evidence.

The next narrowly scoped increment adds room_notes_version to _map_payload,
reading the existing maps row after reconcile_map. This adds no notes content to
viewer responses, no migration, fog bump or notification. Existing authorization
and server stale-save validation are unchanged. Polling, unchanged-state retries,
overlay and open-library invalidation remain pending; bug 27 stays open.

Added test_room_notes_version_payload_web.py using the existing real-app flow
fixture. It requires an integer nonnegative revision matching room-at, verifies
advancement after a notes-only save and unassign, checks unchanged cache/fog/wall
versions, and verifies repeated reads do not advance the notes revision. This
test would fail on the prior payload's missing field; it has not been executed
during preparation. No candidate Python, HTTP, browser, live, recovery, full-suite
or CI execution is claimed.

Run in the normal development environment:

```bash
cd python
../.venv/bin/python -m pytest -q tests/test_room_notes_version_payload_web.py
```

README.md and HANDOVER.md were read again. README needs no new sync guarantee
for this payload-only increment, and HANDOVER already links this updated record.
The existing API file is 24,708 bytes; the single added ASCII line is 54 bytes,
leaving 24,762 bytes, below the 25,000-byte split threshold. Existing records and
all tests are retained, with no exclusions or [skip ci]. Delivery of this payload
increment is pending exact approval and successful GitHub write.

## Payload test fixture registration correction

Payload delivery succeeded as 1688aacb49a51be76cae65b2df1f99fee56ec12a.
The user ran the individual HTTP regression using .venv-test and reported one
setup error: fixture 'env' not found. No payload assertion ran, so this result
provides no passing or failing evidence for the payload behavior itself.

The new test module imported flow but not its env dependency. env is declared
in test_web.py, not conftest.py. Explicitly importing env into the consuming test
module makes it discoverable alongside flow. This correction adds only that
import, retaining all assertions and production code without skips or exclusions.
The reported sys.prefix/sys.exec_prefix warnings are not the missing-fixture
exception; no environment or warning-suppression changes are included.

README.md and HANDOVER.md were reread from the target branch. Neither needs a
cosmetic edit for this test-only correction; HANDOVER already indexes this record.
Both edited files remain below 25,000 bytes. No tests were executed during
preparation of the correction. Rerun the single HTTP regression in the normal
dependency environment; fixture setup and payload validation remain unverified
until that run completes. Polling and overlay/library integration remain pending
and bug 27 stays open. This correction's GitHub delivery is pending exact
approval and successful write.
