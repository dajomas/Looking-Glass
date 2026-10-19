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
map-controls.md and the Patch notes for compatibility and test limitations.

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
[patch notes](../Patch/wall-editor-uvtt.md). This patch adds no migration.

## Sidebar panels and wall appearance

On the battle map screen, Players, Fog, Walls, Saved wall sources, and Wall
legend and types are separate collapsible sidebar panels. Closing Walls does
not hide Saved wall sources or Wall legend and types. They start expanded;
Alignment remains inside Walls and Replace map image retains its behavior.
In the wall editor, Save and export below the tools is also collapsible and
starts expanded. Collapsing panels does not reset controls or discard edits.

Both editors have a Wall width slider (0.5–10 screen pixels), defaulting to the
battle map's existing 2-pixel base width. The preference is saved per map in
this browser and reused when opening either editor. Width stays constant while
zooming. Battle-map doors and secret doors retain their double-width styling.
This changes only the DM overlay, not fog boundary thickness, wall coordinates,
UVTT exports, or the player image. Sidebar open/closed state resets on reload.


## Door arrows: visibility, color and clicking

**Show door arrows (admin)** and **Show door arrows (viewer)** appear above the color pickers. They are independent server-saved per-map preferences. New maps default both on; the upgrade copies the old shared value to both flags on existing maps. Admin visibility controls the admin overlay and arrow hit targets. Viewer visibility controls the composited player image and exact player-image preview. Colors are retained while hidden, and both color inputs remain available if either screen is enabled. Regular arrow color defaults to `#46c0ff`; locked arrow color defaults to `#ff9f43`.

Left-click or tap an arrow in the admin fog editor to reveal the hidden area behind that arrow's door. The cursor becomes a pointer over the visible arrow. This overrides the selected Hide mode for that click only: the selected mode is not changed. Ctrl+Z undoes the resulting reveal normally. Arrows update when the room is revealed, including new arrows toward further hidden destinations. Active-map viewers update through the existing live-refresh mechanism. If the map is not currently shown, the existing offline-reveal warning still applies.

Right-click keeps the normal inverse reveal/hide behavior rather than following the arrow. Drag, Space-drag and pinch remain pan/zoom gestures. Transparent space around an arrow is not a hit target. Clicks are ignored while the displayed fog/arrow overlay is loading or a write is in progress. A stale or rejected arrow click refreshes state and never falls through into a normal hide/reveal click. Viewer screens remain read-only; players cannot use arrows to change fog.

Only ordinary blocking doors separating distinct raster rooms with exactly one revealed side receive arrows. Secret doors, nonblocking/disabled doors, and map-edge segments without open areas on both sides are excluded. Arrow pixels are clipped to revealed open areas, independently of admin wall-overlay visibility. Detection inherits room-reveal gap/resolution limitations; tight rooms may clip arrows. Arrows follow hide/reveal/undo/reset/restore and boundary changes. Changing arrow visibility/color does not modify room reveals or add fog operations.


## Locked and unlocked doors

Design doors in the wall editor using Locked Door (`locked_door`, dashed orange `#ff9f43`) or Unlocked Door (`unlocked_door`, solid orange `#ff9f43`). The fog editor shows the current play-time type; the wall editor shows the authored design.

| Admin target | Single primary click/tap | Double primary click/tap |
|---|---|---|
| Locked door arrow | No action | Unlock only; destination fog stays unchanged |
| Locked door segment | No action | No action; use its arrow to unlock |
| Unlocked door arrow | Reveal the area behind the door, even in Hide mode | Lock only; do not reveal |
| Unlocked door segment | Normal selected reveal/hide mode | Lock only; do not reveal |

Managed door clicks wait 400 ms to distinguish a single from a double. Another target, a state change, another mutation, panning, wheel zoom or window blur cancels a pending click rather than allowing a delayed reveal on stale geometry. Drag/pinch behavior remains PanZoom behavior. Right-click on a locked target does nothing; right-click on an unlocked target retains the ordinary inverse fog mode. Direct segment hits use a 10-screen-pixel tolerance, adjusted for zoom. Hiding arrows prevents arrow interactions; visible unlocked segments can still be double-clicked to lock. Locked segments are protected from accidental single-click fog actions even when their overlay is hidden.

Locked door arrow color is a separate server-saved per-map picker beside the regular arrow color. Its default matches orange door walls; changing it affects locked arrows on both admin and viewer screens, not wall colors. Unlocked arrows always use the regular arrow picker, not the locked-arrow picker. Each screen's visibility toggle covers regular, locked and unlocked arrows together, independently of the other screen. Secret doors still do not generate hints. Viewer accounts cannot change door/fog state.

Locking and unlocking are persistent play-state changes, not fog-history actions; Ctrl+Z undoes reveals/hides but does not toggle locks. They preserve the revealed mask, even if Locked/Unlocked type boundary settings differ: boundary participation follows the authored type during play. Both door types still honor Doors split areas. Locks govern the door controls, not a DM's ability to manually reveal another room or use Reveal all.

