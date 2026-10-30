## Bug 2: editor save context and delayed-response protection (2026-10-30)

Prepared against features/perplexity HEAD
d0216524065e38e1c8bafa32a9372ac98533483f. This implements task 1 of the
next-task list, the editor step after payload context and before strict server
validation. It does not finish revision-safe ordinary saves or bug 2.

The submit handler copies the selected room and point/content into one request
before awaiting anything. It sends area_key, revision, cache_token,
walls_version and room_notes_version from that selection, never stamps from
background map state. Starting a save invalidates pending selection and refresh
generations. Duplicate submits and selections while saving remain blocked.
Successful saves install returned content/context only for the same selection
generation. Error handling preserves fields, edit mode and old context, restores
controls and does not automatically reselect, rebase or retry. The beforeunload
draft warning remains in effect.

select() also captures draftVersion and rejects responses when editing began
after its request, when superseded by another selection or while saving. No fog
or viewer operations, notifications, automatic note reattachment or purge are
added. Existing Markdown/import/clear controls are otherwise unchanged.

Unlike the earlier illustrative draft, this increment does not add a client-side
context preflight guard. It submits captured values without inventing defaults;
required-field/type/staleness checks belong to task 2's server implementation.
Old or malformed payloads must fail server validation once that is activated.
Existing legacy UI fixtures remain unchanged; a separate context-aware fixture
uses realistic 64-character area keys and all three context fields.

python/tests/test_room_note_save_context.js loads the real editor source in
isolated Node VM contexts with DOM/API doubles. Six promise-controlled cases
cover selected-versus-background stamps and successful context replacement,
draft retention/no automatic retry and beforeunload after rejection, delayed
selection during editing, save-time selection/duplicate-submit blocking, late
refresh after save, and out-of-order selections. The existing top-level JS
runner discovers the script; CI reports scripts, not these nested case counts.
This is not browser, real HTTP, CSRF, SQLite or live-listener validation.

Validation: current HEAD, live editor, README.md and HANDOVER.md were reviewed.
No Node scripts, application tests, browser tests or workflow runs were executed
or verified for this increment. The six cases are supplied, not claimed passed.
Run from repository root: node python/tests/test_room_note_save_context.js
and node python/tests/test_room_notes.js. Also run the full JS runner and HTTP
regressions after strict server validation is delivered. No skips/exclusions or
workflow edits are included.

Next: require and validate all save context fields transactionally in api.py and
adapt legitimate HTTP test requests. Recovery/listing/UI and archive-aware
legacy-compatible backup/restore/duplication remain unfinished. The branch is
not deployable against valuable campaign data; records 050-052 remain relevant.
Keep bug 2 open. README.md was reviewed and remains accurate for existing UI
operations; no complete stale-save or recovery capability is advertised. This
focused record and its index link preserve historical records and reconstruction
manifests unchanged. No Patch/ material is included.
