## Cross-map passages (migration 12)

Map passages connect named positions on different maps in the same campaign. They
are separate from wall-based doors and portals: stairs, ladders, drops and climbs
can be placed anywhere inside an image without adding an artificial fog boundary.

### Create and connect endpoints

1. Open an admin map and expand **Map passages** in the sidebar.
2. Choose **Add passage endpoint**, then left-click the map. Escape cancels placement.
3. Enter the admin name, an optional player-facing label, and the passage type:
   Stairway (S), Ladder (L), Hole/drop (H), Portal (P), Climb (C), or Custom (X).
4. Set authored visibility and availability, then select another map and its endpoint.
   An unlinked endpoint is valid and can be saved before its counterpart exists.
5. To create a counterpart, select the destination map and choose **Create destination
   endpoint…**. This opens a new admin tab. Create and save the endpoint there, return
   to the original dialog, choose **Reload destinations**, then select it.
6. Optionally check **Create return connection**. This creates an explicit reverse
   route and refuses to overwrite a destination that already routes somewhere else.
7. Choose the arrival policy and save. Clicking an existing marker or its sidebar
   entry opens its configuration. Use **Pick / move location on map** or edit X/Y to
   reposition it; coordinates are original image pixels, not calibrated wall coordinates.

Connections are directed. A hole/drop can be one-way by leaving the destination
without an outgoing route. A return connection is independent: changing or deleting
a route does not silently remove a previously created reverse connection. Several
sources can share a destination, but each endpoint has at most one outgoing route.
Passage type changes the marker code, not travel mechanics; configure direction
explicitly. Selecting Climb for a new endpoint defaults availability to DM approval.
Use labels such as "Up" or "Down" and DM notes for elevation and skill requirements;
there is no automatic D&D check resolution.

### Discovery and availability

Authored visibility is **Secret**, **Discovered**, or **Admin-only**. Authored
availability is **Usable**, **Blocked**, or **DM approval required**. Current-session
overrides are saved independently and survive restart. Use **Update session state**
to discover a secret or change its current availability. "Use authored setting"
clears the respective override. Saving authored settings does not clear overrides.

**Reset passage session states** restores authored values on the current map without
changing fog, endpoints or links. Ordinary fog resets do not reset these independent
cross-map states; reset them explicitly when starting a new session. There is no
combined reset operation in this first release.

### Preview and travel

- **Inspect destination** opens the saved destination in admin only, with no
  viewer switch, fog mutation or Restore/Reset dialog. New-tab inspection retains
  the source form draft. If popups are blocked, current-tab inspection asks before
  abandoning pending edits. Missing/changed saved destinations are rejected.
- Save configuration changes before using **Travel…**; travel uses
  the saved record, not unsaved dialog fields.
- Show the source map to players first. The travel dialog displays the destination,
  saved arrival policy, current passage state, and estimated area reveal percentage.
- **Preserve destination fog** switches maps without adding a reveal or restoring an
  older snapshot. **Reveal destination area** adds a normal area reveal at the target
  endpoint while preserving all prior exploration on both maps.
- An arrival on a wall is rejected for area reveal. Move it into the room or choose
  Preserve destination fog. Large/open-area reveals require explicit confirmation:
  the engine's existing leak warning, no wall segments, or an area >=50% of the image
  triggers this confirmation. The percentage is the whole destination component,
  not just newly visible pixels; already explored regions may still trigger a warning.
- Secret, blocked and approval-required source passages need an explicit DM override.
  The override permits this trip only; it does not discover the passage or change
  availability. Destination discovery/availability does not prevent arrival; it
  controls that endpoint's own marker and outgoing travel.
- Confirm **Travel** to switch every viewer of this campaign together and open the
  destination editor in the DM tab. A click/double-click on a marker never travels.

The server checks the active source map, both endpoint revisions and the destination
map incarnation/wall/fog versions. If another tab changes them, preview again.
Travel is transactional and duplicate-safe: repeating an identical request ID and
payload returns its previous result without revealing or switching twice.

