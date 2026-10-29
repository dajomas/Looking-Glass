## Bug 10 implementation candidate: ordered NeDB deletion replay (2026-10-29)

Baseline: features/perplexity at 4ab341e648013066f23a17e95480700315d3d949.
Bug 9 runtime is delivered in a0610c6b6a7af13b7b516a992364b4a38035ccd6 and its
TODO status in 6aade7df9fdf103f0b1096c0f86631a66fcbd177; earlier preparation
wording above is historical. README is a present-tense product guide at blob
20d0d3d3b1d897f576af842762f11133c48a9ab7: preserve its editorial policy without
patch references, bug/fix narratives or historical comparisons. It was reviewed
and needs no change for this parser implementation. Detailed NeDB semantics are
added to docs/foundry-import.md instead. HANDOVER baseline blob is
1dd7ec467f74e2c8df3b2d9e8f3ea0ac324c4135; its complete contents are preserved.

Only _parse_ndjson changes runtime behavior. Replay identified records in order:
replace a live _id, remove it on a truthy $$deleted record, and permit recreation
by a later document. Unknown/repeated deletions do nothing. IDs must be non-empty
strings, without coercion or trimming; malformed IDs raise WallImportError.
Anonymous live records remain independent; anonymous deletions and nonobjects are
ignored. Output is live identified records followed by anonymous records. Updates
keep their dictionary position; deletion/recreation inserts after surviving IDs.
Blank lines, JSON syntax errors, format auto-detection, JSON object/array semantics,
Foundry classification/alignment, UVTT and ZIP policies remain unchanged. The
existing No walls found error applies when direct replay leaves no usable geometry;
ZIP retains its skip-invalid-entry/no-supported-sets behavior. No schema, setting,
dependency, route, migration, deletion or rename. Bugs 2, 11 and 12 remain separate.

Live importer baseline matched f785fcc529fd9636a1e5ab1f74cde263072e7435.
Unchanged wall_model.py, pack_images.py, uvtt_export.py and test_foundry_import.py
were also reconstructed and verified against their live Git blobs before use as
test support. None of those unchanged files is proposed for replacement.

Validation actually executed on Python 3.12.8 / pytest 8.3.5 with plugin autoload
disabled in a temporary focused package:
- New pytest regressions on baseline: 15 failed, 9 passed (0.03 seconds).
- New candidate unittest module: 24 passed (0.003 seconds).
- Candidate focused pytest run: 32 passed, none skipped (0.05 seconds): 24 new
  cases and all eight unchanged existing importer cases.
- Changed importer and new regression module compiled successfully.
The preliminary baseline unittest report counted subtest failure/error events;
use the pytest 15-failed/9-passed result for method-level comparison.

Tests import the complete real parser, wall model, standard UVTT and ZIP helpers.
Empty package initializers and a minimal focused conftest containing the existing
two_room_scene helper avoid unrelated application fixture imports. Repository
conftest/configuration/application initialization was not executed. No AST rewriting,
fake parser, network or persistent DB was used. Coverage includes updates,
deletion/recreation, unknown/repeated deletion, ID case/order, anonymous documents,
truthy/false markers, malformed IDs, syntax errors, public walls/scenes/no-walls,
JSON-array compatibility, UTF-8 BOM and ZIP-contained histories. Existing cases
cover standard UVTT/classification/alignment, not extended portal graphs.

Normal-checkout commands:
PYTHONPATH=python python -m unittest discover -s python/tests -p test_nedb_replay.py
PYTHONPATH=python python -m pytest -q python/tests/test_nedb_replay.py python/tests/test_foundry_import.py
No saved-source DB, broader pack-image suite, full suite, HTTP, browser, live-server
or Python 3.14 deployment acceptance ran. Verify normal import and wall-set selection
with application dependencies before declaring integration/deployment acceptance.

Source bytes and walls already copied to maps are not automatically rewritten.
Explicit reapplication can change wall-set counts/indexes when deleted scenes are
omitted: review the selected set and blank viewers before applying geometry.
No automatic data repair is included; broad malformed-input and finite-value work
remain separate. The README and TODO.md are excluded from proposed changes.

The user explicitly approved two-commit delivery for bug 10 only: this HANDOVER
record first, followed by importer, regression module and import guide together.
Each write requires its own exact-content approval. Runtime implementation remains
pending step 2; TODO item 10 stays open until implementation delivery, when its
actual SHA and remaining acceptance must be recorded. No tests were rerun during
this documentation preparation. No archive or generated Patch/ material is included.

