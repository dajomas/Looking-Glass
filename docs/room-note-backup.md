# Retained-note campaign backups and restore

Development branch: archive-aware ZIP backup/restore is implemented but not yet
validated here. Clean map/campaign duplication still omits retained archives.
Do not deploy against valuable campaign data until remaining bug-2 work and
acceptance are complete. Keep stopped database/image backups before upgrades.

Campaign ZIP exports now contain room_note_archives as campaign-scoped map
content. Exact names, Markdown, origin UUIDs, timestamps and historical source
provenance are retained. Export and inspection do not reconcile geometry or
automatically reattach archived content. Expanded/compressed upload limits and
strict ZIP/table/column checks remain in force.

Restore accepts genuine schemas 15, 16, 17 and 18. Legacy backups must not
contain the new archive table or map note-generation column; these are normalized
to an empty archive list and initial generation zero. Schemas 15/16 also retain
the existing double-reveal normalization. Current schema 18 must contain every
required table/column. Intermediate ZIPs mislabeled schema 18 but missing archive
data are rejected rather than silently treated as complete backups.

Current owning map IDs and local archive IDs are regenerated/remapped on restore.
Historical source_* identifiers are not required to point to current maps or
campaigns and are preserved unchanged. Restored maps receive fresh incarnation
tokens; pre-restore editor/recovery requests are stale. Note insert triggers may
advance the restored map generation while rows are imported; that counter is
not a portable identity. Archives remain detached until explicit recovery.

Inspection counts include archives, including zero for legacy backups. Restore
preview digests bind retained content too. The existing durable pre-restore
recovery ZIP uses the same export/inspection code and therefore includes
archives. Existing explicit campaign restore still restores the campaign's saved
fog/active-map state and publishes its usual notification; archive support adds
no independent fog or viewer mutation. Ownership and viewer assignments follow
the unchanged restore workflow.

The caller owns restore transaction rollback and newly created image cleanup.
This increment does not solve process termination, disk exhaustion or all image
lifetime issues. See [handover](handover/057-bug-2-archive-backup-restore-2026-10-30.md)
for supplied regressions, validation limits and remaining work. Recovery UI/API
guidance remains in [room-note recovery](room-note-recovery.md); its conservative
intermediate-state warnings still apply until acceptance and duplication work.
