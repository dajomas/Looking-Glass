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

