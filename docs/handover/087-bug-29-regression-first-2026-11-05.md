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
