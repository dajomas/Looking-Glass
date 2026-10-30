## Named session checkpoints

Open **Session checkpoints** on any campaign-context admin page. Save your editor drafts
first: checkpoints capture committed server data, not unsaved browser work. Enter a name
such as “Before session 12” and optional notes, then save. Saving and inspecting do not
change the player display. Names need not be unique; checkpoint IDs identify entries.
History is paginated (50 entries/page), including automatically generated safety entries.

A checkpoint records, across all maps in the campaign:
- Active player map, including a blank screen.
- Ordered current fog operations and each map's last-displayed fog snapshot, if present.
- Runtime door and per-entry passage overrides.
- Cross-map endpoint runtime discovery/availability overrides.

To restore, open a saved checkpoint and review the current/saved summaries and any
compatibility conflicts. Type the current campaign name and select **Save safety
checkpoint and restore**. Accept the browser confirmation when JavaScript is available.
The server always enforces name confirmation, CSRF, compatibility and preview freshness.
Connected viewers refresh to the restored active map/fog after commit. Restoring is
an explicit player-facing action; merely opening a preview is not.

Before state replacement, an automatic safety checkpoint captures the current play state
inside the same transaction. If restoration fails, both changes and the safety insertion
roll back. To return to the pre-restore state, preview and restore that safety checkpoint.
Restore is not a single fog Undo action. Restored fog-operation author references use the
restoring user; original operation row IDs/authorship/timestamps are not replayed.

Authored content is not restored: map images, walls, alignment, connection definitions,
map/room names, room notes, library content, appearance settings, campaign name/description,
owner and viewer access stay as they are. Last-displayed snapshots retain their saved
operation content, but database update timestamps are fresh. Travel retry records are
cleared; map/cache versions, endpoint revisions and a session generation advance rather
than being rewound. Normal map-switching behavior is otherwise unchanged.

### Compatibility and stale previews

The campaign must contain the same maps and identities. Image bytes, geometry, calibration,
boundary settings, authored passage behavior/connections and fog-engine configuration
must match. Map/room renaming, note editing and appearance changes do not invalidate the
saved state. Checks are deliberately conservative: adding/removing a map blocks an older
checkpoint even if other maps are unchanged. There is no force-restore option.

A preview token binds the selected checkpoint and current play state/version. If state
changes after preview, reload the preview; do not retry an old restore form. Missing images
or invalid checkpoint data block restore. Existing room-note associations may become
stale under a different runtime topology; normal editor reconciliation behavior still
applies when subsequently opening/refreshing editors.

### Storage and deletion

Checkpoints are local database records with a 64 MiB serialized limit per entry. History
is not automatically pruned; delete unwanted entries by typing their checkpoint name.
Deletion affects only the selected saved entry, not current play state or viewers. Campaign
deletion removes its checkpoint history. A portable campaign ZIP does not include named
checkpoint history; keep full installation backups. Restoring a campaign ZIP changes map
identities and will normally make earlier local checkpoints incompatible.

