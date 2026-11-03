# Bug 15: retirement foundation and corrected test review (2026-10-31)

Baseline: dajomas/Looking-Glass, features/perplexity,
4dc97278529edd12930c73b0d3c90a3d9f96aacf, verified live before preparation.

## This proposed write

Install only the retirement helper, its isolated regression suite and this index
pointer. No existing route or CLI integration is delivered here. Bug 15 remains
open; this is not a completed runtime fix. Bugs 2, 13 and 14 remain accepted and
closed with their recorded evidence limits. README.md and HANDOVER.md were read
live; README remains accurate and needs no cosmetic edit for this foundation.

The helper transactionally records known old paths in installation-local SQLite
bookkeeping, created on first use with transactional DDL. It does not change
portable backup schema or applied migrations. Collection is explicit and offline,
reference-checks both image tables under BEGIN IMMEDIATE and excludes arbitrary
untracked files. Invalid paths, symlinks, active references and failed unlinks
remain queued. Missing paths make retry idempotent after an unlink/commit failure.

IMPORTANT: this commit does not make existing servers acquire the shared lock.
Stop ALL servers, direct ASGI/service/backup readers and older versions before
collection. --confirm-stopped acknowledges that responsibility, not automatic
reader detection. Local POSIX flock is required for collection; unsupported
platforms refuse it. Do not remove/replace the lock inode or storage while in use.
External filesystem mutation and distributed/shared-cache deployments are not
supported. No startup/context-construction collection is installed.

## Review findings 1-6

Corrected HTTP and CLI candidate tests were authored separately: exact selected
artwork bytes and composite/fog pixels; exact ZIP artwork bytes; operation-specific
retry success plus state/retirement/collection checks; actual CLI dispatch and
executor-shutdown locking checks; exact-path reader barriers and post-commit
ordering; unrelated campaign and no-alternate-map controls, repeated distinct
alternate replacements, confirmation and stale-stamp rejection checks.
Those candidate files and their corresponding route/CLI integration are NOT in
this first foundation write and need separate exact-content approval. Do not
claim their coverage is installed or executed. The full runtime fix is unfinished.

The isolated subprocess test now has bounded readiness polling and
terminate/kill/communicate cleanup with readiness-failure diagnostics, replacing
the unbounded stdout.readline wait. Existing assertions are not skipped or
weakened; python/tests/test_image_database_failures.py remains unchanged.

## Executed validation and next work

Exact foundation source compilation and isolated pytest: Python 3.12.8 Linux
sandbox, 14 passed in 0.13 seconds. Tests use a small real-SQLite fixture, not
application migrations or FastAPI. They cover transaction rollback, deduplication,
references, containment, unlink retry, selected/open readers, cross-process locks,
exception release and collector precommit-failure retry.

HTTP/CLI candidates were compiled only. FastAPI is unavailable in this sandbox.
No application/HTTP/live/browser execution, current-source CI evidence or user
acceptance was established. No new baseline application reproduction was run.
Prior all-green CI and Bug 14 manual acceptance do not validate this candidate.

Next: obtain separate approval for the corrected application tests and production
route/CLI wiring, update this record and the individual backlog in that commit,
then execute normal-checkout focused suites and the unchanged five-suite workflow.
No historical split manifests, unrelated bugs, dependencies, archives, Patch/
material, workflows or other branches are changed by this foundation write.
