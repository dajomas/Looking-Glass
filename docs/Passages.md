# Passages

Current contract including the compass/Exit-target update based on development
commit c745166b56319901be8b609d120a9ee3b4cf9817. Runtime behavior is unchanged;
this follow-up and the compass-side update change authoring only. Viewer arrows remain display-only. No
cross-map portals, token movement or viewer passage mutation endpoints are added.

## Doors and secret doors

Doors work in both directions. Admin single-click on a usable arrow reveals the
adjacent destination even in Hide mode; the door remains a fog-area boundary.
Locked/unlocked doors can start in either state. Only admin arrow double-click
toggles state; it never also reveals/hides fog. Locked singles do nothing.

Secret doors have admin-only purple hints until discovered. Their post-discovery
type is configured in the wall editor: Door, Locked Door or Unlocked Door. Admin
arrow double-click discovers without revealing. A formerly secret door keeps
arrows after both areas are revealed, but each source area must itself be revealed.
Viewer locked/unlocked hints look ordinary; there is no learned-lock state.

## Portal sections, pairs and sides

- Each pair contains exactly two Portal wall elements on the same map.
- Each element has two sides: Entry, Exit, Both or None. At most one None per
  element is allowed in a complete configuration. Both has independent roles.
- Every Entry explicitly chooses one Exit-capable side of the other element.
  Self/same-element routing is prohibited. Shared Exits are allowed; every Exit
  needs at least one incoming Entry. A pair cannot route to a third element.
- Each Entry independently starts ordinary, locked, unlocked or secret. Secret
  Entries have authored post-discovery types. Discovery or locking affects only
  that Entry. Exit roles are always ordinary and invisible on viewers.
- Admin single-click on an ordinary/unlocked Entry reveals the area behind the
  remote Exit, not the locally adjacent area. Revealed destinations are no-ops.
- Only admin arrow double-click discovers/toggles state, without revealing.
- Portal Entry arrows persist after destination reveal, but their source area
  must be revealed. Admin-only Exit hints appear when an incoming Entry is shown,
  including secret/locked Entries. Exit hints may appear in fog and never act.
- Viewers never follow passages. They see Entry hints only; Both can show a
  double-headed Entry indicator. Undiscovered secret Entries are hidden.

## Portal configuration popup

1. Draw or convert Portal elements. Both sides start Unconfigured, not Entry/Exit.
2. Select one Portal section in the popup and edit only its two sides. All element
   dropdowns contain Portal elements only; ordinary walls/doors are excluded.
3. When configuring a side, the opposite side defaults to None if and only if it
   was still Unconfigured. Already configured sides are never overwritten by this
   default. Unconfigured is a temporary draft state, not a fifth saved role.
4. Entry/Both sides expose destination Portal-section and Exit-side selectors.
   Select an Exit, Unconfigured or None side on the other element. Selecting an
   Unconfigured/None target immediately changes it to Exit inside the popup;
   Apply commits that conversion with the route to the draft. An untouched opposite
   side still defaults to None. Both remains selectable and keeps its Entry role;
   Entry-only targets are disabled. Shared Exits remain allowed.
5. Switching selected section retains pending popup edits. Apply configuration to
   draft commits all edits atomically, including target initialization. Close or
   Escape asks before discarding pending popup edits, without reverting earlier
   Applies. No popup action autosaves to the server.
6. Apply may stage incomplete sections while the rest are configured. Save and
   Download require all portal sections/graphs to be complete, with valid pairs,
   destinations, incoming Entry coverage and the per-element None limit. Client
   preflight and existing server validation both enforce the complete contract.
7. Reset pairing… resets a section and its partner together to two
   Unconfigured Portal elements. Coordinates and Portal type are preserved.
   Reset is pending until Apply and then undoable; re-pair or remove/retype afterward.

