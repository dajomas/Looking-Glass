## Markdown room-note import regression checks

`PYTHONPATH=python pytest python/tests/test_room_note_import.py` covers heading
levels, nested/code exclusions, section preservation, Setext/BOM/CRLF, invalid
input, duplicate titles, idempotent imports, map scope and cascading deletion.
`node python/tests/test_room_notes.js` also covers empty-room eligibility, duplicate
name labels, draft population, no implicit save and Cancel. HTTP coverage is in
python/tests/test_room_note_import_web.py and requires installed dev dependencies.
See Patch/room-note-import.md for which checks actually ran in the patch environment.

