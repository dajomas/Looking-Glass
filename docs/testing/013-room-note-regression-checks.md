## Room-note regression checks

Run `PYTHONPATH=python pytest python/tests/test_room_notes.py` and
`node python/tests/test_room_notes.js` from the repository root. Existing gesture
harnesses now stub the independent room-note component. Full validation should
also run the complete pytest suite and all JavaScript test scripts with installed
runtime/development requirements. See Patch/room-notes.md for the actual patch
validation results and manual acceptance checklist.

### Room editor follow-up

`node python/tests/test_room_notes.js` now covers mutually exclusive view/edit
containers, toolbar actions, multiline formatting, Markdown MIME preference,
clipboard-read denial, length limits, Cancel, save failure/success, dirty selection
protection and collapse persistence. Run from the repository root. See
Patch/room-editor.md for actual validation and browser acceptance checks.

