## Cross-map endpoints and atomic travel (schema 12)

`services/map_transitions.py` owns endpoint validation, authored/runtime state,
arrival preflight, travel and viewer-marker drawing. Endpoints have stable UUID-text
IDs and a map foreign key; their optional outgoing destination references another
endpoint. The service rejects same-map/cross-campaign destinations and coordinates
outside the image. SQL triggers additionally reject cross-campaign links.

`map_transitions` stores authored name/label/type/coordinates/visibility/availability,
arrival policy, private notes, runtime overrides, destination, link_defined and
revision. NULL runtime fields inherit authored values. Deleting a destination sets
its reference NULL while link_defined retains the broken-link distinction. Foreign
keys cascade endpoint deletion with map deletion. Triggers bump map fog versions
on endpoint insert/update/delete and invalidate incoming endpoint revisions on delete.
Two checked map booleans persist viewer marker/label settings, both default on.

Admin routes are included in the existing `/api` router only, reuse campaign/map
management checks and CSRF dependencies, and serialize writes with BEGIN IMMEDIATE.
Travel validates authorization before looking up replay records. Preflight returns
endpoint revisions and destination [cache_token,walls_version,fog_version]; travel
recomputes these in its write transaction. It checks active source and explicit DM
approval/warning acceptance before writing. It checkpoints source fog, optionally
adds one destination reveal, bumps destination fog version, checkpoints destination,
sets the shared active map and records the result in one transaction. It does not
call restore/reset activation: that could overwrite the destination's current fog.
Viewers are notified after commit using the existing active-map refresh event.

`map_transition_travel` has a composite (campaign,user,request_id) primary key and
stores canonical request/result JSON. An identical retry returns the stored result;
a mismatched payload for a reused ID is rejected. Records live until their campaign
or user is deleted; there is no automatic pruning. A replay returns the original
result, not a new navigation instruction applied to the current campaign state.

`web/access.fog_inputs` attaches only (x,y,type,player_label) tuples for discovered
endpoints to MapSpec. Its identity includes markers and marker/label flags, avoiding
stale viewer/preview images. The server compositor checks the endpoint's open-region
label against revealed labels, draws a letter badge and optional label, then clips
all marker pixels to the revealed mask. Private endpoint configuration is not added
to the viewer state API. Raw maps/walls remain admin-only. The existing viewer image
preload/generation guard handles swaps; no new viewer navigation or raw-image path
is introduced. The exact player-image preview includes the same markers.

`map_transitions.js` mounts the editor panel and dialogs; original fog gestures defer
to endpoint selection/placement first. Both overlays use original image coordinates.
The endpoint list refreshes on focus/15-second polling when no dialog or placement is
active. The campaign overview is read-only except for links back to map editors.


### Passage footer, destination activation and fog-editor accordion

The endpoint dialog has a flex-column form with one overflow body and one
non-scrolling actions footer. Closed dialogs retain native display semantics.
The sidebar's peer details share a name for native exclusive opening, with a
small toggle-listener fallback. Legend and nested Alignment are outside the group;
the legend is never programmatically forced open after manual closure.

Inspect destination refreshes and validates the saved source revision/link and
opens an admin-only destination tab. It never calls reveal-choice, active-map, fog,
runtime or travel APIs. Popup-blocked fallback asks before discarding pending edits
and navigates only the admin tab. Existing optional display-options/prompt fields
remain compatible but inspection no longer consumes them.

### Independent passage save scopes

The client stores separate canonical baselines for configuration and session
selections, ignoring the endpoint revision when comparing configuration dirtiness.
Configuration saves return the additive saved_endpoint_id in the existing listing
response, identifying new records without guessing from concurrent additions.
After acknowledgement, the client updates current identity/revision and only the
saved group's fields/baseline; the opposite group's draft/baseline stays intact.
Configuration uses server-normalized values and clears its one-shot return-link
selection. Runtime updates do not repopulate authored fields. Controls are disabled
during writes and re-enabled with current saved-record action availability.

Both saves stay open. Input/change events update independent live status indicators.
Close/Escape and navigation guard pending edits, while Travel warns that it uses
saved values. Successful writes are acknowledged before a subsequent map refresh;
a refresh error does not masquerade as an uncommitted write. Service authorization,
CSRF, serialized writes and stale-revision validation are unchanged.


### Portal Close and travel-return checkpoints

Portal configuration records a canonical snapshot of its local rows and sorted
route selections after opening and each successful Apply. Close/Escape compares
against that checkpoint, asking only when unapplied changes exist. The duplicate
Cancel handler/button is removed. Reset pairing confirms the affected sections
before changing popup state; no server mutation is added.

Travel confirmation stores source form scroll/focus without calling open(item) or
repopulating fields on return. Back/Escape restores the same DOM, dirty baselines
and saved revision, clears the cancelled preflight and uses a fresh preflight on
the next attempt. The listing used for travel preparation is held separately from
the source form's current saved record so previewing/cancelling cannot silently
rebase stale edits. In-flight request cancellation is blocked; server travel
transactions and idempotency are unchanged. Reset labels describe existing backend
effects rather than adding new reset behavior.

