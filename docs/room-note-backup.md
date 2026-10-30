# Retained-note campaign backups, restore and clean duplication

Development branch: archive-aware ZIP backup/restore and clean duplication are
implemented but acceptance remains pending. Do not deploy against valuable
campaign data until remaining bug-2 validation and documentation are complete.
Keep stopped database/image backups before upgrades.

Campaign ZIP exports contain room_note_archives as campaign-scoped map content.
Exact names, Markdown, origin UUIDs, timestamps and historical source provenance
are retained. Export and inspection do not reconcile geometry or automatically
reattach archived content. Expanded/compressed upload limits and strict
ZIP/table/column checks remain in force.

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

## Clean map/campaign duplication

Clean duplication copies every retained archive for the selected source maps.
Only its local archive ID and current owning map_id change. Historical source
identifiers/names/incarnation, source revision, origin UUID, timestamp, anchors,
area key and exact text remain unchanged. Historical names describe the original
archival event, not the newly named copy. Multiple independent copies can share
an origin UUID; they have separate locally owned archive records.

Archives are not turned into active room assignments. Existing active authored
notes are still copied under the existing rules, including fresh active-note
revisions. A copy starts its own note-generation counter at zero, then normal
insert triggers advance it for copied active assignments. It does not inherit
the source's counter. Fresh map incarnation tokens invalidate source-context
requests against the copy.

Existing clean-copy rules are retained: independent image files, fully fogged
start, no reveal history/display snapshots/runtime overrides/checkpoints, no
automatic map activation and no source/viewer changes. Campaign copies have no
viewer assignments; single-map copies remain in their campaign. Existing
permission, CSRF, immediate-transaction and created-image cleanup paths apply.

The caller owns restore/copy transaction rollback and newly created image
cleanup. These increments do not solve process termination, disk exhaustion or
all image lifetime issues. See [backup record](handover/057-bug-2-archive-backup-restore-2026-10-30.md)
and [duplication record](handover/058-bug-2-archive-clean-duplication-2026-10-30.md)
for supplied regressions, validation limits and unfinished work. Recovery UI/API
guidance remains in [room-note recovery](room-note-recovery.md). Conservative
development-state warnings remain until acceptance; implementation is not proof
of a successful workflow, restore or deployment.
