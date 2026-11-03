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

