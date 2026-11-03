## Upgrading for double-reveal rooms

This release appends database migration 17. Stop the application, back up the complete data
directory (database, SQLite sidecars if present, and map storage), and apply the changed/new
files from the patch ZIP at repository root. Restart normally: `AppContext.build` runs the
append-only migrations. No new runtime Python dependency or configuration key is required.
Hard-refresh the DM editor after upgrading so the new controller and API wrapper are loaded.

The alternate image is stored as a normalized PNG in the existing private maps directory and
uses the existing upload limits. Do not expose that directory via a static web server. Only
admin-authorized artwork endpoints may return original/alternate images; the viewer continues
using fogged composites. Replaced alternate files are intentionally retained for in-flight
readers, so repeated replacements consume storage until a separate safe cleanup procedure.

Rollback requires restoring both the pre-upgrade application files and the backed-up data
from the same point in time. Do not downgrade code alone against schema 17. Installation,
validation limitations and archive inventory are in `Patch/DOUBLE_REVEAL_CHANGES.md`.


