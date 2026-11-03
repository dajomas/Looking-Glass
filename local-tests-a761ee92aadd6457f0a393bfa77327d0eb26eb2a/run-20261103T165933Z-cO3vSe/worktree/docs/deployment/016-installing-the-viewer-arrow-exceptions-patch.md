## Installing the viewer arrow exceptions patch

Stop Looking Glass and back up its SQLite database before updating. Extract the patch
archive into the repository root, preserving relative paths and replacing supplied files.
Restart normally; the existing migration runner applies schema migration 11 automatically.
Hard-refresh admin and viewer pages after updating. No new dependencies or config keys
are needed. New exception flags default off and existing visibility settings are preserved.
For a complete rollback, stop the application and restore both pre-patch code and the
pre-patch database backup. Do not manually modify schema_version.


