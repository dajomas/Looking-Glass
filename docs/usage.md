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
