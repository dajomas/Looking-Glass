# Bug 16: finite manual calibration (2026-11-03)

## Scope and decisions

Implementation candidate for bug 16 on `features/perplexity`; acceptance pending.
The request model rejects NaN and infinities for both offsets and scales while
retaining the existing positive scale ceiling of 100. Negative finite offsets
remain supported. The route reuses `foundry_import.validated_calibration` with
a WallSet of all existing map walls and the explicitly requested Calibration.
That rejects both subtraction and multiplication overflow before the SQL update,
fog-cache invalidation, payload reconciliation or notifications.

BEGIN IMMEDIATE serializes the source-wall read, transform validation and update.
WallImportError is normalized to BadRequest (400); invalid request fields use
the existing 422 validation response. Existing success behavior and dependencies
are retained; notifications still occur after commit. No migration or historical
data repair is included; no arbitrary finite-coordinate magnitude cap is added.

## File-size split and integration

The original `web/admin/api.py` was 25,297 bytes. CalibrationIn and its endpoint
were extracted into `web/admin/calibration.py`; api.py registers that route with
its existing `_map_payload` callback. The public URL, route position and
`api.CalibrationIn` / `api.calibration` names remain available. The application
factory continues to include the same api router, so no template, JavaScript,
packaging or application-factory change is needed. Both production files are
below 25,000 bytes after the split. Other routes are unchanged.

The relevant API section is updated. README.md was reviewed and needs no change:
it does not specify the manual-calibration numeric contract. HANDOVER.md links
this record. Original split manifests and historical audit findings are unchanged.

## Validation performed

In an isolated Python 3.12.8 / Pydantic 2.11.4 sandbox, 17 pytest cases were run
with --noconftest. The baseline gave 10 failures and 7 passes; the candidate gave
17 passes. These use real Pydantic/SQLite, AST-loaded request/route/repository
code, extracted import-validation logic and simplified wall data classes, with
authorization, wall loading, rendering and notification doubles. They are not
full application, HTTP, migrated-database or concurrent-server acceptance.
The new module and both test files were parsed for Python syntax.

## Pending validation and limitations

28 full-app HTTP cases were prepared but not executed. They check rejection on
wall-free and walled maps, unchanged persistent state and preview bytes, no cache
invalidation/notification on rejection, valid negative offsets, version changes,
CSRF and ownership checks. The normal Python 3.14 suite, actual FastAPI route
registration, rendering, browser/live suites, packaging and CI remain unverified.
The split is source-reviewed, not claimed fully behaviorally validated. Run CI
without a skip marker and review all failures before accepting or closing bug 16.
No other outstanding bug is fixed by this change.
