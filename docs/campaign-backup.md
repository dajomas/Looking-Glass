# Campaign backup and restore

Open a campaign, expand **Backup / Restore** in **Settings**, and select **Download campaign backup**.
The ZIP contains versioned campaign JSON and map images. It includes campaign name/description,
map order and appearance, wall source uploads, calibration, authored walls/passages, runtime states,
fog history and displayed snapshots, map connections, room notes and the imported room library.
Passwords, sessions, accounts and campaign access assignments are never exported.

To restore safely:

1. Select the ZIP and **Inspect campaign backup**. Live campaign rows/files are unchanged.
2. Review compatible schema, source name/description, map list/dimensions, per-table counts
   and compressed/expanded byte sizes. Incompatible/corrupt archives are rejected.
3. Select the identical ZIP again on the preview page and type the current target name.
4. Select **Save recovery backup and restore** and confirm replacement.
5. Download the pre-restore recovery ZIP from the success page, or later under
   **Retained recovery backups** in campaign Settings. Inspect/restore that ZIP to recover.

Restore replaces current campaign content, not other campaigns. Ownership and viewer
assignments remain unchanged. Backups from another campaign are supported; map/wall IDs,
image names and passage destinations are remapped. Travel replay records are cleared.
The campaign session version advances so old previews cannot be replayed after success.

Preview tokens expire after 15 minutes or server restart and are bound to the user,
archive bytes and target database content. Changed content/archives require inspection again.
No upload is staged on the server: the second file selection is intentional. The signer
uses the supported single-process application model. Files modified outside the application
are not tracked by the target database digest; keep campaigns idle during backup/restore.

The same real importer is exercised against a temporary database snapshot and temporary
images during inspection and again before replacement. A recovery ZIP containing the
current portable campaign content must be exported, validated and durably saved before
replacement is allowed. Missing current images, upload/expanded limits, unavailable disk
or write failures block restore. Recovery files remain even if a subsequent restore fails.
They live under `data/recovery` and are not automatically pruned. Treat them as sensitive.

Admin-portal routes (owning admin/DM or superadmin):
- `POST /campaigns/{campaign_id}/backup` — CSRF-protected ZIP download.
- `POST /campaigns/{campaign_id}/restore/inspect` — CSRF-protected read-only inspection.
- `POST /campaigns/{campaign_id}/restore` — CSRF, typed name and signed preview required.
- `GET /campaigns/{campaign_id}/recovery/{name}` — authenticated recovery ZIP download.

Backups normally require the current database schema. Schema 16 also accepts schema 15
because portable content is unchanged. Compressed upload and expanded ZIP bytes are both
bounded by `storage.max_upload_mb`; downloads alone are not capped. Only expected entries,
allowlisted tables and exact columns are accepted. Archive SQL is never executed and
archive paths are never extracted. Images use the existing validation pipeline. Database
changes roll back on failure; new images are removed on caught failures; old images are
removed only after commit. Clients receive a campaign refresh after success.

Inspection needs memory and OS temporary disk for a full database snapshot and decoded
images. Portable recovery excludes accounts, access assignments and local checkpoint history.
It is not full installation backup or atomic filesystem rollback. See deployment guidance.

Validation for this patch: 18 service/template tests passed; one HTTP module skipped
because FastAPI is unavailable. Browser and HTTP acceptance remain to run in the development
installation. See [testing](testing.md#step-4-backup-inspection-and-recovery) and
[patch notes](../Patch/step-4-backup-inspection.md).

## Readiness capacity check

Before relying on a campaign backup, run **Check campaign**. The report compares current
serialized campaign JSON plus image sizes against the expanded restore limit and checks
archive-entry count. It uses the same payload builder as export without creating a ZIP.
A missing or unreadable image makes the result incomplete. Compressed upload size, proxy
limits and actual restore success are not checked; retain tested backups independently.

## Named checkpoints versus portable backups

Session checkpoints save local campaign play state and are distinct from campaign ZIP
backups. They do not contain authored images/walls/notes and cannot reconstruct a deleted
map. Named checkpoint history and automatic safety checkpoints are stored in the database
and are not exported by portable campaign backups. Use a full installation backup to retain
them. Portable ZIP restore remaps map identities, normally invalidating prior local checkpoints.
The checkpoint table is removed automatically when its campaign is deleted.

Migration 16 is additive; schema-15 portable campaign backups remain supported on schema 16
with exact content-table validation. No broader old-schema import support is implied.

## Clean map/campaign duplication (step 6)

On the campaign page, use Settings → Duplicate campaign to create an independently
owned clean campaign, or the Duplicate map disclosure beside a map to copy it into
the same campaign. Enter a copy name (1–120 non-whitespace characters).

Copies preserve authored map images (independent stored files), calibration, wall
and passage definitions, arrow/marker appearance settings, boundary settings,
room names/notes and imported room-library entries. Campaign copies also preserve
map order, description and saved wall sources. Passage endpoint IDs are regenerated;
connections among copied endpoints are remapped. A single-map copy detaches links
to endpoints outside that map; reconnect them explicitly if desired.

Copies start fully fogged, with no reveal history, last-display fog snapshots,
runtime door/passage/endpoint overrides, travel replay records, or session checkpoints.
A campaign copy belongs to the requesting DM, has no viewer assignments and no
active map. A map copy is appended in its existing campaign and never made active.
The source campaign, its viewer display and its runtime state are unchanged.

The operation requires campaign-management permission and CSRF validation; campaign
copy also requires campaign-creation permission. Database writes share one immediate
transaction. Images created before an error are removed after rollback. No migration,
new dependency, configuration change or port change is required. Large copies hold
the SQLite write transaction while validating and copying images; allow adequate disk
space and avoid concurrent bulk writes. Process termination can leave orphan image
files (as with other multi-resource operations); database commit is still transactional.
