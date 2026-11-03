## Campaign search operations

Quick navigation needs no migration, configuration change, dependency or external search
service. Restart after applying Python/templates, and reload admin pages to load the
versioned quick-navigation script. Existing ports, including viewer default 5100, remain
unchanged. No files need deletion.

Search scans the selected campaign's stored names and text using Unicode casefolding.
Results are bounded, but request work grows with campaign content. The dialog debounces
input by 200 ms and cancels superseded browser requests; cancellation need not immediately
stop server-side work. Evaluate response time on large campaigns before considering an
indexed implementation. No writes or viewer rendering are performed by search.

Search queries can contain private DM terms. Although responses use no-store and no
client-side persistent cache, GET query strings can appear in browser history and server/
proxy access logs. Apply normal protection and retention policies to those logs.

