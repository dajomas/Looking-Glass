# Bug 15: route retirement and CLI ownership (2026-10-31)

Step-4 preparation baseline: dajomas/Looking-Glass, features/perplexity,
e94304cbc2efb5f0dd5b88455f4826857c97e34c, verified as live tip.
This active record consolidates the split-delivery history below. Its current
status supersedes earlier intermediate/pending runtime descriptions, not their
evidence limits. Record 072 and all historical split manifests stay unchanged.

## Status and scope

The step-4 candidate completes the four-stage implementation once delivered.
Bug 15 remains OPEN pending application validation, exact-source CI review and
user acceptance. Bugs 2, 13 and 14 remain accepted and closed with their existing
evidence limits. Implementation delivery is not a new test result or closure.

Map/campaign deletion and HTTP campaign restore capture original and alternate
paths before removal, inside IMMEDIATE write transactions. Restore registers
paths after preview/inspection/recovery creation and before replacing rows.
Post-commit fog invalidation remains; old original files are not unlinked.
Alternate upload registers its previous path after stamp/dimension validation
and before the upsert in its existing transaction. First uploads register no
old alternate. Registration rolls back with database mutations; existing
exceptional new-file cleanup and after-commit notification contracts remain.

Step 4 changes only CLI imports/main plus current documentation. ExitStack holds
storage_use before normal server setup through asyncio.run and executor shutdown.
Only lock-acquisition RuntimeError becomes CLI refusal; server exceptions still
propagate. No startup/context/account-command collection is introduced. Direct
ASGI/server/service launchers still need explicit ownership or a complete stop.
Use a single normal serving process on local POSIX storage, not shared-cache
multi-server or distributed storage. Collection refuses without fcntl.

Original replacement's immediate unlink, failed-new-image cleanup and general
cancellation/crash/power-loss windows are not redesigned. Collector executable
code, routes and every existing test/workflow are unchanged by step 4. The
helper's existing ownership requirement remains valid; no cosmetic helper edit
is needed. See docs/image-retirement.md for maintenance and unsupported readers.
Only registered paths are collected; no arbitrary old orphan scan or adoption.

## Delivery and evidence chronology

- Foundation: 901509e39acd1becec3ecddcd89372bfee63e954. Helper and isolated
  real-SQLite/flock suite; historical Python 3.12.8 result: 14 passed in 0.13s.
  This is not application migration, HTTP, live-serving or current-source proof.
- Split step 1: 71b83c049aa1205f3f7516584d5ea1ebb5a28da7. Corrected HTTP/CLI
  desired-behavior contracts; expected red before corresponding implementation.
  Modules compiled during preparation, but no baseline runtime failure inventory
  or HTTP/CLI pytest execution was established. No xfail/skips/exclusions.
- Step 2: 5e2f64a21062a9f73d5d8a7a38554f1b5024ac6a. Deletion/restore
  retirement. Source review and earlier candidate compilation only, no new tests
  or CI review. Failed restore new-file cleanup and original replacement stayed
  unchanged. Runtime diff was verified after delivery.
- Step 3: e94304cbc2efb5f0dd5b88455f4826857c97e34c. Alternate retirement.
  Baseline/candidate compiled under Python 3.12.8; AST changed only upload_image
  among existing functions/classes. Delivered blob matched candidate
  c5c2484b7b6eabd1f460506691c641be8f478bd8. No application/pytest/CI result.
- Step 4 preparation: reconstructed CLI matched live blob
  ce30da47a2752b5a82f23b57d565ebb3c8c0ec30. Baseline/candidate full modules
  compiled under Python 3.12.8; AST changed only main among existing functions.
  Candidate CLI blob: 30217442f0e9a62662c2474beabd0028151c7314. No pytest,
  application/HTTP, manual/browser/live execution or new CI review was performed.
  FastAPI is unavailable in this preparation sandbox.

## Regression contracts and pending validation

Tests preserve exact selected raw bytes, ZIP artwork bytes, alternate/original
composite pixels and hidden fog pixels. Exact-path barriers pause readers before
opening; a writer reaches post-commit invalidation while they pause. TestClient
readers explicitly model shared ownership, while separate actual CLI-dispatch
tests check serving/startup exclusion, exception release and executor shutdown.
These controlled dependencies are not live Uvicorn proof. Retry checks require
operation-specific success, DB changes, exact candidates, file bytes, collection
and unrelated-state preservation, not a generic redirect. Coverage includes
no-alternate maps, repeated distinct replacements, wrong confirmations and stale
uploads. Foundation checks retain bounded child readiness/termination/reaping.

In a normal checkout, execute and record the actual tested SHA and results:

```bash
PYTHONPATH=python python -m pytest -q \
  python/tests/test_image_retirement.py \
  python/tests/test_image_retirement_cli.py \
  python/tests/test_image_retirement_web.py \
  python/tests/test_image_database_failures.py \
  python/tests/test_double_reveal.py \
  python/tests/test_double_reveal_web.py \
  python/tests/test_campaign_backup.py \
  python/tests/test_campaign_backup_inspection_web.py \
  python/tests/test_fog_response_race.py
```

Review the unchanged five-suite CI against the actual delivered SHA and perform
isolated manual deletion/restore/replacement plus stopped-maintenance checks.
Do not infer passes from compilation or earlier green runs, or acceptance from
delivery. Never weaken assertions, skip or exclude failures to obtain green.
Current README/HANDOVER were reviewed; this commit adds the maintenance overview
and updates the existing pointer. Preserve filename capitalization, historical
records/manifests, dependencies, migrations and other bugs. No archive, Patch/
material, merge or other-branch write.
