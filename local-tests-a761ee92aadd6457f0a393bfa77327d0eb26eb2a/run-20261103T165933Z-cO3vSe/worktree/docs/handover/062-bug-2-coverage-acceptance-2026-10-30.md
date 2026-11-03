# Bug 2: coverage audit and acceptance work (2026-10-30)

Baseline: features/perplexity c508a2dffc6be2785a5a44867b7b192cae65070a.

## Step 1: verified green integration evidence

Completed for source d5fea76382118277a16ac0c2fd15a7e67508bfe8, run 41124059137, attempt 1. Committed ci-results-41124059137-attempt-1/run.json records success for Python/HTTP, JavaScript regressions, Browser/mocked HTTP, Live Uvicorn and Recovery; each report-validation gate succeeded. Evidence is retained at c508a2dffc6be2785a5a44867b7b192cae65070a. Conditional matrix steps marked skipped are not skipped test cases. This is not evidence for newly added tests or later dependency/source changes.

The current requirements-dev.txt contains httpx2>=2.16.0, as requested by the user; this increment preserves it. No warning-removal or dependency-validation claim is inferred for a source other than the tested SHA.

## Step 2: targeted coverage audit

Existing coverage reviewed:

- test_room_note_archive_web.py exercises real geometry imports/read reconciliation, exact custom text, other-map isolation, imported-name release, explicit recovery, auth/CSRF, stale contexts, replacement retention and injected recovery rollback.
- test_room_geometry_release.py exercises split/merge/anchor/outside variants, renumbering and actual wall add/remove, but several assertions check assignment release rather than exact archived content.
- test_room_notes.py covers payload transaction prerequisites and basic generation rollback, but not every insert/update/delete/move combination.
- Existing backup, duplication and browser modules were delivered and executed during previous reviewed integration runs. They are complementary to, not replacements for, schema-18 upgrade and reconciliation savepoint checks.

New test_room_note_retention_invariants.py supplies 11 parameterized cases: schema17 upgrade/idempotency, version18-record failure/retry, committed/rolled-back generation mutation sequences, five synthetic geometry variants with exact archive/provenance checks, and two reconciliation partial-failure cases. Real SQLite/migration runner, triggers and services are used. Simulated alignment means changed label masks, not an end-to-end calibration route; existing real-geometry HTTP coverage must remain. Migration failure injection is not process-kill/disk-full coverage. Reconciliation catches failure inside an outer transaction and checks preservation of both all notes and unrelated outer work, then retries after removing the fault.

Validation of this increment: source review only. No collection, new tests, full suite, browser, live server or deployment exercise was executed/verified here. Tests must execute after delivery; their presence is not a passing result. Run:

```bash
PYTHONPATH=python python -m pytest -v -ra python/tests/test_room_note_retention_invariants.py
```

Then run both workflows for the delivered SHA. No skips/exclusions, production/schema changes or dependencies are introduced. Keep Bug 2 open until new evidence is reviewed.

## Step 3: documentation reconciliation

Corrected docs/room-note-recovery.md's obsolete statement that portability is not implemented. It now distinguishes implemented/tested portability from pending final acceptance, explains ownership/history/copy behavior, and documents the existing validation error envelope. README.md and HANDOVER.md were reviewed; no cosmetic changes are made. Broader README/usage/API cross-link integration and final status/index updates remain for the closure commit after new tests and acceptance. Earlier dated handover records remain historical and are not rewritten as current status.

## Step 4: disposable upgrade/recovery acceptance (not executed)

Use an isolated copy of a genuine schema17 installation, never the only copy of valuable data. Stop that source before making a complete database-and-image backup. Preserve the original unchanged; configure separate disposable storage, cache, ports and credentials for the upgraded copy. Disable external integrations in the disposable configuration. Do not run source and copy against shared writable paths. Never attempt a schema downgrade on the upgraded database; rollback means restoring the complete stopped pre-upgrade copy with its matching application version.

Record source/target application SHAs, source schema, environment, setup steps and results without credentials or private note text. Verify:

1. Before upgrade, record a custom room name and Markdown including whitespace/Unicode, an unaffected room and another map; retain a known player image/fog state.
2. Start the disposable copy with the candidate application. Confirm schema upgrade succeeds, saved names/text/revisions persist, and a second startup does not repeat the migration.
3. With the player screen blanked before changing boundaries, split/merge or realign the affected room. Geometry changes can legitimately change fog replay; do not attribute those effects to note recovery. Confirm old custom content is retained, imported-name assignment is released and unrelated room/map edits remain intact.
4. Open Retained notes, inspect provenance, select a current interior and cancel recovery once. Then confirm deliberate recovery. Verify exact recovered text and retained source archive. For nonempty targets require replacement confirmation and retain the previous target too.
5. Capture player state/pixels immediately before and after note recovery with geometry fixed. Note-only recovery must not change fog, active map or player output. Try saving from a previously opened stale editor; it must not overwrite recovered text.
6. Export a campaign ZIP and restore into a disposable target using its normal preview/confirmation and safety backup. Verify archives, text and historical provenance; old editor context must be stale after restore. Saved fog restore may legitimately change player state as part of explicit campaign restore.
7. Clean-copy map and campaign; verify independent artwork, retained detached archives, no activation, fresh map identity, fully fogged start and unchanged source/viewer state.
8. Restart the disposable candidate and verify retained/recovered content survives. Record failures and clean up only the explicitly isolated test resources.

This checklist is a procedure, not evidence that it ran. A green general container/live job does not prove this exact schema17 campaign exercise. Final acceptance needs a recorded execution or an explicit user-approved scope/deferment decision. Do not remove development warnings or mark the Bug 2 TODO closed merely because this document exists.
