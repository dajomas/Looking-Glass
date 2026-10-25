# Usage guide

## Setup and preparation

Start Looking Glass, sign in with the initial superadmin account and change its
password. Create admin/DM and viewer accounts. Create a campaign, import maps,
and assign viewers from its campaign page. Ports follow your configuration.
The original single-map import accepts an image, optional Foundry VTT / UVTT
walls, and an optional name. The additional batch section accepts multiple
images and independent wall files; see campaign-batch-import.md.

## Saved sources and dropdown values

Save wall sources once in the campaign, choose a saved source and wall set,
and apply. Wall sets are naturally alphabetised while retaining their original
import indices. Applying does not ask for confirmation. The same source/set can
be used for several maps; applying affects only its target map. The removed
one-off importer is not restored by this update.

Valid selected values stay visible after Apply, source-list refresh and page
reload. Browser-local choices are keyed by page, target map and (for wall sets)
source ID. A choice is restored only if its option still exists and the dropdown
is ready. Changing source cannot restore a set from a different source. Choosing
the blank option explicitly clears that preference. The map switch remains
server/URL-authoritative, not restored to a different map by browser storage.
Browser storage can be unavailable; the controls still work without persistence.
This is UI selection memory, not a database association inferred from the menu.

## Wall legend: Show and Enabled

Each type has two independent controls:

- **Show** immediately shows/hides that category in the DM overlay only. It is
  remembered in this browser per map. Hiding it does not remove its boundaries.
- **Enabled** controls whether the type participates in area calculations after
  **Apply wall types**. These settings are saved per map on the server, survive
  reload/reimport and affect both DM area detection and player composites.

Disabled segments remain stored and are displayed passively unless hidden.
They can be re-enabled without reimport. Ethereal walls never block even when
Enabled is checked. Door and secret-door boundaries also require Doors split
areas. The overall Show walls toggle still controls the entire DM overlay.
Changing boundaries can merge rooms and expand previous reveals. Blank the
viewer before applying boundary changes during play. Apply is immediate.

The legend colours are magenta normal walls, blue doors, purple dashed secret
doors, green windows/terrain, yellow dashed invisible walls and grey passive/
ethereal walls. Alignment uses image=(wall-offset)*scale. Apply alignment after
adjusting scale, offset or nudges; no confirmation is shown.

## Opening an editor and revealing

Artwork loads independently from map metadata. If metadata/walls or the mask
fail, an explicit error and **Retry loading map** control are available. A
15-second poll can also recover missing initial metadata. Artwork changes get
new image URLs. If a failure persists, retain the visible error and inspect the
server log rather than resetting the database. This update does not claim to
repair arbitrary missing images or an unrepaired older schema.

Reveal and Reveal all warn if this map is not shown to players. They still save
the operation on the edited map; they do not silently switch the active display.
The warning uses the server's active-state response and a persistent not-shown
notice, so it is not only a potentially stale initial browser indicator.

## Showing and switching maps

Every Show/editor map switch checks the target's live or last-displayed reveal
state afresh. Empty or fully hidden histories start with reset reveals without
a dialog. Restorable histories offer Restore/Reset/Cancel. Check failures make
no display change. An editor dropdown switch activates its target before
navigation; directly opening an editor remains edit-only. Blanking needs no
restore choice. Display Reset clears old undo history; toolbar Reset remains
undoable. Delete and toolbar-reset confirmations remain; Apply has none.

## Viewer framing

On each map/fog version change, the viewer fits and centers the bounding box of
all currently revealed pixels with a small margin. It does not reveal additional
pixels or send raw walls/images. With no revealed pixels it fits the full fogged
map. Manual pan/zoom works until the next update; Fit and resize frame the current
revealed region. With separated visible rooms it fits their combined extent,
not just the most recently clicked room.

## At the table and deployment

Click bounded rooms to reveal/hide; use Undo, Reveal all, Reset, player preview
and Blank as needed. F fits, the wheel zooms and dragging pans. Always inspect
the exact player preview after geometry changes.

Stop the service and back up the data directory before installing. Restart to
apply migration 4, then hard-reload DM and viewer tabs. Migration 4 adds a separate
per-map wall-type settings table; it leaves migration 3, cache tokens, snapshots,
source uploads and any legacy disabled_wall_types column intact. See
[map controls](map-controls.md), [deployment](deployment.md) and [testing](testing.md)
for compatibility and validation guidance.

## Separate wall editor and UVTT saving

Open **Walls → Open wall editor** in the fog editor. This is a separate screen;
opening it does not activate the map or change fog.

1. Select **Add wall** and a wall type, then click the start and end on the map.
   Endpoint snapping is on by default (10 screen pixels). Escape cancels the start.
