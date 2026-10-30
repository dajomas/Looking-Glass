## Room controls follow-up coverage

Run the existing JS room-note tests for populated-room replacement, notes-only
replacement, default import collapse, draft clear/Cancel and failed/successful
clear saves. python/tests/test_room_notes_controls.py verifies a pre-upgrade schema
migration preserves text/revisions/library, allows empty name/notes, retains
length limits, and preserves cascading deletion. The HTTP import/assignment test
also covers clearing, stale revision rejection and notes-only saves; it requires
the project's installed FastAPI development dependencies.

