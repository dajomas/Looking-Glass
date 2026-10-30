## Step 4 backup inspection and recovery

From the repository root, with development dependencies installed:

```sh
PYTHONPATH=python python -m pytest -q python/tests/test_campaign_backup.py python/tests/test_campaign_backup_inspection.py python/tests/test_campaign_backup_inspection_templates.py python/tests/test_campaign_backup_inspection_web.py
```

Patch build results: 18 tests passed; the HTTP module was skipped because FastAPI is
not installed in the build environment. Tests ran with Python 3.12; source compilation is
also checked using Python 3.14. These are not claims of browser or HTTP acceptance.
Service checks cover original round trips and schema compatibility, read-only inspection,
archive/user/target/expiry/restart binding, restorable recovery, corrupt images, missing,
unexpected and duplicate entries, incompatible schema, and recovery failure/limit blocking.
Template checks cover escaped archive text, preview/CSRF fields and the inspection-first UI.
The added HTTP regression covers management/CSRF boundaries, preview requirement,
successful restore, authenticated recovery downloads and preview replay rejection.

Manual acceptance before deployment:
1. Inspect a nonempty campaign ZIP with notes, linked passages and active map; verify
   names/dimensions/counts/schema/size match. Cancel and verify all live state is unchanged.
2. Reject incompatible schema, corrupt JSON/images, missing/duplicate/extra ZIP entries,
   compressed/expanded overflow and foreign-key inconsistencies without replacement.
3. Reject other-admin/viewer access, missing CSRF, wrong typed name, missing preview,
   a different ZIP, expired preview, server restart, target edits and replay after success.
4. Restore a valid backup; check owner/viewers/other campaigns are unchanged, linked
   destinations and runtime states are restored and connected players refresh.
5. Download recovery from success and settings pages. Inspect and restore it; verify
   the original portable state returns, including original active map/fog/notes.
6. Make recovery storage unwritable/full or remove a current image; restore must be
   blocked before live replacement. Restore service permissions afterward.
7. Check an empty campaign round trip and token replay rejection. Check recovery links
   reject nonmanagers and invalid/cross-campaign filenames.
8. Confirm retained ZIPs survive restart and require explicit operator cleanup. Verify
   the temporary directory is cleaned after normal inspection failure/success.
9. Exercise large campaigns on the actual deployment, observing memory/temp/disk use,
   request latency, proxy limits and viewer reconnect behavior.

No automatic recovery retention or full installation rollback is provided. Local named
checkpoint history is excluded from ZIPs and older checkpoints may become incompatible.