2. Select **Remove wall** and click within 10 screen pixels of a segment to delete it.
   **Change wall type** applies the selected type to a clicked segment.
3. Use Undo/Redo, Ctrl/Cmd+Z and Ctrl/Cmd+Shift+Z for draft edits. Drag pans,
   the wheel zooms and F fits. Panning never adds a segment.
4. **Save wall set** applies the draft to this map and saves an immutable,
   reusable wall-only UVTT source in this campaign. There is no Apply confirmation.
   Return to the fog editor; refresh saved sources if another tab is already open.
5. **Download UVTT (current draft)** exports without saving or applying. Tick
   **Include map image in download** for a self-contained map; otherwise it is
   a wall-only file. Pixels per grid defaults to 70 and controls export units,
   not the size or position of walls on the artwork.

Save bakes the current alignment into image-pixel coordinates and resets alignment
to offset 0 / scale 1 without moving walls. Door settings, disabled wall types,
fog operations and snapshots are retained. All stored segments are editable,
including types hidden or disabled in the fog editor. Ethereal segments never block.
Original uploaded sources and other maps are not modified. Repeated identical
saves reuse the same source; changed bytes create a new source.

Changes are not autosaved. Leaving with unsaved changes warns; Reload asks before
discarding them. A 409 conflict means another tab changed walls/alignment/artwork.
Download the draft without artwork to rescue it, then reload before saving.
Boundary changes can expand old reveals: blank players first and inspect the
exact preview after saving. Download limits follow storage.max_upload_mb.

The UVTT core has fallback geometry; exact Looking Glass types and nonblocking
segments use a versioned extension. Other VTTs may interpret extended types
differently. See [wall editor details](wall-editor.md) and
[deployment](deployment.md). The original dedicated wall editor adds no migration.

## Sidebar panels and wall appearance

On the battle map screen, Players, Fog, Map passages, Walls, Saved wall sources
and Replace map image start closed. Map passages appears immediately above Walls.
These peer sections form an accordion: opening one closes any other open peer.
Wall legend and types starts open, is excluded from the accordion, and stays in
its manually selected open/closed state while other sections change. Alignment
starts closed inside Walls and is independent of the peer accordion; opening it
does not close Walls. These defaults are reapplied on page reload.
In the wall editor, Save and export below the tools is also collapsible and
starts expanded. Collapsing panels does not reset controls or discard edits.

Both editors have a Wall width slider (0.5–10 screen pixels), defaulting to the
battle map's existing 2-pixel base width. The preference is saved per map in
this browser and reused when opening either editor. Width stays constant while
zooming. Battle-map doors and secret doors retain their double-width styling.
This changes only the DM overlay, not fog boundary thickness, wall coordinates,
UVTT exports, or the player image. Sidebar open/closed state resets on reload.


## Door arrows: visibility, color and clicking

The admin and viewer arrow toggles are independent per-map preferences. A single
admin click on an ordinary/unlocked arrow reveals the destination, overriding
Hide mode. Viewers cannot follow passages. Locked/unlocked doors look ordinary to
viewers. Undiscovered secrets and Exit-only portal arrows never appear there.

Regular door arrows require a revealed source and hidden adjacent area. Secret
door arrows persist after discovery/use. Portal arrows persist after remote
reveal. Entry arrows are clipped to revealed source areas; admin-only Exit hints
may appear in fog when an incoming Entry is visible. Raster sampling, wall gaps
and tight rooms have the same limitations as area reveal. See Passages.md.

## Locked and unlocked doors

| Admin target | Single click | Double click |
|---|---|---|
| Locked arrow | No action | Unlock, fog unchanged |
| Unlocked arrow | Reveal destination | Lock, fog unchanged |
| Undiscovered secret arrow | No action | Discover as configured, fog unchanged |
| Normal portal Entry arrow | Reveal remote destination | No action |
| Exit-only hint | No action | No action |
| Door segment | Existing manual fog rules | No passage-state change |

Managed arrow singles wait 400 ms so a double gesture cannot first reveal.
State changes, another target, drag, wheel or blur cancel pending clicks. Portal
Entry sides have separate gesture identities. Secret portal state is independent
per Entry; Exit roles have no state. Configure secret outcomes in the wall editor.

Fog Undo affects reveal/hide history, not locks or discovery. Reset restores
authored states and hides secrets again; Restore/restart retains runtime state.
Saving/replacing walls clears runtime overrides for the replaced set. Export
contains authored states only. Locks never prevent a DM's manual reveal tools.
Locked door arrow color customizes the admin hint; viewers use the regular color.

## Independent admin and viewer arrow visibility

