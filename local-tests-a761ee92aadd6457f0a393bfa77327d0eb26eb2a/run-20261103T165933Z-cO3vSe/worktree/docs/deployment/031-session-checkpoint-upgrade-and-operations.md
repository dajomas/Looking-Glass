## Session checkpoint upgrade and operations

This feature requires automatic migration **16**, adding a checkpoint table/index and a
campaign session-generation column. Before first startup with the patch, stop the server
and keep a full database/map-directory backup. Restart to apply migration normally. No
new package, configuration setting or port change is required (viewer default stays 5100).

The migration is additive and leaves existing campaign content intact. Portable campaign
ZIPs from schema 15 remain accepted by schema 16 because their exported content structure
is unchanged; older unrelated schemas remain rejected. Named checkpoint histories are not
part of portable ZIPs and are protected by full instance backups instead.

Capture/preview/restore hash map images and serialize play state. Create/restore hold a
write transaction; preview holds a read snapshot. Allow time/I/O/memory for large campaigns
and avoid concurrent image replacement. Each payload is limited to 64 MiB; total history
is not capped or automatically pruned. Manage retained checkpoints explicitly. The item-7
file-import feedback bug is not addressed by this feature.

No down-migration is supplied. A full rollback to the pre-upgrade installation requires
the matching old code and pre-upgrade database/map backup. Reverting code alone does not
rewind restored play state or remove migration 16. If a restore itself needs undoing,
use its automatic safety checkpoint while authored content remains compatible.

