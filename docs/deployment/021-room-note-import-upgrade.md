## Room-note import upgrade

The incremental room-note-import patch targets source baseline 77e7284. Back up
SQLite and restart after deployment so the additive imported_room_notes migration
runs. No new dependencies or configuration are required (uses existing Mistune).
The room-note JS cache version is updated. Libraries are backed up with SQLite;
no uploaded raw files are stored. Restoring older code may leave the additive table
intact; use a full pre-upgrade database backup for a complete schema rollback.

