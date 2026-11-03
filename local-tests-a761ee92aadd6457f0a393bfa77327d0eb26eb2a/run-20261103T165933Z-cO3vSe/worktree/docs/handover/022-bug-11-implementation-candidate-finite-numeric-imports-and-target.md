## Bug 11 implementation candidate: finite numeric imports and target transforms (2026-10-29)

Baseline: features/perplexity at 9713edf7bc4a9fc2c5c772207e330a8287b27fad.
Bug 10 runtime is delivered in be09fef50ea0a3bd1609b9850eab98b9a0061e41 and
its TODO status in this baseline; earlier preparation wording above is historical.
The current README is reviewed and remains a present-tense product guide without
patch references or bug/fix history. No README edit is required for this scoped
candidate; detailed numeric behavior belongs in docs/foundry-import.md. Preserve
the complete HANDOVER baseline d22a3c25e2c57e6710ecb728a8d73a7e34e0e68e.

Numeric helpers reject non-finite converted coordinates, origins and derived
geometry. Explicit dimensions, grids and UVTT scales/sizes must be positive;
padding must be non-negative. Omitted/null optional metadata retains defaults.
Explicit zero/negative required sizes and nonnumeric grid values are rejected.
Finite numeric strings and negative coordinates/offsets remain supported. Numeric
conversion/overflow failures use WallImportError, not a blanket exception handler.
Legacy omission of nonnumeric/zero-length wall coordinates remains unchanged;
structure/type and skip-policy work stays under bug 12. No arbitrary coordinate
cap, schema, dependency, configuration, deletion or rename is introduced.

validated_calibration checks actual target-map scales, offsets and transformed
endpoints. campaigns.apply_walls invokes it BEFORE walls_repo.replace for both
automatic and retained calibration. Direct and saved-source inspections translate
numeric calibration rejection to BadRequest. Complete route modules preserve
unrelated source, signatures, decorators and registration statements. Do not deploy
routes without the corresponding importer/helper implementation.

Measured validation on Python 3.12.8 / pytest 8.3.5 with plugin autoload disabled:
- Final 170 new baseline cases: 158 failed, 12 passed.
- Fresh combined candidate after restoring uploaded implementation and complete
  route artifacts: 202 passed, no failures/errors/skips (0.35 seconds).
- Counts: numeric/parser 154; isolated route-body 16; existing importer 8; NeDB 24.
- All six complete candidate Python files passed py_compile in the fresh rerun.
- Route assembly also verified unchanged source/AST outside the three targeted
  functions and preserved all 49 decorated-function definitions; 12 wiring checks
  passed. The earlier fragment run is not substituted for the combined rerun.
No application tests are claimed rerun merely for this documentation preparation.

The focused tree uses empty package initializers and a minimal conftest containing
the existing two_room_scene helper. Unchanged wall-model, UVTT/ZIP helpers and
existing tests matched pinned live Git blobs. Numeric parser/helper logic is real;
route tests AST-extract bodies from COMPLETE modules and remove annotations and
decorators. DB/repository, permission, request, response/fog and reconciliation
boundaries are doubles. Write-spy ordering is not persistent-DB rollback proof.
No full application imports/registration, HTTP/ASGI, authentication/CSRF, migrated
DB, full suite, extended portal graphs, browser, live listener or Python 3.14
acceptance was executed. No HTTP/DB regression module is included; that coverage
and acceptance remain unfinished and must not be described as passed.

Focused command in a normal checkout after complete delivery:
PYTHONPATH=python python -m pytest -q python/tests/test_import_numbers.py python/tests/test_import_numeric_routes.py python/tests/test_foundry_import.py python/tests/test_nedb_replay.py

Limits: ZIP keeps its per-entry skip policy; a numeric rejection can omit an entry
while accepting usable companions. Actual target/current calibration can make a
finite source unusable on one map. Source bytes, copied walls and bad legacy data
are not automatically repaired. Map-upload partial-wall/source-retention and file
lifecycle behavior are not redesigned. Broader malformed containers/doors are bug 12.

The user explicitly approved four-commit delivery for bug 11 only:
1. HANDOVER documentation.
2. Importer, numeric/parser regression module and import guide.
3. Complete campaigns.py and wall_sources.py replacements.
4. Complete api.py replacement and numeric route-body regression module.
Each write needs its own exact-content approval. The 202-pass result applies to
the COMPLETE final candidate, not separately to intermediate commits. Do not deploy
intermediate states as the completed fix. TODO item 11 remains open until step 4
succeeds; record actual delivered SHAs and pending integration/deployment acceptance
then. No unrelated README/TODO edit, archive or generated Patch/ folder is proposed.