| Admin arrows | Viewer arrows | Result |
|---|---|---|
| On | On | Both displays show eligible arrows. |
| On | Off | DM sees/clicks arrows; players see no arrow hints. |
| Off | On | Players see hints; DM arrow overlay and arrow click targets are hidden. |
| Off | Off | Neither display shows arrows; saved colors are retained. |

These settings affect arrow indicators, not actual door wall segments or the map image. Show walls and per-type Show controls are unchanged. Hiding admin arrows prevents unlocking through a hidden locked arrow; wall segment double-clicks do not toggle passage state. Viewer hints remain noninteractive. The in-editor Player preview (opaque fog) is still the admin overlay with opaque fog; use Open exact player image for the viewer-specific arrow setting.

Both flags survive reloads/restarts and map activation/Reset. Switching visibility does not change designed/runtime door types or fog operations/checkpoints. An admin-only visibility update does not bump the viewer's image version or notify viewers; other admin tabs receive it on the existing 15-second poll. Viewer visibility/color changes use the existing live image refresh. Color inputs are disabled only when both screens are off or saving is in progress. Failed saves restore confirmed values.


## Viewer double-click room zoom

Double-click a revealed area on the viewer screen to zoom to that individual room/area and center it with a small margin. If that area's fitted camera position and zoom already match the current view, another double-click returns to the overview bounding all currently revealed areas and centers the visible battle map. Double-clicking a different revealed area switches focus to that area. If you have manually moved away from a room's fitted view, double-click first refits/recenters it rather than toggling out. With only one revealed room, room and overview framing can be identical.

The viewer Fit button and F shortcut always leave room focus and show the revealed-area overview. Dragging, wheel zoom and pinch still work normally. On touch screens, two stationary taps also work; taps must be within 400 ms and 12 screen pixels. Pan/Space-drag, pinch/multitouch, non-primary clicks, wheel zoom, pointer cancellation and window blur cannot complete an old tap pair. No admin fog/door gesture is changed.

Hidden/fogged areas and out-of-map clicks do nothing; the viewer cannot use zoom to reveal rooms or control locks. Eligible areas are the same calibrated raster rooms/components used by fog reveal, so incomplete walls or disabled door boundaries may make multiple rooms one zoom area. Click visible interior pixels for the most predictable selection; hidden open pixels near a dilated wall are still rejected.

A focused room is refitted on viewer resize. When a newly revealed area appears in a live update, room focus is cleared and the viewer fits/centers all visible areas. For other updates the focus point is revalidated: focus is retained if still visible, otherwise the viewer returns to the remaining revealed-area overview. Switching/blanking maps clears focus. A late lookup cannot override newer navigation or map state. Manual wheel/drag clears room-focus tracking; existing overview fitting on subsequent live refresh remains available. Camera state is local to this viewer tab, not a saved campaign preference or a change to other viewers.

This feature does not add the previously rolled-back Center/Fit admin toggles. Split admin/viewer arrow visibility and locked-door behavior remain unchanged.


## Double-click in admin to control viewer zoom

Double primary click/tap a revealed area of the admin fog map to send a camera command to all currently connected viewers for that campaign. Each viewer uses its existing behavior: if the selected room is already fitted and centered in that viewer, show the all-revealed overview; otherwise fit and center the room. The admin viewport never moves as part of this command. Different viewers may toggle differently if their current local camera poses differ.

Viewer-local double-click, Fit/F, drag, wheel, pinch and resize behavior remain available. A local viewer double-click still changes only that tab. A viewer fetches the current authorized area bounds before applying an admin command; stale, duplicate, wrong-map and superseded commands are ignored. Newer local navigation cancels a pending camera lookup.

To separate area double-clicks from fog actions, ordinary primary single-clicks now wait 400 ms. A nearby second click within that interval cancels the pending single and sends zoom instead—even in Hide mode—so the gesture does not reveal/hide a room first. The double-click tolerance is 12 screen pixels. Right-click inverse fog actions remain immediate. Another target, state/mode change, mutation, camera movement, drag, pinch, pointer cancellation, keyboard/resize or window blur cancels pending area work rather than allowing a delayed fog action.

Regular arrows and managed door/arrow gestures take priority and are not reinterpreted as area zoom: regular arrow reveal, locked-arrow double-click unlock and unlocked-arrow double-click lock remain unchanged. A hidden-area double-click sends no zoom and does not fall back to revealing it; use a single click to reveal normally. The selected map must already be active on viewers—this action never activates or switches maps automatically.

Commands use live WebSockets and are ephemeral, not stored camera preferences. The admin reports when no viewer screens are connected. Disconnected or not-yet-opened screens do not replay old zoom commands; issue the double-click again after reconnecting. The success toast counts subscribed screens, not confirmed camera acknowledgments. Reload both admin and viewer tabs after installing this update. Camera commands do not change fog operations, locks, checkpoints, versions, arrow visibility or the database.


