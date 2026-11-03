## Imported-name availability follow-up

Incremental patch targets 3703c06. Deploy the changed Python service, JavaScript
and template; restart the server and refresh the editor. No migration, dependency
or configuration change. Old saved room names are recognized immediately; there
is no backfill. Template updates room_notes.js cache key. Restoring baseline code
is sufficient for rollback; no library data is deleted by filtering.

