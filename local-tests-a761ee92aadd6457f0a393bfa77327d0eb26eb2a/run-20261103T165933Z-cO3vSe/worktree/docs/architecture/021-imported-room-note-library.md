## Imported room-note library

An appended migration creates imported_room_notes, cascade-owned by a map, with
name/Markdown, monotonic ID and SHA-256 content digest unique per map. Import
parses and validates first, then appends in one immediate SQLite transaction;
identical records are ignored, modified records append without altering prior
assignments. Neither importing nor saving notes changes fog.

room_note_import subclasses the existing Mistune block parser to record offsets
of document-level ATX and Setext headings. It slices normalized source between
headings at the globally smallest level, preserving lower headings and Markdown
source. Nested/container/code headings do not delimit records. UTF-8 BOM and CRLF
are accepted; invalid UTF-8, NULs and validation failures reject the complete file.
Preamble is deliberately omitted. Cross-section reference definitions are not
rewritten or copied. The library is loaded by the room UI on page initialization;
imports refresh it in-session. A generation counter prevents stale library loads
from replacing a newer import response. Picker assignment fills an unsaved draft
for every selected room, including rooms with existing metadata. Existing sanitization and
optimistic-save checks apply; library choices do not bypass those checks.

### Optional room names and reversible draft controls

An appended migration rebuilds room_notes with a relaxed name-length constraint
(0–200), copying geometry anchors, Markdown and revision unchanged. No imported
library rows are modified. Clearing saves empty strings in the existing row and
increments revision rather than deleting/recreating it; this preserves optimistic
concurrency against old clients. Payloads still use “Unnamed room” as a UI-only
placeholder for an empty name. Notes-only metadata is supported.

Clear name and notes changes the draft, not the server, and Cancel restores saved
content. Imported choices are allowed for all selected rooms in edit mode.
The upload section uses a native details/summary initialized closed on load and
an explicit closed-details CSS rule to defeat author .stack display rules.