## Revealing another area clears room focus

If a viewer is focused on one room, revealing another area returns it to the overview of all currently revealed areas and centers that visible portion of the battle map. It works for focus created by either a viewer-local double-click or an admin remote double-click. Reveal all, an arrow revealing a destination, re-revealing a hidden room and Undo of a hide also reset focus when they make an additional area visible.

The new area need not expand the outer visible bounding box. Replacing one visible area with another between displayed states is also detected, even when the visible area count stays equal. Repeating Reveal on an already revealed room does not reset focus. Arrow visibility, color and lock/unlock-only changes keep room focus when area geometry/visibility is unchanged. Hiding another room alone also preserves focus; hiding the focused room still falls back to overview through existing validation.

After the overview reset, a fresh explicit admin/viewer zoom can focus a room again. Old in-flight area lookups cannot restore the discarded focus. The viewer applies the reset with the newly decoded map image; a newly visible area inside unchanged overview bounds still triggers it. Detection compares the last displayed state with the next displayed state, rather than replaying transient states that never reached the viewer.

Areas follow the fog engine's raster room components. Changing wall geometry/calibration or boundary settings can change those components' footprints and may reset focus as newly represented visible areas. Routine lock/unlock keeps those footprints unchanged. Existing manual pan/zoom, overview behavior, Fit/F and both double-click paths are otherwise unchanged. Reload viewer tabs after the upgrade.

## Portal authoring

Open Walls → Open wall editor → Portal configuration. Select one Portal section
and edit its two sides using compass designations (North is the top of the map).
Fresh sides start Unconfigured; configuring one defaults only an untouched opposite
side to None. Entry/Both sides select the other Portal section and paired Exit
heading. Select Exit, Unconfigured or None; Unconfigured/None changes to Exit
inside the popup. Existing Both targets keep their Entry role, while Entry-only
targets remain disabled. Every Exit needs an incoming Entry; shared Exits are valid.
A pair still contains exactly two sections, each allowing at most one None side.

Apply commits popup edits to the draft in one Undo/Redo step. Close/Escape asks
before discarding unapplied popup edits; previously applied edits remain in the draft. Save/Download rejects incomplete graphs. Reset/unpair keeps both sections as
Unconfigured Portal elements. Stored numeric indices and runtime behavior are
unchanged. See [passages](Passages.md) and [wall editing](wall-editor.md).

## Portal overview and matching visible arrows

Use Portal overview in the wall editor to inspect every side's authored role,
initial state, discovery outcome and counterpart connections. Use the overview
inside Portal configuration to include pending local edits without applying them.
Drag either dialog by its title bar or focus the title bar and use arrow keys;
Center repositions it. These remain modal dialogs, so the map is visible behind
them but background edits remain blocked.

The admin fog page highlights one visible Entry/Exit route at a time. Default is
5 seconds per route, adjustable from 1–15 seconds. The complete color-alternation
cycle is 1.2 seconds and independent of route dwell. Disable Cycle visible Entry/Exit pairs to pause. Preferences are saved
only in this browser for this map. Two or more routes must qualify, and both arrow
polygons must intersect the current viewport; pan/zoom to bring a pair into view.
Shared Exits and Both roles are matched by exact side, not just by portal wall ID.
The status line identifies the current sections, compass sides and effective
Entry state. Viewer images, arrow hit targets and fog operations are unaffected.
Highlights alternate bright yellow with a black outline and deep blue with a white
outline at full opacity; neither phase fades away. Reduced-motion preferences use
a steady bright-yellow highlight while retaining route rotation. Wall-editor
portal labels now have semi-transparent dark backing badges. See
[wall editing](wall-editor.md) for presentation details.


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

## Collapsible map-editor help

The left sidebar’s `? Help` control contains eight independent help topics:
Players; Fog and navigation; Door arrows; Wall alignment; Wall types; Map
passages; Saved wall sources; and Replace map image. Help and every topic start
collapsed on each page load. Expand a heading with a pointer or Tab followed by
Enter/Space. Multiple topics can remain open, independently of the editor’s
control-panel accordion. Expansion state is not persisted across reloads.

Saved wall sources contains five further collapsed subsections: Sources and
wall sets; Save and apply walls; What applying changes; Reuse, refresh and
delete; Supported files. Closing a parent hides its children without resetting
their open state until the page is reloaded.

For a campaign with one map, Map passages and its help topic are hidden; the
other seven help topics remain available. With two or more maps, all eight are
shown. Reload the editor after changing the campaign’s map count. This changes
presentation only, not saved endpoints or passage APIs.

