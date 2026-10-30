## Campaign search and navigation targets

`services/campaign_search.py` streams campaign-filtered rows using parameterized SQL.
The table/column choices come from fixed internal definitions. Python casefold matching
supports Unicode and literal tokens without a database schema/index migration. At most
51 ranked matches are retained for a 50-result response plus a truncation indicator;
campaign rows/text are still scanned for each nonblank request. This is not an indexed
full-text engine; very large note collections may warrant indexing later.

The admin page router checks management authorization before invoking search in an
explicit query-only read snapshot. Search never calls room-note reconciliation, map
activation, geometry mutation or viewer events. Current stored associations are returned
without silently repairing stale data. A generic inspection URL reuses the readiness
inspection handler and template while resolving selected objects by map-scoped identity.

The base template includes the quick-navigation partial only for signed-in admin pages
with a campaign context. The native dialog uses debounced GET requests, aborts superseded
requests, ignores stale responses, inserts results with textContent, and restores focus
on close. Ctrl/Command+K respects other text fields and open dialogs. The full GET-form
page is the no-JavaScript fallback. No persistent search cache/local storage is used.
Selected Markdown is escaped plain text in inspection, not active HTML.

