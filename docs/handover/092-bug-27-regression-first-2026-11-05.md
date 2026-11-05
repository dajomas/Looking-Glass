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