Static sidebar instructions live in Help. Live errors, warnings, counts and
statuses stay beside their controls; action-specific modal guidance is unchanged.

### Help text reference

#### Players

Show to players makes this map the active player display.
Blank replaces the player display with a waiting screen.
Open exact player image opens the player rendering in a separate tab so you can check what is visible.

#### Fog and navigation

Select Reveal area or Hide area, then single-click inside a room to change its fog. Single-click actions wait 400 ms so they can be distinguished from double-clicks.
Double-click a revealed area to toggle player zoom without changing its fog. Clicks on doors and arrows take priority over area clicks.
Navigate the DM map:
Right-drag or hold Space and drag to pan.
Use the mouse wheel to zoom.
Press F to fit the map.

Shortcuts:
R — Reveal mode.
H — Hide mode.
Ctrl+Z — Undo the last fog action.

#### Door arrows

Single-click a door arrow to reveal through that doorway.
Double-click a locked door arrow to unlock it without revealing. Double-click an unlocked door arrow to lock it.
Reset restores the designed door states. Ctrl+Z undoes fog reveals, not door locking or unlocking.

#### Wall alignment

Use Alignment when the wall overlay does not line up with the map image.
Offset X / Y adjusts the horizontal and vertical position of the source walls.
Scale X / Y adjusts their horizontal and vertical size.
Use the arrow buttons for small position adjustments. Hold Shift for a 10-pixel nudge.

Select Apply alignment to save the alignment settings.
Check the overlay against recognisable features, such as room corners and doorways. If the walls match in one part of the image but drift elsewhere, check the scale as well as the position.
Coordinate conversion:
image coordinate = (source wall coordinate − offset) × scale
The offset is subtracted before scaling. Increasing an offset therefore moves the walls in the opposite direction along that axis.

#### Wall types

Show and Enabled serve different purposes:
Show controls whether a wall type is visible in the DM’s wall overlay. It does not change the fog boundaries.
Enabled controls whether a wall type is used when calculating fog boundaries. Select Apply wall types to apply changes to these settings.

Disabling a wall type does not delete its wall segments. You can enable them again later.
Ethereal walls never form fog boundaries. Whether doors divide the map into separate areas also depends on Doors split areas.

#### Map passages

Map passages connect locations on different maps—for example, stairs between dungeon floors.
Select Add passage endpoint to create an endpoint on the current map. Click an existing passage marker to edit it.
Marker letters identify the passage type:
S — Stairs
L — Ladder
H — Hole
P — Portal
C — Climb
X — Custom

A passage endpoint defines one end of a connection. Configure its destination to connect it to an endpoint on another map.
Creating or editing a passage does not move the players. Travel is a separate DM action.

#### Saved wall sources

##### Sources and wall sets

A saved source is a Foundry VTT or Universal VTT file stored for reuse within this campaign.
A source can contain one or more scenes. Each scene provides a separate wall set containing its walls and doors. Choose the wall set that matches the current map image.

##### Save and apply walls

Choose a supported file and select Save source. This saves the file to the campaign library; it does not change the current map.
Select the file under Saved source.
Select the matching scene under Wall set. Use its name, wall and door counts, and position in the source file to distinguish similar entries.
Choose your alignment option:Checked: Auto-align for this map calculates alignment for the current map image.
Unchecked: the map keeps its current offset and scale.

Select Apply selected wall set to replace the current map’s walls.
Check the wall overlay and player preview. If necessary, adjust the alignment under Walls → Alignment.

Selecting a source or wall set does not apply it. The map changes only when you select Apply selected wall set.

##### What applying changes

Applying a wall set replaces the current map’s existing walls. It does not merge wall sets, change other maps or modify the saved source.
The map image, Doors split areas setting and existing fog history are retained.
During play, blank the player display before applying a different wall set. Existing fog actions may reveal different areas when replayed against the replacement walls. Check the player preview and reset fog if necessary.

##### Reuse, refresh and delete

Reuse: select the same saved source on another map in this campaign without uploading it again. Saved sources remain available after a restart.
Refresh sources: reload the list of saved sources.
Delete source: remove the source from the campaign library. Walls already applied to maps remain unchanged.

Editing a map’s walls does not update the saved source. To use the source in another campaign, save the file in that campaign separately.

##### Supported files

Supported sources include Foundry scene or adventure JSON, legacy Foundry NeDB .db files, and Universal VTT .dd2vtt, .uvtt and .df2vtt files.
Foundry LevelDB directories cannot be uploaded directly; export the scene as JSON instead. A .db extension alone does not mean a file is supported—arbitrary SQLite databases are not wall sources.


#### Replace map image

Use Replace map image to replace the artwork for the current map.
Choose an image file, then select Upload.
After uploading, check that the walls line up with the new image and inspect the player preview before continuing play.