### Player markers and privacy

**Show map passage markers (viewer)** and **Show passage labels (viewer)** are saved
per map and default on. They are independent from door arrows and portal-arrow
exceptions. Only currently discovered endpoints whose center is in a revealed open
region are drawn; the marker and label are clipped to the fog mask. Secret and
admin-only endpoints never produce player markers. An unlinked discovered endpoint
can still have a marker; player markers are display-only, not navigation controls.

The server renders the marker into the fogged image. Viewers do not receive endpoint
IDs, connection records, destination names/coordinates, admin names or DM notes.
Use player labels suitable for players; blocked/approval state is not exposed in
marker colors. The admin overlay shows all endpoints, with purple secret markers,
gray admin-only markers and red outlines for broken links.

The campaign page's **Map passage connections** section lists all endpoints,
directions, current states and broken links. Deleting an endpoint or destination
map leaves incoming routes visibly broken, never rerouted. Reconnect them manually.
If a replacement image makes an endpoint fall outside its map, reposition it before
travel. Endpoints are not automatically rescaled on image replacement.

### First-release boundaries

One shared active map per campaign; DM-controlled travel only. No tokens, movement
simulation, split-party viewer groups, cross-campaign routes, automatic skill checks,
small-radius reveals, endpoint-facing/area shapes, automatic wall associations or
multi-destination routes. Existing wall-passage logic is unchanged. Cross-map
endpoints are stored in SQLite; UVTT/Foundry wall exports and saved wall-source
copies do not include these separate campaign links. Back up the complete data
folder/database to retain them.


### Map passage modal actions

The passage form scrolls inside a dedicated body. Save configuration, Delete endpoint,
Update session state, Inspect destination, Travel… and Close
sit in a non-scrolling footer, so the main actions stay visible while editing long
configuration forms. Delete and Update session state are hidden for a new endpoint.
Placement and destination-selection helpers remain next to their fields. The footer
wraps on narrow displays; the dialog remains bounded by the viewport. Travel keeps
its separate confirmation and transactional arrival policy.


### Configuration versus current session state

The Map passage modal has two independent save scopes:

| Action | Saves | Does not save |
|---|---|---|
| Save configuration | Name, player label, type, position, authored visibility/availability, destination/return link, arrival policy, notes | Pending session overrides |
| Update session state | Current visibility and availability overrides only | Pending configuration changes |

Both save immediately to the database and keep the modal open. Each group shows its
own saved/unsaved status. Saving one group retains unsaved values and dirty status
in the other, so you can discover a passage without losing an edited destination or
save a new name without applying a staged lock/discovery change. Use Close when done.
Saving configuration never resets existing runtime overrides. A "Use authored setting"
session selection inherits the last saved configuration, not an unsaved field above.

For a new endpoint, save its configuration first; session controls then become
available without reopening the modal. Controls are disabled while a save is in
flight. Successful saves refresh the endpoint revision before another save, avoiding
self-generated stale errors. Rejected/stale saves retain the form drafts and do not
claim that either scope was saved. A failed map refresh after a committed save is
reported separately; the save itself remains acknowledged.

Close and Escape ask before discarding pending edits. Confirmed discard does not
undo either group that was already saved. Page navigation/reload with pending edits
uses the browser's unsaved-changes warning where supported. Travel still uses saved
configuration and session state; when pending edits exist, it asks before proceeding
without them. Inspecting in a new tab neither saves nor discards either draft.


### Clear modal actions and returning from Travel

Portal configuration has one Close button, not duplicate Close/Cancel actions.
Apply configuration to draft still applies one undoable draft update and keeps the
popup open. Close/Escape needs no extra question for a clean popup; if edits are
pending, a discard confirmation protects them. Declining leaves them untouched.
Reset pairing… asks which selected/paired sections will be reset, then stages the
reset in the popup only. Apply is still required to update the wall draft and
Save wall set is still required for database persistence; geometry is not deleted.

