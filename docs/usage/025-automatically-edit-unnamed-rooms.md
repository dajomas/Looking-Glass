## Automatically edit unnamed rooms

Enable Select room (fog unchanged) and click an unnamed room. The Room notes
editor opens directly, so you can enter a name or choose Use imported room notes
without clicking Edit room first. An empty or whitespace-only name counts as
unnamed; a room with notes but no name also qualifies, and its notes are preserved.

The editor starts clean: merely opening it does not save anything, mark content
as changed or modify fog. Save room persists edits; Cancel returns to the saved
read view and does not immediately reopen the editor. A later explicit selection
of that unnamed room opens editing again. Existing unsaved-change protection
still applies when switching rooms.

Named rooms, normal fog reveal clicks, background refreshes, and selections when
the checkbox is unchecked do not auto-open editing. A deliberately collapsed
right panel stays collapsed, although its internal state switches to editing;
expand it to see the form. When expanded, the room-name field receives focus.

