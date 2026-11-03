### 10. NeDB imports resurrect deleted walls/scenes
- [x] Implementation delivered on `features/perplexity`; integration/deployment acceptance pending.
- Fix commit: `be09fef50ea0a3bd1609b9850eab98b9a0061e41`.
- HANDOVER commit: `cf5b42d5041958514be5156578aa460f6146e407`.
- Baseline: `4ab341e648013066f23a17e95480700315d3d949`. The user separately
  approved ordered replay and documentation-first, two-commit delivery for bug 10.
- Validation during preparation on Python 3.12.8 / pytest 8.3.5 with plugin
  autoload disabled: new baseline regressions produced 15 failures and 9 passes;
  the candidate focused run passed all 32 cases, none skipped (24 new regressions
  and eight existing importer tests). The new unittest module also passed all
  24 cases. Both changed/new Python files compiled. Tests used the complete real
  parser, wall model, standard UVTT and ZIP helpers in a focused temporary package
  with empty initializers and a minimal conftest containing the existing scene
  helper. Repository conftest/application initialization was not executed.
  No saved-source DB, broader pack-image suite, full suite, HTTP, browser,
  live-server or Python 3.14 acceptance ran. No tests were rerun during GitHub
  delivery or this TODO-only update. See HANDOVER.md for commands and limits.
- Problem: deletion records were discarded before latest-record resolution,
  retaining earlier walls/scenes that the source history had deleted.
- Solution: `_parse_ndjson()` replays identified records in order: replace live
  IDs, remove IDs on truthy `$$deleted`, and permit later recreation. Require
  non-empty string IDs without coercion/trimming; malformed IDs raise
  WallImportError. Retain independent anonymous live documents and ignore
  anonymous deletions/nonobjects. Identified output precedes anonymous output;
  updates retain position, while deletion/recreation inserts after surviving IDs.
- Test: update/delete/recreate sequences, absent/repeated deletions, ID case/order,
  anonymous records, truthy/false markers, malformed IDs, syntax errors, public
  wall/scene/no-walls imports, JSON-array compatibility, UTF-8 BOM and ZIP histories.
- Limits: JSON object/array imports keep their separate semantics. ZIP retains
  its existing skip-invalid-entry/no-supported-sets policy. No automatic rewrite
  of saved source bytes or copied map walls occurs. Reapplication can change
  wall-set counts/indexes when deleted scenes disappear; review the selected
  wall set and blank viewers before explicitly applying geometry. No schema,
  configuration, dependency or route change. Bugs 2, 11 and 12 remain separate.
- Remaining acceptance: run the focused modules with normal application
  dependencies, verify NeDB/ZIP imports and saved-source wall-set selection,
  then validate on the Python 3.14 deployment before declaring acceptance complete.

