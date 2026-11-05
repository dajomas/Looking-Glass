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

## Passing local payload regression (2026-11-05)

The fixture correction was delivered as
079ddc67718e634eaddbff28ef48f9243e1ff98c on features/perplexity.
The production payload addition and its HTTP regression were already delivered
as 1688aacb49a51be76cae65b2df1f99fee56ec12a; this evidence update does not
reapply or modify those code changes.

The user reported running the following command from the repository root:

```bash
.venv-test/bin/python -m pytest -q python/tests/test_room_notes_version_payload_web.py
```

Reported output: 1 passed in 7.62s. This replaces the earlier setup-only result
for purposes of this specific local regression: fixture setup completed and all
assertions in the single test passed. Those assertions cover integer/nonnegative
admin payload revision exposure, equality with room-at, advancement after a
notes-only save and unassign, unchanged cache token/wall/fog versions, cleared
room content after unassign, and revision stability on repeated reads.

Evidence is user-provided local output. The assistant did not execute or
independently reproduce this run, and the user did not supply a checkout SHA
with the output. Do not present it as CI, full-suite, browser, live-listener,
recovery or two-editor end-to-end validation. Earlier preparation statements and
the setup failure above remain historical records, not the latest test result.

Current delivered scope: the client handles explicit notes revisions and the
admin map payload exposes the existing revision. Remaining work: editor polling
detection and unchanged-state retries, coordinated named-room overlay/open
library-manager invalidation, and additional integration/response-order
coverage. Bug 27 remains open; these results do not establish automatic
cross-editor convergence in the running application.

README.md and HANDOVER.md were reread from the live working branch. No README
behavior claim or index change is needed for this evidence-only update because
HANDOVER already links this focused record. Only this record changes; it remains
below 25,000 bytes. No tests were run during evidence-record preparation, no
assertions or workflow exclusions changed, and no migrations, archives or Patch/
material are included. This documentation commit's delivery is pending exact
approval and a successful GitHub write.

## Polling and unchanged-state retry candidate (2026-11-05)

The next increment changes readState in static/js/admin_map_editor.js: its
comparison includes room_notes_version and its accepted unchanged-state path
also calls roomNotes.refresh. The component's existing stamp suppresses completed
work while its null stamp after a failed/deferred refresh permits a later poll
to retry. No pending flag is duplicated in the editor. The request-generation
guard runs before both paths; stateKey, mask identities, poll interval, action
responses and server stale-save checks are unchanged. No new script asset or
template dependency is introduced.

Added python/tests/test_admin_notes_polling.js with five cases using the complete
production editor IIFE, actual room-notes class and wall renderer under isolated
DOM/image/API doubles. A test-only IIFE observation seam exposes the notes object
and state. Cases require notes-only convergence without new masks, same-revision
retry after library failure, same-revision retry after room-at failure, retry
after a simulated saving flag clears, and rejection of a pre-action stale poll.
The library-retry case also checks completed work is not fetched repeatedly.
These are client integration contracts, not live HTTP or browser tests.

Validation performed during preparation: source review only. No new Node tests,
existing ordering/mask tests, Python, HTTP, browser, live, recovery, full-suite or
CI tests were executed. The five cases are prepared contracts, not passing results.
Run from the repository root:

```bash
node --test python/tests/test_admin_notes_polling.js
node --test python/tests/test_admin_editor_ordering.js
node --test python/tests/test_admin_mask_identity.js
node --test python/tests/test_room_notes_sync.js
node python/tests/test_room_note_save_context.js
```

README.md and HANDOVER.md were reviewed on the live branch. The existing handover
index already links this record; README gains no full-convergence guarantee while
overlay/open-library invalidation and end-to-end acceptance remain pending.
The editor starts at 23,522 bytes and this small addition remains below 25,000;
the new test and this record also stay below the limit. All existing tests and
historical records are retained without exclusions. No migration, [skip ci],
archive or Patch/ material is included. Bug 27 remains open. GitHub delivery is
pending exact approval and successful write.

## Passing polling evidence and overlay candidate (2026-11-05)

Polling integration was delivered as 548b99187df8d21c9163d709bc1412c749858e41.
The user subsequently reported all five listed scripts passing: admin notes
polling 5 cases, editor ordering 10, mask identity 4, room-notes sync 3 and
room-note save context 6, totaling 28 cases. The four node --test reports show
zero failures and zero skips; the save-context script reports all six cases
passed. These are user-run local client results, not independently rerun tests,
CI, browser or live-server evidence. No checkout SHA accompanied the output.
The code was already committed; this record adds that passing evidence.

The overlay increment adds room_notes_version to LGRoomNameOverlay.mapChanged's
identity using JSON.stringify and clears the stamp only on a current request's
failure, permitting retry on an unchanged-state poll. Existing generation guards
retain late-success/error fencing and disabling behavior. Old coverage is hidden
while fetching replacement coverage; successful unchanged revisions do not
refetch and an identical poll does not duplicate the pending request. No change
to fog masks, room drafts, server routes, schema, permissions or script loading.

Added test_room_name_overlay_sync.js with five cases: notes-only coverage/count
refresh, superseded success, superseded failure, same-revision failure retry
without duplicate in-flight work, and disable-during-notes-refresh.

