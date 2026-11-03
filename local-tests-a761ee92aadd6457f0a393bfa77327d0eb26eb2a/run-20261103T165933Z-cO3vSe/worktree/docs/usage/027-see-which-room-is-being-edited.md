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

