## Room-note persistence and rendering

An appended SQLite migration creates room_notes with a cascading map foreign key,
a geometry key, selection anchor, name, Markdown and optimistic revision. No
existing migration is rewritten. The service hashes packed component membership
plus image/work dimensions and scale, caching keys in AreaMap.region_signatures.
This conservatively avoids assigning notes to the wrong room after relabeling.
Inactive records survive geometry edits and are discoverable in the admin list API.

Mistune renders escaped Markdown; Bleach applies an explicit HTML tag, attribute
and URL-protocol allowlist. Images and active HTML are not allowed. Only sanitized
server HTML is inserted into the preview; room names use textContent. The viewer
payload and viewer app do not include note content.

The standalone room_notes.js owns panel state, dirty protection and selection.
The editor refreshes named-room visibility on applied fog/wall state changes,
including managed-door reveals, undo and reveal-all. Explicit selection mode has
priority over map actions; outside it, existing delayed singles/doubles and door
hit-testing remain in place. Multiple newly revealed named rooms choose the first
alphabetically. Notes save without fog invalidation; other admins see updated
content when they reselect the room. There is no live collaborative note editor.

### Exclusive room-note read/edit modes

LGRoomNotes tracks editMode separately from the map's room-selection checkbox.
Read and form containers use mutually exclusive hidden states (enforced in scoped
CSS). Edit mode suppresses automatic room switching, including pristine drafts.
Save disables editing controls until completion and blocks selection while pending;
errors preserve the draft, successful saves and Cancel restore read mode.
The toolbar inserts Markdown source with textarea selection APIs and updates dirty
tracking. Clipboard paste prefers text/markdown over text/plain; rich HTML is never
inserted into the preview. Clipboard-read completion is guarded against changed
room, edit mode and draft state. Server rendering, sanitization, permissions,
revision checks, endpoints and database schema are unchanged by this UI follow-up.

