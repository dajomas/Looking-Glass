## Edit highlight and library manager follow-up

Incremental patch targets 5f7dfb3. Deploy Python, template, CSS and new JS files,
restart the server and refresh admin assets. No new dependencies, migrations or
configuration. Notes overlays use a data:image/png base64 source; if an external
reverse-proxy CSP restricts images, permit data: for this admin feature. Back up
SQLite before using library deletion: it is a permanent record deletion with no
application undo. Restore source from 5f7dfb3 for code rollback; restoring deleted
entries requires a DB backup or reimport of their source Markdown.