## Room names and Markdown notes

1. Open a map in the admin editor and expand Room notes on the right.
2. Enable “Select room (fog unchanged)”. Click inside any room, including
   hidden rooms. Selection ignores door/transition actions while this mode is on.
3. Click Edit room. Enter a room name (up to 200 characters) and Markdown (up to
   100,000 characters), then Save room to return to read mode. Cancel discards
   the draft and returns to the saved name and rendered notes.
4. Disable selection mode. Reveal a room normally to show its notes. A repeated
   reveal click on an already revealed room shows the notes without changing fog,
   fog version, action history, or undo. Hide mode still hides revealed rooms.
5. Use Room notes to collapse/expand the right panel. The browser remembers the
   preference. Revealing rooms updates the content without overriding a deliberate
   collapse. On narrow screens the panel stacks below the map.

Headings, emphasis, lists, links, blockquotes, fenced code, tables and strikethrough
are supported. Raw HTML is escaped and rendered output is sanitized; images are
not rendered, preventing remote-image tracking. Notes remain DM-only.
Unsaved edits prompt before selecting another room or leaving the page. Cancel
restores the saved version. Concurrent saves are rejected by revision check.

Room identity uses an exact fingerprint of its rasterized interior, not its
transient component number. Unchanged interiors retain notes after unrelated wall
changes. Changes to the room outline, calibration, image dimensions or work
resolution may detach the old record. Detached notes remain in SQLite and appear
as inactive in the admin list API; automatic reassignment and a recovery UI are
not provided. Back up the database before changing geometry. Reset/undo affect
fog only, not saved notes. When multiple named rooms are revealed together, the
panel selects the first newly revealed named room alphabetically; click another
revealed room in reveal mode to inspect its notes. Initial page load does not
arbitrarily select one of the already revealed rooms.

### Room notes: read mode, edit mode and formatting

Rooms open in read mode: only the room name and rendered notes are displayed,
with an Edit room button. Edit mode hides that read view and displays only the
name/Markdown editing fields, formatting toolbar, and Save room/Cancel controls.
The room selection checkbox remains accessible while editing; the room status message is hidden.
Automatic room switching is paused while the editor is open, even before typing.
Saving failure keeps the draft open; a successful save returns to read mode.

The toolbar supports bold, italic, strikethrough, H2 headings, bullet/numbered
lists, blockquotes, inline code, fenced code blocks, links and horizontal rules.
Select text to format it; list/heading/quote buttons apply to the selected lines.
Link inserts a Markdown link with an editable example URL. Formatting changes
remain drafts until Save room. Existing notes need no data conversion.

Paste Markdown using Ctrl+V or Command+V in the notes field. Clipboard
text/markdown is preferred when available; otherwise text/plain is inserted.
Markdown syntax is preserved verbatim, not escaped or converted to rich text.
Paste Markdown also offers a clipboard-read button; if browser permissions or
secure-context requirements prevent reading, use the normal keyboard paste.
Copying from a rich-text web page uses its plain-text clipboard representation;
HTML-to-Markdown conversion, image pasting and file import are not implemented.
The 100,000-character limit also applies to toolbar insertion and pasting.


## Importing room notes from Markdown

Open Import room notes in the right-hand Room notes panel, choose a UTF-8 `.md`,
`.markdown` or `.txt` file, and click Import notes. The importer uses the highest
heading level actually present (the lowest number: H1 before H2). Each heading
at that level becomes a room name. Everything after it, up to the next heading
at the same level, becomes that room's Markdown note. The room-name heading
itself is excluded; lower headings remain in the note. ATX (`#`) and Setext
(underlined) headings are supported. Headings inside code, quotes or lists do not
split rooms. Heading inline formatting is reduced to a plain name.

Example:

```markdown
## Entrance Hall
A cold breeze blows through the broken doors.

### Features
- Two cracked statues.

## Burial Chamber
Dust covers the stone coffins.
```

This creates Entrance Hall and Burial Chamber; Features stays in Entrance Hall's
note. See docs/examples/room-notes.md for another complete file. A single `# Dungeon`
document title above `## Room` headings creates ONE imported room named Dungeon;
omit that title if the H2 headings should be individual rooms. Preamble text before
the first room heading is ignored and reported. Reference-link definitions should
be included in each section that needs them; definitions elsewhere are not copied.

After importing, enable Select room (fog unchanged) and click any room.
Click Edit room. Use imported room notes is available inside the editor whether or not the room already has a name or note.
Choose a name from the dropdown; the name and note load together into an unsaved
edit draft. Review or adjust them, then Save room to assign them. Cancel discards
the selection. Selecting an imported entry replaces both fields in a draft, including for existing named rooms.

