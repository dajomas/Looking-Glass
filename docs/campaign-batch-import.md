# Campaign batch map import and wall assignment

The original single-map form remains available. The additional batch panel
accepts multiple images and separate Foundry VTT / UVTT wall files, or either
kind alone. Wall files may be `.db`, `.json`, `.uvtt`, `.dd2vtt`, `.df2vtt`, or
supported ZIP packs. Map names default to the image filenames.

## Upload progress

There is exactly one live import-status line. It shows the current file and
its position, for example `Importing 2/4: ground-floor.png`. It is replaced for
each file rather than creating a growing log. At completion it shows totals for
imported maps, imported wall sources, failed files and editor warnings. The
completion message disappears after four seconds. Starting a new operation
cancels the previous message timer so it cannot erase new progress.

Files are processed sequentially through the existing endpoints. The batch is
not an all-or-nothing transaction: successful files remain if another fails.
File inputs clear after completion; reselect failed files only. The summary is
brief and does not retain a detailed file-error log. If an upload loses its
connection, check the campaign before retrying, because the server may already
have created the map. Re-uploading a successful image creates another map.

## Assign walls

Existing maps and maps imported in the current tab appear in the assignment
table. Select a saved source and wall set for each target, and choose auto-align
per map. Wall sets are naturally alphabetised, but original scene indices remain
the import keys. The same source or set can be reused across maps. No filename-
or selection-order matching is assumed.

**Apply selected wall assignments** applies immediately, without confirmation.
Only explicitly selected rows are changed; map artwork is retained. Successful
assignments are deselected; failed choices remain for retry and their row errors
remain visible. The total assignment summary disappears after four seconds.
Changing source clears any stale wall-set selection. A failed source inspection
leaves its source selector usable for retry.

Blank the viewer before changing walls during play: saved reveals are replayed
against the new geometry. The batch panel does not activate maps itself. Reload
the campaign to refresh the original Battle maps table or discover maps imported
from another tab. Source refresh updates saved source lists without discarding
valid choices. JavaScript is required for this panel, not the single-map form.

## API and deployment

Uploads and assignments still reuse the existing campaign-scoped map/form,
wall-source and from-source endpoints with session cookies and CSRF checks.
Per-file limits and parser validation are unchanged. There is no new database
migration. Deploy templates and static scripts together and hard-reload tabs.
