### 11. Wall imports accept non-finite coordinates
- [x] Implementation delivered on `features/perplexity`; integration/deployment acceptance pending.
- Final implementation commit: `c21c0d1a299449eadf93ec8188afe6caf799654d`.
- Importer, numeric tests and guide: `f03520b8ac76a2155a3af3eef4fc0c878acb71b6`.
- Apply/saved-source routes: `0f537c9b5b2e4881997da3ccb18e05543009b5f3`.
- HANDOVER preparation: `df9ad36b369b77aa2e896dd56dff95fb45d6fb7c`.
- Baseline: `9713edf7bc4a9fc2c5c772207e330a8287b27fad`. The user separately
  approved four-commit delivery for bug 11 only; all four steps are delivered.
- Validation: the fresh complete-candidate run immediately before step 4 approval
  passed all 202 cases, none skipped, in 0.26 seconds on Python 3.12.8:
  154 numeric/parser cases, 16 isolated route-body cases, eight existing importer
  cases and 24 NeDB replay cases. All six candidate Python files compiled.
  Earlier baseline regressions produced 158 failures and 12 passes across the
  170 new cases. No tests were rerun after the GitHub writes or during this
  documentation-only preparation.
- Test scope: the focused temporary package uses empty initializers and a minimal
  conftest with the existing scene helper; unchanged support modules and existing
  regression modules matched live Git blobs. Parser/calibration logic is real.
  Route tests AST-load actual bodies from complete modules, removing decorators
  and annotations; DB/repository, permission, request/response, fog and reconciliation
  boundaries are doubles. Write-spy ordering is not persistent-DB rollback proof.
- Problem: float conversion accepts NaN/infinity; unchecked source or target
  arithmetic can fail later or produce unusable geometry/calibration.
- Solution: reject non-finite converted coordinates, origins and derived geometry;
  require positive explicit dimensions/grid scales and non-negative padding.
  Validate actual automatic or retained target calibration and transformed endpoints
  before wall replacement. Both inspection paths normalize numeric rejection to
  BadRequest. Omitted/null optional metadata, finite numeric strings and negative
  coordinates/offsets remain supported; no paired-dimension restriction was added.
- Limits: ZIP retains per-entry skipping; invalid entries can be omitted while
  usable companions import. Existing zero-length/nonnumeric wall omission remains.
  No automatic repair of saved source bytes, copied walls or bad legacy data.
  No schema, dependency or configuration change. Broader malformed containers/doors
  remain bug 12; upload partial-wall/source-retention and file lifecycle are separate.
- Remaining acceptance: rerun the four focused modules in a normal checkout, add
  and run real HTTP/DB inspection/import/saved-source cases, and verify unchanged
  persistent geometry on rejection for automatic and retained calibration.
  Application initialization/registration, authentication/CSRF, migrated DB, full
  suite, extended portal graphs, browser, live-server and Python 3.14 acceptance
  were not executed and remain pending. See HANDOVER.md for the focused command.

