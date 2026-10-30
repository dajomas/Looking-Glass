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