Portal sides use compass designations in the popup, destination selector, error
messages and map labels. The top of the map is North. The side's outward normal
is rounded to the nearest of N, NE, E, SE, S, SW, W or NW; opposite sides always
have opposite headings. Map labels are section-number.heading (for example 2.E
or 3.NW), not side 1/2. Pan/zoom does not change map-relative headings.

Stored side and Exit indices remain 0/1 for compatibility. Internal index 0 is
minus the normal (-dy,dx), and index 1 is plus that normal, with image Y down.
Reversing endpoints swaps the compass designation attached to those indices;
existing role assignments and routes are not silently remapped. Midpoint
sampling and narrow-room/gap limitations are unchanged; an unusable destination
open pixel yields no actionable arrow. Graph validity is not geometric room validity.

## Appearance

| Entity | Default color | Wall dashed | Admin arrow | Viewer arrow |
|---|---|---|---|---|
| Door | Blue #46c0ff | No | Toward passage | Ordinary door |
| Locked Door | Orange #ff9f43 | Yes | Locked color | Ordinary door |
| Unlocked Door | Orange #ff9f43 | No | Regular door color | Ordinary door |
| Undiscovered Secret Door | Purple #b07cff | Yes | Yes | No |
| Portal Entry / Exit | Silver #c0c0c0 | No | Toward / away | Entry only |
| Portal Both | Silver #c0c0c0 | No | Double-headed | Double-headed Entry |
| Locked Portal Entry | Brown #a66a3f | Yes | Yes | Ordinary silver Entry |
| Unlocked Portal Entry | Brown #a66a3f | No | Yes | Ordinary silver Entry |
| Undiscovered Secret Portal Entry | Red #ff5252 | No | Yes | No |

Existing per-map regular/locked door arrow color overrides and independent
admin/viewer arrow visibility preferences are preserved. Portal strokes remain
per-side over the silver segment; Unconfigured draft sides have no category stroke.

## Runtime, export and safety (unchanged)

Fog Undo changes reveal/hide history, not discovery/locks. Reset covers the map,
restores authored states and hides secrets; Show-map Reset does the same. Undoing
fog Reset does not restore discarded runtime overrides. Reload/restart/Restore
retains state. Replacing/saving walls clears state on replaced wall IDs.
UVTT extension v2 stores complete authored configuration only, never temporary
draft state or runtime overrides; ordinary v1 files remain supported. Standard
UVTT fallback represents teleport elements as opaque boundaries and loses routing.

Locks constrain passage controls, not the DM's manual reveal tools. Enabled and
Doors split areas control boundaries. Changing boundaries can merge areas and
expand existing reveals: blank viewers before editing, save, inspect the exact
viewer preview and reset fog if needed. Show controls affect wall overlays, not
passage-arrow visibility. Permission/CSRF/stale-save/runtime behavior is unchanged.

See [wall editing](wall-editor.md) for the single-section editor, compass labels
and selectable None targets; [API](api.md) and [architecture](architecture.md) for
storage details; and [deployment](deployment.md) for passage migration guidance.

## Movable editor, overview and admin route cycle

The Portal configuration title bar is draggable by mouse/touch and keyboard
arrows. Center restores its position; resizing keeps its title bar reachable.
The native modal remains modal, with a lighter backdrop so underlying artwork is
visible. Moving the popup does not edit walls, reset fields, reveal or save.

Portal overview is available from the wall toolbar and inside the popup. It shows
one row per side with section/compass, role, initial state, secret post-discovery
state, outgoing paired Exit and incoming Entries (including shared Exits). It is
a read-only snapshot: the toolbar uses the current wall-editor draft; the popup
uses pending buffered edits. These are authored states, not live session overrides.