Imports are stored per map, persist across restarts, and do not affect fog or
existing rooms. Assigned names are hidden from subsequent dropdown choices until released. Reimporting identical
name/content pairs does not duplicate them. Changed content appends a new entry
rather than replacing a previous entry or assigned room. Same-name variants have
an ID suffix in the dropdown. Unassigned imported records can be removed using List imported notes (see below).
Reload the editor to see imports made by another admin session.

Limits: 1 MiB per UTF-8 file, 500 room sections per import, 200 characters per
room name, and 100,000 characters per note. Empty sections are allowed. Invalid
files are rejected as a whole, without partially adding entries. Imported content
is sanitized by the existing renderer after assignment, like manually entered notes.

### Clearing and replacing room metadata

Import room notes is a collapsible section, closed by default on each page load.
Click its summary to expand it. It remains collapsible independently of the whole
right panel. An explicit closed-details CSS rule keeps its form hidden even with
generic form layout styles. Expanding it is not persisted between page loads.

To remove metadata, click Edit room and Clear name and notes, then Save room.
Clear changes the draft only; Cancel restores the previous saved content. You
can also erase either field individually: names are optional, so notes-only rooms
are supported. Both blank fields clear the room's displayed metadata, without
changing fog, walls, imported entries or other rooms. Blank names display the
placeholder “Unnamed room”. This clears the stored text, not an encrypted/secure
wipe of historical database backups.

The imported-note dropdown is offered for every selected room inside Edit room only.
Choose a replacement to fill the current edit draft with the imported name and note.
Save room applies it; Cancel restores the previous values. Replacement is still
subject to revision and geometry checks. While editing, choose another imported entry directly from the dropdown; a different
unsaved draft prompts before being replaced.

## When imported-room replacement asks for confirmation

“Replace unsaved room name and notes with the imported entry?” is only appropriate
when there are unsaved name/note differences AND the chosen imported entry differs
from that draft. It is not a warning about replacing already saved metadata:
opening Edit room and selecting a replacement before changing any fields does not prompt. Save room
still controls whether it is persisted; Cancel restores the saved content.

The check compares actual field contents with the selected room's saved values.
Editing and then undoing/reverting to the saved content is clean again. Room names
are compared trimmed (matching server save behavior); Markdown preserves whitespace
other than normalized newline encoding. Choosing an entry identical to the draft
is a no-op and does not prompt. Clearing an already empty room stays clean.

OK replaces the draft once. Cancel leaves it unchanged. Neither choice should
redisplay the modal by itself. The imported-room dropdown always resets to its
placeholder and is never automatically remembered/restored between refreshes or
rooms. Other persistent dropdowns retain their existing behavior. Deploy the fix
and refresh the page; old cached dropdown choices are ignored without requiring
all browser storage to be cleared.

### Imported notes picker location

Select a room, then click Edit room. Use imported room notes appears at the top
of the edit form, above Room name, and stays available while editing. It is hidden
in read mode and when no room is selected. The separate Import room notes upload
section remains outside the editor and starts collapsed as before.

Selecting an entry updates the draft only. Save room persists it; Cancel restores
the saved content. The dropdown prompts once only if a different unsaved draft
would be discarded; choosing an identical entry is a no-op. The picker is disabled
with the other form controls while a save is pending.

## Automatically edit unnamed rooms

Enable Select room (fog unchanged) and click an unnamed room. The Room notes
editor opens directly, so you can enter a name or choose Use imported room notes
without clicking Edit room first. An empty or whitespace-only name counts as
unnamed; a room with notes but no name also qualifies, and its notes are preserved.

The editor starts clean: merely opening it does not save anything, mark content
as changed or modify fog. Save room persists edits; Cancel returns to the saved
read view and does not immediately reopen the editor. A later explicit selection
of that unnamed room opens editing again. Existing unsaved-change protection
still applies when switching rooms.

Named rooms, normal fog reveal clicks, background refreshes, and selections when
the checkbox is unchecked do not auto-open editing. A deliberately collapsed
right panel stays collapsed, although its internal state switches to editing;
expand it to see the form. When expanded, the room-name field receives focus.

## Hide already assigned imported names

Use imported room notes now lists only names not already saved on a room in this
map. This includes the room currently being edited: its saved name is omitted
from the dropdown, while its current name and notes remain in the editing fields.
Manual room names count too, even when their notes differ from the imported text.
Name matching ignores case and surrounding whitespace. All imported variants with
the same assigned name are hidden. Other maps have independent availability.

Save room commits the assignment and refreshes availability. Merely selecting an
entry, editing a draft, or cancelling does not reserve/release a name. Save a
rename or clear the name to make the previous name available again, provided no
other saved room still uses it. Clearing only the note does not release the name.
The library remains intact. If every imported name is assigned, the dropdown is
disabled and says “All imported room names are assigned”.

