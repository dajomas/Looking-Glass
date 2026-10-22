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

Apply commits popup edits to the draft in one Undo/Redo step; Cancel/Escape discards
them. Save/Download rejects incomplete graphs. Reset/unpair keeps both sections as
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
overrides are saved independently and survive restart. Use **Apply session state**
to discover a secret or change its current availability. "Use authored setting"
clears the respective override. Saving authored settings does not clear overrides.

**Reset passage session states** restores authored values on the current map without
changing fog, endpoints or links. Ordinary fog resets do not reset these independent
cross-map states; reset them explicitly when starting a new session. There is no
combined reset operation in this first release.

### Preview and travel

- **Open destination in admin** now shows the saved destination map in admin and
  activates it for all connected viewers. It freshly checks both the saved reveals
  and the destination's currently revealed areas. If either exists, the existing
  **Show battle map** modal offers Restore last reveals, Reset reveals or Cancel.
  With neither, it activates the destination fully covered without a prompt.
  Cancel leaves both admin navigation and the active viewer map unchanged. A reserved
  blank admin tab is closed on cancellation/error; if popups are blocked or the
  reserved tab was closed, successful activation navigates the current admin tab.
  This is normal map activation, not passage Travel: it does not reveal the arrival
  area or apply passage-state approval rules. Save route edits first; changed or
  missing saved destinations are rejected. Restore uses the existing saved-checkpoint
  semantics; current reveals trigger the choice but do not replace an older checkpoint.
- Save configuration changes before using **Travel / show destination…**; travel uses
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

The passage form scrolls inside a dedicated body. Save endpoint, Delete endpoint,
Apply session state, Open destination in admin, Travel / show destination and Close
sit in a non-scrolling footer, so the main actions stay visible while editing long
configuration forms. Delete and Apply session state are hidden for a new endpoint.
Placement and destination-selection helpers remain next to their fields. The footer
wraps on narrow displays; the dialog remains bounded by the viewport. Travel keeps
its separate confirmation and transactional arrival policy.
