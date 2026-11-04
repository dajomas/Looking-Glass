# Bugs 17/18: regression-first lifecycle checks

## Scope and status

Baseline: `3c48b47abb89b1cbc98d7d8ca46261cdd47c6299` on
`features/perplexity`. This is an intermediate test-only change. It does not
apply the production fix, close either bug or constitute a deployable completed
fix. Two new checks are expected to fail against the unchanged route.

The shared fix is to register the old original through
`image_retirement.retire_paths` inside the existing BEGIN IMMEDIATE replacement
transaction, and remove its post-commit online unlink. Preserve compatibility
checks, failed-new-image cleanup, post-commit invalidation and notification.
Existing HTTP assertions expecting immediate old-file deletion must change in
the implementation commit. Update retired-artwork maintenance documentation
there too; originals will join alternates in deferred offline collection.

## New checks

`python/tests/test_original_image_retirement_unit.py` uses only the standard
library. It extracts the production replacement route, failed-write cleanup
helper and retirement helper with AST. It removes route decorators, annotations
and the inner room-notes import to inject dependency doubles. SQLite, commit/
rollback and file operations are real. Authorization, upload decoding, actual
map-repository writes, reconciliation, fog invalidation and notifications are
not integrated application dependencies in these checks.

Run from the repository root:

```bash
python python/tests/test_original_image_retirement_unit.py -v
```

Cases cover consuming a previously selected old path after replacement while
new references read new bytes; injected unlink failure not interrupting update
notification; and precommit failure rolling back the reference and retirement
registration while cleaning the new file. They do not exercise deferred ASGI
FileResponse consumption, a cold fog worker, image decoding or offline collection.

## Executed validation and limits

In the assistant sandbox, this exact standalone test file ran in subprocesses
against staged excerpts of the baseline functions and the proposed two-line
lifecycle change. Baseline: 3 run, 1 passed, 2 errored as expected (missing old
file; injected PermissionError). Proposed: 3 run, all passed. An earlier notebook
invocation hit an already-running event loop; subprocess execution avoids it.
Four additional isolated copied-retirement-helper checks passed using real
SQLite/temp files: commit/read retention, rollback, transaction requirement and
duplicate registration. These are not repository-suite or HTTP results.

The sandbox has Python 3.12 and lacks FastAPI; no full checkout, dependency
installation, Python application suite, browser/live suite or GitHub CI run
was executed. The connector exposes no shell or workflow dispatch/result tool.
The live README.md and HANDOVER.md and relevant source/tests were reviewed.
README.md needs no behavioral change for this test-only intermediate step.
No archive or Patch/ material is added. All new files are below 25,000 bytes;
HANDOVER.md remains a navigation index. Delivery is pending exact-write approval.
