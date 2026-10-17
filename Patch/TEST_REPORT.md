# Validation report

## Executed in the packaging environment

- 12 repository/migration pytest cases passed (fresh schema, v1 upgrade,
  idempotent migration, persistence across reconnect, same-campaign deduplication,
  changed bytes, campaign isolation, filename normalization, cascade deletion,
  preservation of copied map walls, monotonic IDs and transaction rollback).
- All bundled Python files parsed successfully with ast.parse.
- node --check passed for static/js/wall_source_library.js.
- The four modified executable/template baselines were verified against the Git
  blob hashes read from the exact target commit in the preceding inspection:
  db.py, admin/api.py, admin/campaigns.py, and admin/map_editor.html.
- README baseline matched its pinned Git blob hash. The remaining updated docs
  preserve the project-file baseline and append the relevant feature sections.
- Supplied maps.db structure inspected: 13 newline-delimited JSON scene
  records with walls. Scene names/counts are in sample-database-summary.json.
  This is structural input inspection, not a full-app import/render test.

## Not executed here

FastAPI installed in this environment: False.
The complete application suite, new HTTP workflow test and browser/live-viewer
checks were not run here. These are supplied validation steps, not claimed passes.
A successful syntax check is not proof of working authentication or rendering.

## Required checks in the complete repository

```bash
.venv/bin/pip install -r requirements-dev.txt
cd python
../.venv/bin/python -m pytest -q
```

The new HTTP regression test covers a multi-set map upload with no automatic
first-set application, non-first scene import, reuse on a differently-sized map,
independent calibration, same-source deduplication, keeping existing alignment,
missing/negative/out-of-range indices, CSRF, cross-campaign access, another DM's
access, absence on the viewer app, invalid input, and deletion preserving walls.

## Manual browser acceptance

1. Create a map with the supplied maps.db; confirm it has no auto-applied walls.
2. Under Saved wall sources, select the source and one of its 13 wall sets.
3. Apply it; verify wall overlay, alignment and exact player preview.
4. Create another image-only map, select the same source and a different set.
5. Repeat with the same wall set on both maps and verify independent alignment.
6. Restart the server; verify the source is still available without re-uploading.
7. Delete the source; verify both maps retain their already-applied walls.
8. Check a second DM cannot list/inspect/apply the first DM's campaign sources.
9. With an assigned live viewer, apply a set and confirm refresh notification.
10. Test file-upload errors, an empty library, refresh from another tab, cancelled
    replacement/deletion confirmations, and keyboard-accessible controls.
