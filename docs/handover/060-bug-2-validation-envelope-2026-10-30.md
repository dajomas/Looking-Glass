# Bug 2: recovery validation response assertions (2026-10-30)

Prepared against features/perplexity 974383bbfda810cd5e8444687cd839c27ad04a83.

The shared RequestValidationError handler in python/looking_glass/web/errors.py deliberately returns HTTP 422 with {"ok": false, "error": "field: message"}, not FastAPI's default detail array. RoomRecoveryIn.overwrite remains a strict boolean. The three parameterized rejection cases for 1, "true" and null already returned 422 in focused run 41099334945 against 2a6b53b26f14c1e81cac4ee20f39cd0a5976d58b; the assertion then failed with KeyError: detail.

The targeted test now checks JSON content type, ok=false, a string error prefixed with overwrite:, unchanged database state and an intact source archive. It does not depend on the exact dependency-generated message. No production handler/model changes, coercion, skips, exclusions, workflow changes or unrelated test fixes are included.

README.md and HANDOVER.md were reviewed. README.md requires no change for this test-only correction. HANDOVER.md links this record. Historical records, evidence collections and reconstruction manifests are unchanged.

Validation: source and previously committed failure evidence were reviewed; no pytest collection or test execution was performed for this correction. Run from the repository root:

```bash
PYTHONPATH=python python -m pytest -v python/tests/test_room_note_recovery_web.py -k recovery_overwrite_requires_a_json_boolean
PYTHONPATH=python python -m pytest -v python/tests/test_room_note_recovery_web.py
```

Then inspect both workflows for the new commit SHA. No passing result is claimed. Bug 2 stays open: route-introspection, transaction-fixture, browser collection and regular-suite legacy-backup failures remain separate work, as do broader coverage and acceptance. The previous focused run's 129 passes and five failures are historical evidence, not results for this fix.

## Follow-up: six local failures (2026-10-30)

Prepared against live branch 0b11de10351e240312416ebce0242aa73dfa5a47. The supplied local log reports 1225 passed, six failed and 29 subtests passed. The previous validation-envelope correction passes; these are different failures, not a reason to relax API validation.

This test-only follow-up changes four modules:

- test_double_reveal.py removes the archive table and map note-generation column when constructing simulated schema-15/16 ZIPs. It retains strict production rejection of mismatched schemas and now checks restored map count, empty archives and foreign keys as well as absent alternate artwork metadata.
- test_room_notes_controls.py explicitly begins the transaction required by payload(), preserving migration, content clearing, limits and cascade assertions.
- test_room_note_recovery_web.py records real registration into each fresh archive router to check unique router identity and exactly one definition per expected method/path. Each admin app's generated OpenAPI must include both endpoints; anonymous HTTP requests must reach their authorization guard. The viewer app must neither invoke archive registration nor expose archive paths in OpenAPI or HTTP. This avoids relying on a flat app.routes representation, without replacing actual registration or weakening viewer isolation.
- test_scrying_glass_web.py explicitly supplies a disabled settings section through a function-scoped autouse fixture before app creation and raises if a catalog fetch is attempted. Local config.yaml and credentials are not changed. Existing auth, CSRF, viewer isolation, stale revision and mocked verified-access assertions remain.

No production files, migrations, workflow exclusions, evidence files or new skips are included. The pre-existing FastAPI importorskip is unchanged. README.md and HANDOVER.md were reviewed again; README needs no test-only update, and the existing handover index link already points to this record. Earlier sections above describe the previous increment and remain historical.

Validation for this follow-up is source review only: no pytest collection, application tests, full suite, browser run or new CI result was executed/verified here. The six failures are targeted, not claimed resolved by a passing run. From the repository root, run:

```bash
PYTHONPATH=python python -m pytest -v -ra python/tests/test_double_reveal.py python/tests/test_room_notes_controls.py python/tests/test_room_note_recovery_web.py python/tests/test_scrying_glass_web.py
```

Then rerun the full Python/HTTP selection and inspect both workflows for the delivered SHA. The separate browser conftest import collision is not included in these six local failures and remains open, alongside broader Bug 2 coverage/deployment acceptance. No archive was requested; no archive-only Patch/ material is committed.
