## Passage UI and interchange

`static/js/portal_editor.js` provides a separate modal, using atomic batch draft
changes in admin_wall_editor.js. Existing coordinate edits preserve metadata;
paired elements cannot be independently removed/retyped. Side labels correspond
to the directed segment normal. Both editor and fog overlays use per-side strokes
for portal type colors. `WallSegment` adds comparison-excluded keyword-only
passage/runtime dictionaries; positional six-field constructors remain valid.
Rows have an optional seventh authored-config object. UVTT extension v2 is emitted
when passage metadata is present; v1 ordinary sets remain readable/emittable.
Core fallback exports portals as opaque wall segments, not falsely linked doors.
The existing geometry checksum protects core/extension coordinate consistency.

