# Bug 15: regression-first route and CLI contracts (2026-10-31)

Split delivery step 1 of 4. Baseline: dajomas/Looking-Glass,
features/perplexity, 901509e39acd1becec3ecddcd89372bfee63e954,
verified live before this exact-write proposal.

## Scope and status

Add only the corrected HTTP/CLI integration regressions, this evidence record
and one short HANDOVER pointer. Existing routes, CLI and retirement helper are
unchanged. Bug 15 remains open; Bugs 2, 13 and 14 remain accepted and closed.
This is an intentionally regression-first intermediate, not a completed fix.

The new desired-behavior contracts are expected red until production retirement
and serving ownership are integrated in steps 2-4. No baseline execution of
these tests has established a failure inventory yet. They are discovered by
the existing main workflow; no xfail, skip, weakened assertion or exclusion
hides intermediate failures. Preserve test_image_database_failures.py and
the foundation test_image_retirement.py unchanged.

## Review corrections preserved

Reader tests verify exact selected raw bytes, exact backup artwork entries,
visible alternate/original composite pixels and hidden-area fog pixels. The
fixture enables true artwork in a revealed room so cold fog rendering must
read the alternate. Barriers match the exact old path, not any Image.open.
A separate mutation reaches post-commit invalidation while the reader pauses;
release/join cleanup uses finally blocks. TestClient/direct service readers
explicitly model serving ownership; separate tests exercise actual CLI dispatch.

Retry checks require operation-specific success, database changes, exact
retirement candidates, retained bytes, successful collection and unrelated
campaign preservation, rather than accepting a generic 303. Coverage includes
a no-alternate map, repeated distinct replacements, wrong confirmations and
stale-upload rejection. CLI tests check serving exclusion, startup refusal,
server exception propagation/release and ownership through executor shutdown.
The previously committed foundation retains bounded child readiness/cleanup.

## Evidence and operational warning

These exact new Python modules were compiled during the earlier full-payload
assembly under Python 3.12.8. That is syntax evidence, not pytest or application
execution. No HTTP/CLI/browser/live test or new CI review was executed for this
proposal. FastAPI was unavailable in that preparation environment. The earlier
foundation result of 14 passed in 0.13 seconds is historical isolated evidence,
not a result for these integration tests or this proposed commit.

The current CLI still does not acquire storage_use. Stop ALL serving/direct
ASGI/service/backup readers before offline collection. Do not interpret the
manual lock in TestClient tests as proof of production CLI coordination.

## Remaining approved delivery sequence

2. Campaign/map deletion and restore retirement, with corresponding docs.
3. Alternate-artwork replacement retirement, with corresponding docs.
4. CLI ownership and final maintenance documentation.

Each step requires its own exact-action approval. Update this focused record
as implementation and actual evidence arrive; keep Bug 15 unchecked pending
acceptance. README and HANDOVER match the previously reviewed live blobs;
README remains accurate for this test-only step and needs no cosmetic edit.
No migrations, dependencies, workflows, historical records/manifests, archives,
Patch/ material or other branches are changed.

## Step 2: map/campaign removal and restore retirement

Step 1 was delivered in 71b83c049aa1205f3f7516584d5ea1ebb5a28da7,
verified as the live tip before preparing step 2. This section updates the
current partial-integration status; the step-1 statements above retain their
historical context and execution limits.

The proposed step 2 registers original and alternate paths transactionally
for map deletion, campaign deletion and HTTP campaign restore. Map/campaign
deletion begins IMMEDIATE before current authorization and path capture.
Restore uses its existing IMMEDIATE transaction and captures paths after
preview/inspection/recovery creation, before restore removes the old rows.
On success, fog invalidation remains but old original files are not unlinked.
Registration and removals roll back together. Existing cleanup of newly
created restore files on failure is unchanged.

Original-image replacement, failed-upload cleanup, alternate upload, CLI,
retirement helper, all existing tests and the five-suite workflow are unchanged.
Alternate replacement retirement remains step 3; CLI ownership remains step 4.
Bug 15 is open and this partial delivery is not acceptance. Bugs 2, 13 and 14
remain closed. New docs/image-retirement.md describes this precise stage and
the requirement to stop ALL readers before collection. No current normal CLI
server-lock guarantee is claimed. No arbitrary untracked-file adoption occurs.

Validation: source review against live campaigns.py blob
ac251388575d9e5c3d3a14c19ad48f222c1c6a94. This campaigns.py candidate
was compiled during earlier complete-payload assembly; that is historical
syntax evidence, not a new run. No new compilation, pytest, application/HTTP,
manual execution or CI review was performed for step-2 preparation. Existing
regression expectations are preserved, not reported as passing. Execute the
map/campaign/restore, rollback and paused-reader contracts in a normal checkout
and record its exact source SHA and actual results. Alternate/CLI cases remain
expected red until later steps; no failures are hidden or excluded.

README remains the reviewed blob 592cd720793432e2add533717c91e7b41f2930a3
and its overview needs no cosmetic edit for this partial stage. HANDOVER's
existing record-073 pointer and runtime-pending label remain accurate; no new
index edit is needed. Update only the individual Bug 15 backlog, not its split
manifest. No historical record, dependency, migration, archive or other branch
is changed.