Reset both covers the map and restores every door's authored locked/unlocked type. Choosing Reset when activating a map does the same. Undoing a fog Reset can restore fog history but does not restore discarded runtime lock changes. Switching maps with Restore and restarting the service retain runtime states. Saving/replacing a wall design discards runtime overrides for that wall set and establishes a new designed state. UVTT export from the wall editor uses the authored design, not session overrides.


## Independent admin and viewer arrow visibility

| Admin arrows | Viewer arrows | Result |
|---|---|---|
| On | On | Both displays show eligible arrows. |
| On | Off | DM sees/clicks arrows; players see no arrow hints. |
| Off | On | Players see hints; DM arrow overlay and arrow click targets are hidden. |
| Off | Off | Neither display shows arrows; saved colors are retained. |

These settings affect arrow indicators, not actual door wall segments or the map image. Show walls and per-type Show controls are unchanged. Hiding admin arrows prevents unlocking through a hidden locked arrow; visible unlocked wall segments can still be double-clicked to lock as before. Viewer hints remain noninteractive. The in-editor Player preview (opaque fog) is still the admin overlay with opaque fog; use Open exact player image for the viewer-specific arrow setting.

Both flags survive reloads/restarts and map activation/Reset. Switching visibility does not change designed/runtime door types or fog operations/checkpoints. An admin-only visibility update does not bump the viewer's image version or notify viewers; other admin tabs receive it on the existing 15-second poll. Viewer visibility/color changes use the existing live image refresh. Color inputs are disabled only when both screens are off or saving is in progress. Failed saves restore confirmed values.


## Viewer double-click room zoom

Double-click a revealed area on the viewer screen to zoom to that individual room/area and center it with a small margin. If that area's fitted camera position and zoom already match the current view, another double-click returns to the overview bounding all currently revealed areas and centers the visible battle map. Double-clicking a different revealed area switches focus to that area. If you have manually moved away from a room's fitted view, double-click first refits/recenters it rather than toggling out. With only one revealed room, room and overview framing can be identical.

The viewer Fit button and F shortcut always leave room focus and show the revealed-area overview. Dragging, wheel zoom and pinch still work normally. On touch screens, two stationary taps also work; taps must be within 400 ms and 12 screen pixels. Pan/Space-drag, pinch/multitouch, non-primary clicks, wheel zoom, pointer cancellation and window blur cannot complete an old tap pair. No admin fog/door gesture is changed.

Hidden/fogged areas and out-of-map clicks do nothing; the viewer cannot use zoom to reveal rooms or control locks. Eligible areas are the same calibrated raster rooms/components used by fog reveal, so incomplete walls or disabled door boundaries may make multiple rooms one zoom area. Click visible interior pixels for the most predictable selection; hidden open pixels near a dilated wall are still rejected.

A focused room is refitted on viewer resize. On live map updates the focus point is revalidated against the current revealed area: focus is retained if still visible, otherwise the viewer returns to the remaining revealed-area overview. Switching/blanking maps clears focus. A late lookup cannot override newer navigation or map state. Manual wheel/drag clears room-focus tracking; existing overview fitting on subsequent live refresh remains available. Camera state is local to this viewer tab, not a saved campaign preference or a change to other viewers.

This feature does not add the previously rolled-back Center/Fit admin toggles. Split admin/viewer arrow visibility and locked-door behavior remain unchanged.


## Double-click in admin to control viewer zoom

Double primary click/tap a revealed area of the admin fog map to send a camera command to all currently connected viewers for that campaign. Each viewer uses its existing behavior: if the selected room is already fitted and centered in that viewer, show the all-revealed overview; otherwise fit and center the room. The admin viewport never moves as part of this command. Different viewers may toggle differently if their current local camera poses differ.

Viewer-local double-click, Fit/F, drag, wheel, pinch and resize behavior remain available. A local viewer double-click still changes only that tab. A viewer fetches the current authorized area bounds before applying an admin command; stale, duplicate, wrong-map and superseded commands are ignored. Newer local navigation cancels a pending camera lookup.

To separate area double-clicks from fog actions, ordinary primary single-clicks now wait 400 ms. A nearby second click within that interval cancels the pending single and sends zoom instead—even in Hide mode—so the gesture does not reveal/hide a room first. The double-click tolerance is 12 screen pixels. Right-click inverse fog actions remain immediate. Another target, state/mode change, mutation, camera movement, drag, pinch, pointer cancellation, keyboard/resize or window blur cancels pending area work rather than allowing a delayed fog action.

Regular arrows and managed door/arrow gestures take priority and are not reinterpreted as area zoom: regular arrow reveal, locked-arrow double-click unlock and unlocked door/arrow double-click lock remain unchanged. A hidden-area double-click sends no zoom and does not fall back to revealing it; use a single click to reveal normally. The selected map must already be active on viewers—this action never activates or switches maps automatically.

Commands use live WebSockets and are ephemeral, not stored camera preferences. The admin reports when no viewer screens are connected. Disconnected or not-yet-opened screens do not replay old zoom commands; issue the double-click again after reconnecting. The success toast counts subscribed screens, not confirmed camera acknowledgments. Reload both admin and viewer tabs after installing this update. Camera commands do not change fog operations, locks, checkpoints, versions, arrow visibility or the database.
