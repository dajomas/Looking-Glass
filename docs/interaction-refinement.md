# Immediate Apply and conditional display policy

This update targets features/development commit
82159e7c0d88c5c9ec5dd32e01fa55d1b6c8f664.

Apply actions no longer confirm. Destructive deletion confirmations and the
existing toolbar Reset confirmation are deliberately retained. Restore/Reset/
Cancel is a separate display policy, not an Apply confirmation.

GET `/api/maps/{id}/display-options` requires a managing user's session and
returns `{"ok":true,"map_id":1,"can_restore":false}` with Cache-Control:
no-store. It loads live fog operations for the active map or the last-displayed
checkpoint for an inactive map. It uses the fog engine's area map and ordered
reveal/hide replay, not a raw operation count. The checkpoint mask is not put
into the live mask cache. Empty, never-displayed or fully hidden maps return
false. Malformed checkpoints fail rather than causing automatic reset.

The browser checks on every Show or editor map-switch action. False means it
submits the existing activation request with fog_action=reset. True means it
asks Restore/Reset/Cancel and submits only after a choice. The activation APIs
remain explicit and unchanged; external clients must still send fog_action.
Opening an editor directly does not implicitly publish it. Switching via the
editor dropdown now does publish the selected map after this policy check.

The check is fresh but is not a cross-request concurrency lock: another DM tab
could change operations between the check and activation. This release does not
add optimistic concurrency tokens. The existing activation transaction and
permissions remain authoritative. If the check fails, no action is submitted.

The restored legend documents existing colours/styles. This patch does not
introduce persistent per-category boundary switches or alter the previous
wall-type schema. Existing Show walls and Doors split areas retain their roles.
The duplicate one-off importer is removed from the editor, but old API endpoints
are retained for compatibility. Optional pack-image controls remain null-safe.

No migration is added and no schema-version history is rewritten. Previously
installed cache-token/checkpoint schema is a prerequisite. Server restart and
browser hard reload are required because the availability route is new.
