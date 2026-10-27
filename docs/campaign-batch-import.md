# Campaign batch map import and wall assignment

The existing single-map form remains. The batch panel accepts multiple images
and separate Foundry VTT / UVTT wall sources (.db, .json, .uvtt, .dd2vtt, .df2vtt
or supported ZIP packs), either kind alone or both. Map names default to filenames.
Sources are saved first, then images imported sequentially via existing routes.
Nothing is matched by filename/order and nothing is displayed automatically.

One progress line identifies the current file. At completion it shows totals
for imported maps/sources, failures and editor warnings, then clears after four
seconds. No growing per-file log is kept. Successful imports remain if another
fails. Inputs clear after completion; retry failed files only. With connection
loss the result may be uncertain: check the campaign before retrying an image.

New maps and existing campaign maps appear in the assignment table. Choose source,
wall set and auto-alignment per map; Apply selected wall assignments acts without
a confirmation. Artwork is retained. Blank the viewer first if boundaries change
during play: prior reveals are recalculated. The same source or set can supply
many maps. Original scene indices remain the import keys despite sorting.

Valid dropdown choices now remain visible, including after successful Apply.
Reapplying selected rows is intentional if you press Apply again. Failed rows
retain their errors and choices for retry. Changing source clears invalid choices
and restores only a previously chosen set belonging to the new source, when that
option exists. Browser-local storage remembers valid choices across reloads.
Explicitly choosing the blank option clears that preference.

Refresh sources reloads saved uploads. Reload the campaign for maps added in
another tab and to update the original Battle maps table. JavaScript is required
for batch mode, not the original single-map form. Existing authorization, CSRF,
per-file size checks and parser validation remain. This release's migration 4
concerns wall-type settings, not batch import storage. Restart and hard-reload
all pages when deploying the combined map-controls update.


## Browser harness follow-up (a24b7d0)

Browser tests share one session-scoped synchronous Playwright/browser lifecycle
from python/tests/browser/conftest.py. Do not re-export browser from test modules
or start overlapping drivers. Function cleanup closes leftover contexts after
failed setup; the batch fixture closes its page and local HTTP server in finally.
Batch readiness uses initialized controls with aria-busy=false, not a Ready
message. Result checks use separate map/source/failure/editor-warning counts
and verify Apply never calls window.confirm. Production behavior is unchanged.

Run python -m pytest --setup-plan -q python/tests/browser to check fixture
resolution (not UI execution), then python -m pytest -ra python/tests/browser.
Measured results and limitations are recorded in Patch/.
