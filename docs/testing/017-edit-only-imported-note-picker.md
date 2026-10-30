## Edit-only imported-note picker

The room-note JS tests now open Edit room before importing and verify the picker
is hidden during reading and visible while editing, including after assignment.
Read-mode action attempts are ignored. Existing confirmation OK/Cancel, undo and
no-replay checks remain. python/tests/test_room_import_edit_layout.py asserts the
picker is structurally inside room-form, not the read view.