Availability refreshes on opening the editor, after saving, and after import.
Opening an editor again picks up another session's saved changes; this is dropdown
filtering, not a database uniqueness lock against simultaneous manual assignments.
Preserved room-note records detached by geometry edits also reserve their saved
names until those records are renamed/cleared or otherwise managed in the database.

## See which room is being edited

Entering Room notes edit mode (manually or automatically for an unnamed room)
marks the room interior with an amber tint and boundary on the admin map, plus
an Editing room notes label. The mark follows map pan/zoom and appears even for
hidden rooms. It is local to this admin page; viewers never receive it.

Save success, Cancel, or changing to another room/read mode removes the highlight.
Failed saves keep the editor and mark. It is a separate visual layer: underlying
fog/reveal history never changes, so removing it restores the original map view
without replaying or undoing any fog operation. Geometry changes invalidate the
mark; if the selected room no longer matches, reselect it to get a new highlight.

## List and delete imported notes

Expand Import room notes and click List imported notes. A dialog shows every
imported name and its Markdown source, including assigned entries hidden from the
assignment dropdown. Notes sections start expanded and can be collapsed. Names
have import IDs to distinguish variants. Refresh list reloads assignment status.

Status is Unassigned, Assigned · name and notes match, or Assigned · saved notes
differ from this import. Assignment follows the existing trimmed/case-insensitive
room-name matching within this map, including manually entered names and preserved
inactive geometry records. Notes-match means at least one matching-name saved room
has the same Markdown (normalized CRLF); modified assigned notes remain protected.

Only unassigned entries have Delete imported entry. Confirm to permanently remove
that one library record. Deletion does not remove map rooms, room notes, walls or
fog. The server rechecks assignment under a write transaction, so an entry assigned
by another session since opening the dialog cannot be deleted. The list and picker
refresh after deletion; errors are shown with refreshed status where possible.
Unsaved drafts do not count as assignments. A deleted entry can be imported again.
Close or Escape exits the dialog. The browser list shows note source as text rather
than executing or rendering uploaded HTML. Back up SQLite before deleting records
if you need recovery; there is no undo for library deletion.

## Show named and unnamed areas

With Select room (fog unchanged) checked, a Show named / unnamed areas button
appears directly below it. Click to show a translucent green tint for areas with
saved names and red for unnamed areas, plus a text legend/counts. Click again to
hide the overlay. It starts off on page load. Unchecking Select room removes the
colours and hides the button; rechecking reveals the button with the overlay off.
The checkbox and its button remain accessible during note editing so the overview
can be toggled while the amber edit marker remains on top.

Classification uses saved names only: whitespace-only or missing names count as
unnamed, even if notes exist. A saved name turns its current matching area green;
saving a cleared name turns it red. Draft text does not change colours until saved.
Colours cover both hidden and revealed areas, are local to the admin page, and do
not alter fog, player images, undo history or metadata. Map pan/zoom moves the
colours with the artwork. Wall pixels stay transparent.

Areas follow the fog engine's connected-region boundaries, including exterior
open regions if present. Counts are detected areas, not imported-note entries.
A detached old room record whose saved geometry no longer matches does not name
a different current area. The overlay reloads after successful room saves and
geometry changes. To see another admin session's metadata changes, hide/show the
overview again. Removing the overview leaves the original map/fog display intact.

## Imported room list: fixed header and unassigning

Open Room notes → Import room notes → List imported notes. The title, Close,
Refresh list, instructions and status stay fixed above the scrollable entries.
The list accepts keyboard focus for scrolling; individual Markdown blocks retain
their existing independent scrolling for long notes.

Assigned entries provide **Unassign from rooms**. Confirm to clear both the saved
name and Markdown from all matching rooms on this map. Matching trims surrounding
whitespace and ignores case, exactly like library availability. The operation
also clears custom room-note edits; the original imported text remains unchanged.
If multiple imported entries share the same normalized name, they all become
available once the matching room assignments are cleared. Other maps are untouched.

This is immediate, not a draft edit, and has no Undo. Cancel at confirmation to
leave data unchanged. Save or cancel any pending room draft first. During a
request, actions and Close/Escape are disabled to prevent duplicate operations.
After success the imported picker, dialog status, selected room (if affected),
and named/unnamed overlay refresh. An unassigned selected room returns to read
mode; use Edit room to assign another entry. Fog, walls and player images do not
change. Delete imported entry remains available only for unassigned entries.

Existing geometry-change reconciliation continues to remove invalid assignments
when walls change; this manual action releases an assignment without editing walls.
