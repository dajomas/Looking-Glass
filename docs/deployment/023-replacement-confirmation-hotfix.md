## Replacement confirmation hotfix

Incremental patch for baseline 40c79a8. Frontend-only: no database migration,
configuration or dependency changes. Deploy changed files and refresh the editor.
The template versions both keep_select_values.js and room_notes.js so stale assets
are not reused. Previously stored imported-room choices are ignored; other saved
browser settings need not be cleared. Rollback by restoring source from 40c79a8.

