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
