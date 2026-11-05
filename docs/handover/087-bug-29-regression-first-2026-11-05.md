# Bug 29: regression-first upload write-lock checks (2026-11-05)

## Scope and status

Baseline: 769200b3cd4de242192d2e7a4502ac20c5aeb895 on features/perplexity.
The live branch was rechecked before this exact approval request. Bug 29 remains
open. This is a test-only intermediate step, not the production fix or closure.
No migration, application behavior, TODO status or existing regression changes.

The current upload_image in web/admin/double_reveal.py begins an immediate write
transaction before awaiting asyncio.to_thread(images.store_map_image, ...).
A synchronous competing writer can stall the same admin loop until its SQLite
lock wait ends; this source review is not a live timing reproduction.

## Prepared regression contracts

python/tests/test_double_reveal_upload_lock_web.py uses the existing real-app
HTTP fixture, existing upload helper, real image storage and real SQLite. The
image-store spy tries a separate BEGIN IMMEDIATE with a 200 ms busy timeout.
Only SQLITE_BUSY/SQLITE_LOCKED become a failed probe; other errors propagate.
No production timeout is changed.

- During image processing another writer must acquire and release the lock.
- A competing fog-version update during processing must succeed; the upload
  must then reject its stale stamp with 400 and remove the newly staged file.
- Wrong image dimensions must leave no new file or alternate revision.
- A successful second upload increments the revision and retains the first
  alternate file for the existing offline-retirement workflow.

The first two checks are expected to fail against this baseline; that expected
result has not been executed here. The other two are compatibility guards, not
reported passes. No skip/xfail is added for the expected baseline failures.

## Validation actually performed

The exact prepared test source syntax-compiled under sandbox Python 3.12.8.
FastAPI is unavailable in this sandbox. No application HTTP, browser, live-server,
recovery, full-suite or CI execution occurred. These tests use TestClient and an
independent writer inside the image worker, not two live Uvicorn requests on
one event loop, and do not measure the event-loop stall or deployed latency.

Run in the normal dependency environment from the repository root:

```bash
PYTHONPATH=python python -m pytest -q python/tests/test_double_reveal_upload_lock_web.py python/tests/test_double_reveal_web.py
```

## Implementation and acceptance still required

Stage/validate the owned image before opening the write transaction, then acquire
BEGIN IMMEDIATE and reauthorize management permission, recheck the full stamp
and dimensions against current state, retire any old alternate and install the
new reference atomically. Preserve existing post-commit notifications and error
semantics. Clean up newly owned files after failed rechecks/rollback; review
cancellation while a storage worker is still running rather than assuming the
await stops the worker or that a completed path has reached the coroutine.
Do not weaken or remove the atomic compatibility checks to pass these tests.

Expand regressions for deletion, ownership changes, original-image replacement,
concurrent alternate replacement, transaction/storage failure and cancellation.
Add bounded live same-admin-loop upload/mutation responsiveness coverage with
real SQLite before claiming concurrency acceptance. Review normal-runtime CI
and local evidence and obtain user acceptance before closing bug 29.

README.md and HANDOVER.md were reviewed. README advertises no new protection and
needs no cosmetic change. HANDOVER.md adds only a link to this focused record.
Each proposed file is below 25,000 UTF-8 bytes; historical manifests are unchanged.
The earlier confirmation accidentally bound a placeholder, not these files. No
write was performed with that payload; this exact three-file approval replaces
it. Delivery must be reported only after the approved GitHub write succeeds.
No other branch, archive, Patch/ material or generated-evidence cleanup included.

## Implementation candidate (2026-11-05)

The preceding sections record the regression-first step delivered as
5606e6660728615f318befe2b7c682ceb9062896, also the live implementation baseline.
This section supersedes its production-fix-pending instructions only for the
candidate described here. Bug 29 stays open pending runtime validation and
acceptance. HANDOVER.md already indexes this focused record; its link label
describes the original regression-first step, not an acceptance decision.

Image validation/encoding/storage now runs before BEGIN IMMEDIATE. The initial
permission read captures the storage campaign without retaining a connection
across either upload read or staging. Inside the final transaction checked()
reauthorizes campaign management and validates the full original stamp. A
campaign-id guard and dimension check use the current map row. Retirement,
alternate-reference update and response snapshot remain in the transaction;
no await occurs there. Notifications remain after commit, outside cleanup, so
a notification exception cannot delete committed artwork. No migration or
other route behavior is changed. Already-stale uploads may now stage an image
before rejection; their completed new file is then discarded.

_stage_image coordinates worker/result ownership with a threading lock. A
cancelled await marks the result abandoned; either the caller removes an
already-completed result or the still-running worker removes its late result.
The worker owns no database connection. Cleanup OSError is logged with the path
without masking the original error/cancellation. Such filesystem failures and
process termination can still leave orphan files; this is not crash-atomic
filesystem/database storage or an orphan-collection feature.

Added test_double_reveal_upload_rechecks_web.py: six HTTP recheck cases (fog
version, dimensions, incarnation, ownership, deletion and alternate revision),
HTTP snapshot rollback and post-commit notification fault cases, and a
controlled worker-cancellation case. Existing regression-first tests are
unchanged. These prepared repository tests have not executed in this sandbox.

### Candidate validation and remaining limits

Python 3.12.8 syntax-compiled the replacement upload definition, staging helper
definitions and new test source. An isolated upload-function excerpt harness
used real SQLite and temporary files, with stubbed authorization, snapshots,
notifications and image encoding. Baseline: an independent writer was blocked
and the stale-change attempt did not run. Candidate: nine asserted cases passed
(normal install, stale stamp, dimensions, permission loss, deletion, alternate
revision, campaign change, snapshot rollback and notification failure after
commit). A separate threaded cancellation check passed: cancellation propagated
and the late file was removed. These are extracted-function checks, not the
actual app/schema/HTTP regression suite or deployed latency measurements.
The first cancellation-harness invocation used asyncio.run inside the notebook
loop and failed before running; retrying with the notebook's await completed
the check. No result from that failed invocation is counted as passing.

FastAPI is unavailable here. No application HTTP, browser, live Uvicorn, recovery,
full-suite or CI execution occurred. Real same-admin-loop overlapping requests,
original-image replacement via its real route, repeated cancellation races,
filesystem cleanup failures and storage/commit fault matrices still require
normal-runtime validation. Existing SQLite contention from other synchronous
transactions or external writers is not eliminated by this scoped change.

Run the existing focused command with
python/tests/test_double_reveal_upload_rechecks_web.py added, then the normal
five-suite workflow/local runner. This implementation commit does not use
[skip ci]; the earlier skip request applied to the regression-only commit. No
workflow outcome or GitHub delivery is claimed before it actually occurs.
README.md and HANDOVER.md were reviewed again; the README's user-facing
behavior is unchanged and this already-indexed focused record contains the
implementation decision and limits. No cosmetic index edit or historical
manifest change is needed. No TODO closure, other branch, archive or Patch/.