The admin fog page cycles live visible Entry→Exit routes, highlighting both arrow
polygons for 5 seconds before moving to the next route. A 1–15 s slider controls
per-route dwell, not the fixed 1.2-second color-alternation period. At least two routes and
both endpoint arrow polygons must be in view. Only existing enabled admin arrow
geometry is eligible; a shared Exit is highlighted once for each incoming route,
and Both roles reuse their displayed double-headed polygon. Full-opacity bright
yellow (#ffea00, black outline) alternates with deep blue (#1538d0, white outline)
over the normal arrows; the overlay never intercepts clicks. Ordinary door
arrows are not included. Viewer rendering and hit-target validation are unchanged.

Pause is local to the browser/map, as is dwell preference. Cycling stops while
busy/loading, offscreen, with fewer than two visible routes, when arrows are
hidden or when the tab is hidden. New geometry cancels old highlights until the
current mask loads. Reduced-motion users see steady bright-yellow highlighting,
while the route selection still advances at the chosen dwell. See [map controls](map-controls.md).

## Readable portal labels and route highlights

Wall-editor portal labels have white semibold monospace text on rounded dark
background badges at 78% opacity, with a subtle light border. Backgrounds fit the
actual text bounds, including longer section numbers. Text size, padding and
corner radius are compensated for zoom; all labels render above all wall strokes.
Badges remain pointer-events:none and do not change editing/hit targets or exports.

Admin route highlights alternate full-opacity yellow/black-outline and blue/white-
outline phases every 1.2 seconds per complete cycle, instead of fading a yellow
fill. Outlines are 4 screen pixels with a light/dark halo. Route dwell (1–15 seconds)
and selection rules remain unchanged. Reduced-motion uses a steady yellow phase;
its route dwell still advances. This overlay remains masked to existing arrow alpha
and is admin-only: player images, fog state and authoritative hits are unchanged.
See [testing](testing.md) for reproducible checks and validation scope.


## Viewer portal and discovered-secret arrow exceptions

When **Show door arrows (viewer)** is unchecked, two indented controls appear:

- **Show portal arrows (viewer)**: show eligible portal entry/Both arrows, including discovered secret portal entries.
- **Show secret arrows (viewer)**: show eligible arrows with a secret origin after discovery, including secret-origin portal entries.

The categories form a union: either matching option is sufficient. An entry whose current state is `secret` is always hidden from players, regardless of all three toggles. Ordinary doors remain hidden when the main toggle is off. Existing revealed-area, blocking-wall, source-side, and doors-split-areas rules still apply; these options never reveal fog or display admin-only exit hints.

The main viewer toggle retains its previous all-eligible-arrows behavior when enabled. Exception choices are saved per map, retained while the main toggle is on, and default to off for both existing and new maps. The admin arrow toggle is independent. Changes are saved immediately and notify connected viewers.


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

The passage footer action is Travel… and its final confirmation says Travel to
[destination map]. It still uses saved configuration/session state, shows the
source/destination and arrival policy, and retains all server validation/approval
rules. Back to passage (or Escape) closes the confirmation without executing a trip
and reopens the same source form, retaining both pending field groups, their dirty
indicators and body scroll position. The prior focus is restored where available.
A new attempt performs a fresh preflight; cancelled requests are not reused. While
a trip request is in flight, cancellation is blocked to avoid implying the server
operation was stopped. Failed trips remain in the confirmation with an error.

The Show battle map choice now labels its actions Restore saved reveals,
Reset fog and show map, and Cancel. Reset permanently discards that map's reveal
history, restores wall-door locks and wall-passage discovery to authored states,
and shows the map fully covered. Fog Undo cannot undo this activation reset.
Cross-map endpoint session overrides remain separate and are not reset by it.
Restore still uses the existing checkpoint semantics; the labels do not change
activation behavior. Cancel still performs no activation or reset.

## Single-map campaigns

The fog editor hides the Map passages sidebar section when there is only one
map in the campaign. It becomes visible on editor load with two or more maps.
Stored endpoint data and passage APIs are not deleted or disabled. Passage
marker instructions are consolidated under the sidebar’s `? Help` control.
