## Campaign backup operations

The campaign Settings backup is a portable content backup, not a full instance backup.
Continue backing up the database, map storage, configuration and secrets using your
normal installation backup procedure. Campaign ZIPs exclude users, password hashes,
sessions, campaign owner and viewer assignments, and travel replay records.

Restore normally requires the same database schema version; schema 16 also accepts schema-15 backups (the exported content tables are unchanged). `storage.max_upload_mb` limits
both uploaded ZIP bytes and total expanded ZIP bytes; base64 wall sources add overhead.
Reverse-proxy upload limits may reject requests first. Backup downloads themselves are
not capped by this setting. Export and restore buffer archive data in memory and restore
holds a database write transaction, so allow sufficient memory/disk space and schedule
large operations while the campaign is idle. Use only trusted backups and store them
securely; archives contain unrevealed maps and notes and have no built-in encryption.

Apply this patch over the supplied source baseline, restart the application, and follow
[testing](testing.md#campaign-backup-and-restore-validation). No migration/configuration
change is necessary. Preserve a full instance backup before deployment. To roll back code,
revert the patch and restart; reverting code does not undo a campaign restore.

### Step 4 recovery storage and resource requirements

Allow the service account to create `data/recovery` under the configured data directory.
Recovery ZIPs contain unrevealed maps and DM notes; restrict filesystem access and include
them in your backup policy. Files use 0600 and a newly created recovery directory uses 0700
on POSIX. An existing directory's permissions are not automatically changed. Windows uses
file flush/fsync but has no POSIX directory-fsync/permission guarantees.

Recovery files are retained indefinitely, including after campaign deletion. Operators must
monitor space and archive/remove old ZIPs explicitly; no background retention job exists.
The campaign settings lists its retained backups; after campaign deletion recovery requires
an operator to retrieve the ZIP and restore it into another campaign. Do not serve the data
directory as static web content. Recovery downloads require current management permission.

Inspection makes a private full-database snapshot under the OS temporary directory and
writes validated temporary images there. Provision memory for archive buffers and serialized
DB snapshots, plus temporary disk for the DB and decoded images, and persistent disk for a
complete recovery ZIP. A crash can leave temporary snapshots or orphaned image files; clean
up while stopped. Missing current images, unwritable/full storage or a recovery exceeding
`storage.max_upload_mb` block replacement. Raise limits/provision space or repair the
installation deliberately rather than bypassing the safeguard.

Apply over source baseline 38f52b8, restart, and follow the step 4 acceptance checklist.
No migration, new dependency or configuration key is introduced. Restart invalidates open
previews. Use the supported single application process, not multiple independent workers.
Rollback code by restoring prior files and restarting; that does not reverse restored data.
Recover portable content by inspecting/restoring the retained recovery ZIP; recover instance
state/checkpoint history using a complete matched database/maps installation backup.

