## Step 6: duplication

Run `PYTHONPATH=python python -m unittest discover -s python/tests -p test_duplication.py -v`.
Service regressions cover campaign link remapping and reset, internal single-map
links, external link detachment, independent image storage, invalid inputs,
missing-image rollback and partial-copy file cleanup.

Target-installation acceptance (not executed in patch environment):
1. Duplicate a live campaign with revealed rooms, runtime doors, checkpoints,
   notes, imported library entries, wall sources and linked maps. Verify authored
   content survives and all play state/access assignments reset in the copy.
2. Confirm the original player screen does not change and the copy is not live.
3. Duplicate a map with internal and external links; verify only internal links survive.
4. Change/delete copied images/walls/notes and verify source content is independent.
5. Exercise anonymous, viewer, foreign-DM and missing/invalid-CSRF POSTs; ensure denied.
6. Test missing/corrupt images and storage errors, checking no database partial copy
   or referenced partial image remains. Test a large campaign under the target runtime.

FastAPI is unavailable in the patch environment, so HTTP authorization/CSRF routing,
real browsers and Python 3.14 runtime acceptance remain outstanding.