Assistant validation actually executed under sandbox Node v20.20.1: the new
five-case suite failed all five cases against the unchanged overlay and passed
all five against the candidate, with zero skips. Most baseline cases stop at the
missing notes-invalidation assertion before their later ordering assertions;
this is not evidence of five independent baseline defects. The existing
test_room_name_overlay.js also executed successfully against the candidate.
The reconstructed baseline matched live Git blob
c9fb142710ca335d58ddef12944f8334ec2227f0 and the existing test matched blob
0fd4d4145978e5ebefbab43d0910cac595d71f71 before execution.

These were isolated actual-class/DOM/API-double checks in a temporary sandbox
layout, not a repository checkout, Chromium run, real API/image-decode test,
full-suite run or CI execution. Candidate coverage validates response installation
and count text, not the server-generated PNG's pixel correctness.
Overlay bytes: baseline 2,123, candidate 2,233; new test 4,239 bytes.

Run from the repository root in the normal environment:

```bash
node --test python/tests/test_room_name_overlay_sync.js
node python/tests/test_room_name_overlay.js
```

README.md and HANDOVER.md were read again. Existing overlay usage remains
accurate; no full-sync guarantee is added before acceptance. HANDOVER already
links this updated record. All proposed files remain under 25,000 bytes, so no
size split is needed. The open imported-notes manager still needs coordinated
revision invalidation and request ordering with the picker. Further delayed
notes/library response coverage and two-editor browser acceptance remain pending.
Bug 27 is not closed. No unrelated changes, migrations, [skip ci], archives or
Patch/ material are included. Delivery of this overlay increment remains pending
exact approval and a successful GitHub write.

## Overlay local evidence and manager/picker regression-first increment

Overlay delivery succeeded as 00937cac896e7c43f20685716e4f086caef5f205.
The user subsequently reported test_room_name_overlay_sync.js: 5 passes, zero
failures/skips, and successful execution of test_room_name_overlay.js. This is
additional user-run local evidence, not CI or browser acceptance.

Added python/tests/test_room_library_sync.js before changing production library
synchronization. It loads the real room-notes and manager classes; the owner is
created from the production prototype with explicitly seeded constructor state,
and the manager is constructed normally. Real refresh/loadLibrary/render methods
run with DOM/API doubles and controlled library promises. Cases cover an open
manager following notes-only unassign, older dialog/newer picker ordering, the
reverse ordering safety contract, suppression of obsolete dialog errors, and
assignment convergence while a dirty room draft and its save context survive.
No alternate production implementation is embedded in the test.

Preparation validation: source review only; this new suite was not executed.
Current source suggests four missing synchronization/error-order contracts fail
and the existing older-picker/newer-manager protection passes. These are
expectations, not measured results. Do not label this suite passing or the
manager fixed. Production code and existing tests are unchanged; no skips,
exclusions or [skip ci] are introduced. Normal JavaScript CI is therefore
expected to expose intentional regression-first failures until the fix lands.

Run from the repository root:

```bash
node --test python/tests/test_room_library_sync.js
node python/tests/test_room_library_manager.js
```

Follow with one coordinated library acceptance/read-generation policy shared by
the dialog and picker, preserving dirty drafts, mutation safety, loading/error
recovery and closed-dialog behavior. Extend mutation/close/retry cases as needed,
then perform two-editor browser acceptance before closing bug 27. This test-only
increment does not implement that policy or prove full application convergence.

README.md and HANDOVER.md were reread on the live branch. README advertises no
new behavior and needs no cosmetic update; HANDOVER already links this record.
Both proposed files remain below 25,000 bytes. No migrations, other branches,
archives or Patch/ material are included. Delivery is pending exact approval
and successful GitHub write; report the actual commit only after success.

## Manager/picker implementation awaiting delivery

The user reported the committed manager/picker suite at 4 failures, 1 pass and
zero skips, with the existing manager script passing. No candidate tests have
been executed. Earlier write attempts were rejected by the approval gate and
did not modify the repository. The live JavaScript files were reread before
preparing this fresh exact-content confirmation.

The candidate adds syncEntries to refresh an open manager from accepted picker
GET/import results while preserving scroll and busy controls. Manager accept
uses the same rendering helper with an explicit force flag for its own results.
Manager refresh takes a shared owner.libraryGeneration ticket plus its dialog
generation; both must match before accepting data or displaying errors. Its
finally cleanup uses the dialog generation alone, releasing controls even when
a newer picker request supersedes the result. If Loading was not replaced by
new data/error status, it displays an explicit retry message. Existing mutation
handlers, close behavior, room drafts and save-context validation are unchanged.

Validation remains source review only: no candidate Node, Python, HTTP, browser,
live, recovery, full-suite or CI run is claimed. Existing tests are unchanged.
Rerun the library sync, manager, notes UI, save-context and admin polling scripts.
Additional mutation/close/import/retry ordering coverage and two-editor browser
acceptance remain unfinished. Shared generations order client requests, not
server snapshots by a returned library revision. Bug 27 remains open.

README.md and HANDOVER.md were reread. No full-sync guarantee is advertised, and
the existing handover index already links this record. All three proposed files
remain below 25,000 bytes; no split is required. No schema, API, permission, asset
loading, test exclusion, [skip ci], archive or Patch/ changes. This exact write
requires fresh approval; report a delivery SHA only after successful write.
