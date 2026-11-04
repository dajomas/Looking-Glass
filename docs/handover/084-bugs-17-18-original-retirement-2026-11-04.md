# Bugs 17/18: original-image replacement retirement

## Implementation and decisions

Prepared against the live features/perplexity branch after regression-first
commit f393128a07bc983405dc2f91984bae4ec9ef03fa. This proposed commit contains
the combined production change, not another test-only intermediate step.
Delivery awaits exact-write approval; no acceptance or CI success is claimed.

In web/admin/campaigns.py, replace_image registers the superseded original via
image_retirement.retire_paths after the locked compatibility recheck and before
maps_repo.replace_image. Registration, the new reference and room-note
reconciliation share the existing BEGIN IMMEDIATE transaction. Rollback retains
the original reference and rolls back registration. The existing failed-new-file
cleanup helper remains unchanged. No migration or new cleanup mechanism is added.

Remove the post-commit old-original delete_map_image call. Retaining old bytes
prevents this replacement route from unlinking paths selected by in-flight
readers (bug 17), and removes old-file unlink failure from the path to fog
invalidation and viewer notification (bug 18). This does not guarantee delivery
if invalidation or notification itself fails, and does not change other routes.

Existing compatibility and database-failure HTTP tests now expect retention and
registration instead of immediate removal, while preserving their byte, state,
rollback, authorization, compatibility and notification assertions.
Retired-artwork maintenance documents original replacement and offline cleanup.
README.md was reviewed: its existing retirement summary remains accurate and
links the expanded maintenance guide; no unrelated README edits were made.
HANDOVER.md links this focused record; historical records remain unchanged.

## Validation and unfinished work

The earlier regression-first sandbox results are recorded in record 083:
3 isolated route checks passed against staged proposed-function excerpts;
baseline excerpts produced the two expected errors. Four separate retirement/
SQLite checks passed. These are not full-checkout, HTTP or CI-suite results.
No new suite execution is claimed for this implementation preparation.

The live .github/workflows/integration-tests.yml was read. It configures pushes
to features/perplexity to start five checks: Python / HTTP, JavaScript,
Browser / mocked HTTP, Live Uvicorn and Recovery. No workflow edit is needed.
An approved push uses that trigger; actual scheduling, run IDs and results must
be checked independently. The connector exposes no workflow dispatch/result or
shell tool. The sandbox lacks FastAPI and does not contain a full checkout;
the full suite has not run here. Verify all five jobs and their evidence before
accepting these bugs as closed. Deferred FileResponse/cold-render race coverage
and original-replacement offline-collection integration remain unverified.

Superseded originals now consume disk until explicit coordinated collection.
Stop all readers and use the same installation configuration as documented.
Uncoordinated readers, external unlinks, process termination/new-file orphan
windows and power-loss durability are not redesigned. No archive or Patch/
folder is delivered, and no other branches are modified.
