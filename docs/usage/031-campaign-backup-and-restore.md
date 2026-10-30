## Campaign backup and restore

Open a campaign from Campaigns, then expand **Settings → Backup / Restore**.

1. Select **Download campaign backup** and retain the ZIP securely.
2. Choose a ZIP and select **Inspect campaign backup**. No campaign content changes.
3. Review schema compatibility, source campaign details, map names/dimensions, content
   counts and compressed/expanded sizes. Invalid archives are rejected without replacement.
4. On the preview, select the identical ZIP again, type the current target campaign name,
   and select **Save recovery backup and restore**. Accept the confirmation.
5. The server revalidates the preview and archive, saves a validated recovery ZIP, then
   replaces campaign content. Successful restore refreshes connected clients.
6. Download the recovery ZIP from the success page or **Retained recovery backups** in
   campaign settings. Inspect and restore it normally to recover the prior portable content.

Restore replaces the campaign name, description and all map content, including active
map, order, appearance, calibration, wall sources, authored walls and passages, runtime
door states, fog operations and displayed checkpoints, linked map transitions, room
notes and imported room library entries. Owner and viewer access remain unchanged.
A backup from another campaign may be restored into the current campaign; IDs are remapped.
Travel replay records are cleared. Original fog-operation author accounts are not restored.

A pre-restore portable recovery ZIP is retained automatically. It is not a full installation
backup or a one-click undo. If recovery creation/validation fails, restore is blocked.
Previews expire after 15 minutes, on server restart, or after target content changes.
Uploads are not retained; select the same file twice. Local named checkpoint history is
not included in portable backups and older checkpoints may become incompatible after restore.
Only the campaign manager or a superadmin can use these controls. Backups normally must match
the database schema version; schema 16 also supports schema-15 campaign backups. Both ZIP upload size and expanded size are limited by
`storage.max_upload_mb`. A backup may exceed the restore limit even when download succeeds.
Keep this ZIP private: it contains unrevealed maps and DM notes, and is not encrypted.
This is not a full installation backup; see [deployment](deployment.md#campaign-backup-operations).

