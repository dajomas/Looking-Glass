## Upgrading for room notes

Install the updated requirements (Mistune 3.x and Bleach 6.x are new dependencies)
and restart the application; the existing startup migration path appends room_notes.
Back up SQLite first. No new configuration is required. Refresh browser assets;
the editor script URL was versioned for this patch. Container deployments must
rebuild the image. Notes are part of the SQLite backup, not map image files.
Reverting code leaves the additive table intact; do not downgrade by deleting
schema_version entries. Test the patch against your installed dependencies before
production; full HTTP integration tests were not executable in the patch environment.

### Room editor toolbar follow-up

The room read/edit toolbar patch is frontend-only relative to baseline 4d31231:
no migration or dependency change. Deploy its changed files and refresh the page;
admin CSS and room-note JS cache keys are updated. The optional Paste Markdown
button uses the browser Clipboard API, which may require HTTPS/localhost and
permission. Keyboard paste does not depend on that API and remains available.

