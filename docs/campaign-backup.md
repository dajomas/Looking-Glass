# Campaign backup and restore

Open a campaign, expand **Backup / Restore** in **Settings**, and select **Download campaign backup**.
The ZIP contains versioned campaign JSON and map images. It includes campaign name/description,
map order and appearance, wall source uploads, calibration, authored walls/passages, runtime states,
fog history and displayed snapshots, map connections, room notes and the imported room library.
Passwords, sessions, accounts and campaign access assignments are never exported.

To restore, select the ZIP, type the current campaign name and confirm. Restore replaces current
campaign content, not other campaigns. Ownership and viewer assignments remain unchanged.
A backup from another campaign can be restored into the current campaign. IDs and image names
are remapped, including linked passage destinations. Retry/replay travel records are cleared.
Download a backup before restoring; no automatic pre-restore backup is retained.

Only campaign managers (owner/admin or superadmin) can use these CSRF-protected POST routes:
- `/campaigns/{campaign_id}/backup`
- `/campaigns/{campaign_id}/restore`

Backups require the same database schema version. Both compressed upload size and total expanded
ZIP size are bounded by `storage.max_upload_mb`. Archives are read directly, never extracted;
SQL is not accepted. Images use the existing image validation pipeline. Database changes roll
back on failure, newly created images are removed on failure, and old images are removed only
after successful commit. Connected clients receive a campaign refresh after success.

Validation performed in this build: three service tests passed (round trip including runtime
states/links/access isolation, transaction rollback, expanded-size rejection). Python sources
compile. The web tests could not run in the build environment because FastAPI is not installed.
Run `PYTHONPATH=python pytest python/tests/test_campaign_backup.py python/tests/test_web.py -q`
in the application's development environment for service and existing web coverage.
