## Unnamed room auto-edit regression cases

node python/tests/test_room_notes.js now verifies explicit checked-mode selection
of hidden/empty and revealed/notes-only unnamed rooms auto-opens a clean editor
with the imported-note picker. Named rooms, unchecked mode and nonexplicit
selections remain in read mode. The test also checks Cancel, no extra writes or
warnings, existing draft protection and retention of panel collapse state.

